import m3u8
import requests
import os
import logging
import subprocess
from Crypto.Cipher import AES
from urllib.parse import urljoin
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class M3U8Downloader:
    def __init__(self, url, output_path, key_info=None):
        logger.info(f"初始化M3U8下载器: url={url}")
        self.m3u8_url = url
        self.output_path = output_path
        self.key_info = key_info
        self.progress = 0
        self.total_segments = 0
        self.downloaded_segments = 0
        self.total_size = 0
        self.segment_sizes = []
        self.failed_segments = []

        # 配置请求会话
        self.session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=5,  # 最大重试次数
            backoff_factor=0.5,  # 重试间隔
            status_forcelist=[500, 502, 503, 504, 429],  # 需要重试的HTTP状态码
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # 设置请求头
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Connection": "keep-alive",
                "Accept": "*/*",
            }
        )

        # 禁用SSL验证
        self.session.verify = False

    def _download_segment_with_retry(
        self, segment_url, output_file, key=None, iv=None, max_retries=3
    ):
        """下载单个分片，带重试机制"""
        retries = 0
        while retries < max_retries:
            try:
                response = self.session.get(segment_url, stream=True, timeout=(5, 30))
                if response.status_code != 200:
                    raise Exception(f"下载失败，状态码: {response.status_code}")

                # 解密并保存分片
                with open(output_file, "wb") as f:
                    if key:
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        content = response.content
                        decrypted_content = cipher.decrypt(content)
                        f.write(self._unpad(decrypted_content))
                        return len(content)
                    else:
                        chunk_size = 8192
                        downloaded_size = 0
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                        return downloaded_size

            except Exception as e:
                retries += 1
                logger.warning(
                    f"下载分片失败 (尝试 {retries}/{max_retries}): {segment_url}, error={str(e)}"
                )
                if retries == max_retries:
                    raise
                time.sleep(1)  # 重试前等待1秒

    def download_segment(
        self, progress_callback=None, cancel_event=None, pause_event=None
    ):
        """下载M3U8视频分片"""
        try:
            logger.info(f"开始下载M3U8: {self.m3u8_url}")
            # 加载M3U8文件
            playlist = m3u8.load(self.m3u8_url, verify_ssl=False)
            if not playlist.segments:
                logger.error("M3U8文件没有分片")
                return False

            self.total_segments = len(playlist.segments)
            logger.info(f"找到 {self.total_segments} 个分片")

            # 获取密钥（如果有）
            key = None
            iv = None
            if playlist.keys and len(playlist.keys) > 0:
                key_info = playlist.keys[0]
                if key_info:
                    logger.info(
                        f"发现加密密钥: method={key_info.method}, uri={key_info.uri}"
                    )
                    key_url = self._get_absolute_url(key_info.uri)
                    key = self.session.get(key_url).content
                    # 处理IV
                    if key_info.iv:
                        if isinstance(key_info.iv, str):
                            iv_str = key_info.iv.lower().replace("0x", "")
                            iv_str = iv_str.zfill(32)
                            iv = bytes.fromhex(iv_str)
                        else:
                            iv = key_info.iv
                    else:
                        iv = bytes([0] * 16)
                    logger.info(f"使用IV: {iv.hex()}")

            # 下载每个分片
            downloaded_segments = []
            self.downloaded_segments = 0
            download_start_time = time.time()
            last_progress_update = time.time()
            bytes_since_last_update = 0

            for index, segment in enumerate(playlist.segments):
                if cancel_event and cancel_event.is_set():
                    logger.info("下载已取消")
                    return False

                while pause_event and pause_event.is_set():
                    if cancel_event and cancel_event.is_set():
                        logger.info("暂停时取消下载")
                        return False
                    time.sleep(0.1)

                segment_url = self._get_absolute_url(segment.uri)
                output_file = os.path.join(
                    os.path.dirname(self.output_path), f"segment_{index:03d}.ts"
                )
                downloaded_segments.append(output_file)

                try:
                    logger.info(
                        f"下载分片 {index+1}/{self.total_segments}: {segment_url}"
                    )
                    segment_size = self._download_segment_with_retry(
                        segment_url, output_file, key, iv
                    )
                    bytes_since_last_update += segment_size

                    self.downloaded_segments += 1
                    self.progress = (
                        self.downloaded_segments / self.total_segments
                    ) * 100

                    # 更新进度
                    if progress_callback:
                        progress_callback(
                            self.downloaded_segments, self.total_segments, segment_size
                        )

                    # 更新下载速度
                    current_time = time.time()
                    if current_time - last_progress_update >= 1.0:
                        download_speed = bytes_since_last_update / (
                            current_time - last_progress_update
                        )
                        bytes_since_last_update = 0
                        last_progress_update = current_time

                    logger.info(
                        f"分片下载进度: {self.downloaded_segments}/{self.total_segments} ({self.progress:.1f}%)"
                    )

                except Exception as e:
                    logger.error(f"下载分片失败: {segment_url}, error={str(e)}")
                    self.failed_segments.append(
                        {"index": index, "url": segment_url, "error": str(e)}
                    )
                    continue

            # 检查是否有失败的分片
            if self.failed_segments:
                logger.error(f"有 {len(self.failed_segments)} 个分片下载失败")
                for failed in self.failed_segments:
                    logger.error(
                        f"失败的分片: index={failed['index']}, url={failed['url']}, error={failed['error']}"
                    )
                return False

            # 合并分片
            if downloaded_segments:
                return self._merge_segments(
                    downloaded_segments, os.path.dirname(self.output_path)
                )

            return False

        except Exception as e:
            logger.error(f"下载失败: {str(e)}", exc_info=True)
            return False

    def _merge_segments(self, downloaded_segments, task_dir):
        """合并下载的分片"""
        try:
            logger.info("开始合并分片")
            output_format = os.path.splitext(self.output_path)[1][1:] or "mp4"
            final_output = os.path.join(task_dir, f"output.{output_format}")
            logger.info(f"输出文件路径: {final_output}")

            if output_format in ["mp4", "mkv"]:
                # 使用ffmpeg合并并转换格式
                segments_file = os.path.join(task_dir, "segments.txt")

                # 使用相对路径写入segments.txt
                with open(segments_file, "w", encoding="utf-8") as f:
                    for segment in downloaded_segments:
                        # 确保使用相对于task_dir的路径
                        segment_name = os.path.basename(segment)
                        f.write(f"file '{segment_name}'\n")

                # 检查segments.txt是否创建成功
                if not os.path.exists(segments_file):
                    raise Exception(f"segments.txt 文件创建失败: {segments_file}")

                logger.info(f"创建segments.txt文件: {segments_file}")
                logger.info(f"segments.txt内容:")
                with open(segments_file, "r", encoding="utf-8") as f:
                    logger.info(f.read())

                # 检查所有分片文件是否存在
                for segment in downloaded_segments:
                    if not os.path.exists(segment):
                        raise Exception(f"分片文件不存在: {segment}")

                # 确保输出目录存在
                os.makedirs(os.path.dirname(final_output), exist_ok=True)

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    "segments.txt",
                    "-c",
                    "copy",
                    "output.{0}".format(output_format),  # 使用相对路径
                ]

                try:
                    logger.info(f"执行FFmpeg命令: {' '.join(cmd)}")
                    logger.info(f"工作目录: {task_dir}")

                    # 检查工作目录是否存在
                    if not os.path.exists(task_dir):
                        raise Exception(f"工作目录不存在: {task_dir}")

                    # 检查工作目录权限
                    if not os.access(task_dir, os.W_OK):
                        raise Exception(f"工作目录没有写入权限: {task_dir}")

                    result = subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=task_dir,
                    )

                    output_file = os.path.join(task_dir, f"output.{output_format}")
                    if not os.path.exists(output_file):
                        raise Exception(
                            f"FFmpeg执行成功但输出文件不存在: {output_file}"
                        )

                    logger.info("FFmpeg合并成功")
                    logger.info(f"输出文件大小: {os.path.getsize(output_file)} bytes")

                    # 获取视频信息
                    self._process_video_info(output_file)

                    return True

                except subprocess.CalledProcessError as e:
                    logger.error(f"合并视频失败: {e.stdout}\n{e.stderr}")
                    return False
                finally:
                    # 清理临时文件
                    try:
                        self._cleanup_temp_files(
                            task_dir, segments_file, downloaded_segments
                        )
                    except Exception as e:
                        logger.error(f"清理临时文件失败: {str(e)}")
            else:
                # 直接合并TS文件
                return self._merge_ts_files(downloaded_segments, final_output)

        except Exception as e:
            logger.error(f"合并分片失败: {str(e)}", exc_info=True)
            return False

    def _process_video_info(self, video_path):
        """处理视频信息"""
        try:
            from services.video.detector import VideoDetector

            detector = VideoDetector()
            self.video_info = detector.detect_from_file(video_path)
            if self.video_info:
                logger.info(f"成功获取视频信息: {self.video_info}")
                # 设置任务状态为已完成
                self.status = "completed"
                logger.info("下载任务完成")
            else:
                logger.warning("无法获取视频信息")
                # 即使视频信息获取失败，也将任务标记为完成
                self.status = "completed"
                logger.info("下载任务完成（无视频信息）")
        except Exception as e:
            logger.error(f"处理视频信息失败: {str(e)}", exc_info=True)
            # 即使视频信息获取失败，也将任务标记为完成
            self.status = "completed"
            logger.info("下载任务完成（处理视频信息失败）")

    def _merge_ts_files(self, downloaded_segments, final_output):
        """直接合并TS文件"""
        try:
            logger.info("直接合并TS文件")
            with open(final_output, "wb") as outfile:
                for segment in downloaded_segments:
                    if os.path.exists(segment):
                        with open(segment, "rb") as infile:
                            outfile.write(infile.read())
                        # 立即删除已合并的分片
                        try:
                            os.remove(segment)
                            logger.info(f"删除分片文件: {segment}")
                        except Exception as e:
                            logger.error(f"删除分片文件失败: {segment}, error={str(e)}")
            return True
        except Exception as e:
            logger.error(f"合并TS文件失败: {str(e)}")
            return False

    def _cleanup_temp_files(self, task_dir, segments_file, downloaded_segments):
        """清理临时文件"""
        try:
            # 删除segments.txt
            if os.path.exists(segments_file):
                os.remove(segments_file)
                logger.info(f"删除segments.txt: {segments_file}")

            # ���除分片文件
            for segment in downloaded_segments:
                try:
                    if os.path.exists(segment):
                        os.remove(segment)
                except Exception as e:
                    logger.error(f"删除分片文件失败: {segment}, error={str(e)}")
            logger.info("删除分片文件完成")

        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            raise

    def _get_absolute_url(self, url):
        """获取绝对URL"""
        if url.startswith("http"):
            return url
        return urljoin(self.m3u8_url, url)

    def _unpad(self, data):
        """去除PKCS7填充"""
        padding_len = data[-1]
        if padding_len < 1 or padding_len > 16:
            return data
        for i in range(padding_len):
            if data[-i - 1] != padding_len:
                return data
        return data[:-padding_len]

    def _prepare_task_directory(self):
        """准备任务目录"""
        try:
            task_dir = os.path.join("temp", self.task_id)
            # 确保目录存在
            os.makedirs(task_dir, exist_ok=True)

            # 检查目录权限
            if not os.access(task_dir, os.W_OK):
                logger.error(f"任务目录没有写入权限: {task_dir}")
                raise Exception(f"任务目录没有写入权限: {task_dir}")

            logger.info(f"创建任务目录: {task_dir}")
            return task_dir
        except Exception as e:
            logger.error(f"创建任务目录失败: {str(e)}", exc_info=True)
            raise

    def download(self):
        """开始下载"""
        try:
            # 准备任务目录
            task_dir = self._prepare_task_directory()
            logger.info(f"开始下载任务 {self.task_id}")

            if not self.segments:
                self.parse_m3u8()

            downloaded_segments = []
            self.failed_segments = []

            for index, segment_url in enumerate(self.segments):
                if self.status == "cancelled":
                    logger.info("任务已取消")
                    return False

                if self.status == "paused":
                    logger.info("任务已暂停")
                    return False

                segment_path = os.path.join(task_dir, f"segment_{index}.ts")
                try:
                    success = self._download_segment(segment_url, segment_path, index)
                    if success:
                        downloaded_segments.append(segment_path)
                        self.downloaded_segments = len(downloaded_segments)
                        self.progress = (
                            len(downloaded_segments) / len(self.segments)
                        ) * 100
                    else:
                        self.failed_segments.append(
                            {"index": index, "url": segment_url}
                        )
                except Exception as e:
                    logger.error(f"下载分片失败: {segment_url}, error={str(e)}")
                    self.failed_segments.append(
                        {"index": index, "url": segment_url, "error": str(e)}
                    )

            if not downloaded_segments:
                logger.error("没有成功下载的分片")
                return False

            if len(downloaded_segments) != len(self.segments):
                logger.warning(f"部分分片下载失败: {len(self.failed_segments)} 个失败")

            # 合并分片
            success = self._merge_segments(downloaded_segments, task_dir)
            if not success:
                logger.error("合并分片失败")
                return False

            logger.info("下载完成")
            return True

        except Exception as e:
            logger.error(f"下载过程发生错误: {str(e)}", exc_info=True)
            return False

    def _download_segment(self, segment_url, segment_path, index):
        """下载单个分片"""
        try:
            logger.info(f"下载分片 {index+1}/{self.total_segments}: {segment_url}")
            segment_size = self._download_segment_with_retry(
                segment_url, segment_path, self.key, self.iv
            )
            self.downloaded_segments += 1
            self.total_size += segment_size
            self.segment_sizes.append(segment_size)
            return True
        except Exception as e:
            logger.error(f"下载分片失败: {segment_url}, error={str(e)}")
            self.failed_segments.append(
                {"index": index, "url": segment_url, "error": str(e)}
            )
            return False

    def parse_m3u8(self):
        """解析M3U8文件"""
        try:
            logger.info("开始解析M3U8文件")
            playlist = m3u8.load(self.m3u8_url, verify_ssl=False)
            self.segments = [
                self._get_absolute_url(segment.uri) for segment in playlist.segments
            ]
            logger.info(f"找到 {len(self.segments)} 个分片")
        except Exception as e:
            logger.error(f"解析M3U8文件失败: {str(e)}")
            raise

    def get_total_size(self):
        """获取总大小"""
        try:
            logger.info("开始获取总大小")
            response = self.session.head(self.m3u8_url)
            if response.status_code != 200:
                raise Exception(f"获取总大小失败，状态码: {response.status_code}")
            self.total_size = int(response.headers.get("Content-Length", 0))
            logger.info(f"总大小: {self.total_size} 字节")
        except Exception as e:
            logger.error(f"获取总大小失败: {str(e)}")
            raise
