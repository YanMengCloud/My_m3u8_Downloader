import os
import time
import logging
import threading
import json
from datetime import datetime
from typing import Dict, Optional
from services.video.detector import VideoDetector
from services.m3u8_downloader import M3U8Downloader
from models.video.metadata import VideoMetadata
from models.database import TaskModel, get_session

logger = logging.getLogger(__name__)

# 全局变量存储下载任务
download_tasks = {}


class Task:
    def __init__(
        self,
        task_id: str,
        url: str,
        filename: str = None,
        format_type: str = "mp4",
        temp_dir: str = "temp",
    ):
        self.task_id = task_id
        self.url = url
        self.filename = filename or f"video_{task_id}"
        self.format_type = format_type
        self.temp_dir = os.path.join(temp_dir, task_id)
        self.status = "pending"
        self.progress = 0
        self.total_segments = 0
        self.downloaded_segments = 0
        self.video_info = None
        self.video_metadata = None
        self.preview_path = None
        self.cancel_event = threading.Event()
        self.metadata_ready = threading.Event()
        self.downloader = None
        self.video_detector = VideoDetector()

        # 添加时间相关属性
        self.start_time = None
        self.end_time = None
        self.downloaded_size = 0
        self.download_speed = 0
        self.estimated_time = 0

        # 创建临时目录
        os.makedirs(self.temp_dir, exist_ok=True)

        # 保存到全局字典
        download_tasks[task_id] = self

        # 保存到数据库
        self._sync_to_db()

    def _sync_to_db(self):
        """同步任务状态到数据库"""
        try:
            session = get_session()
            try:
                task_model = session.query(TaskModel).filter_by(id=self.task_id).first()

                if task_model:
                    task_model.status = self.status
                    task_model.progress = self.progress
                    task_model.segments = {
                        "downloaded": self.downloaded_segments,
                        "total": self.total_segments,
                    }
                    task_model.video_metadata = self.video_metadata
                    task_model.preview_path = self.preview_path
                else:
                    task_model = TaskModel(
                        id=self.task_id,
                        url=self.url,
                        filename=self.filename,
                        format_type=self.format_type,
                        status=self.status,
                        progress=self.progress,
                        segments={
                            "downloaded": self.downloaded_segments,
                            "total": self.total_segments,
                        },
                        video_metadata=self.video_metadata,
                        preview_path=self.preview_path,
                    )
                    session.add(task_model)

                session.commit()
            except Exception as e:
                logger.error(f"同步到数据库失败: {str(e)}", exc_info=True)
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            logger.error(f"数据库操作失败: {str(e)}", exc_info=True)

    def start(self):
        """开始下载任务"""
        try:
            logger.info(f"开始下载任务: task_id={self.task_id}, url={self.url}")

            # 设置开始时间
            self.start_time = datetime.now()
            self.status = "downloading"
            self._sync_to_db()
            logger.info(f"任务状态已更新: {self.status}")

            # 创建下载器
            logger.info("创建下载器...")
            output_file = os.path.join(self.temp_dir, f"output.{self.format_type}")
            self.downloader = M3U8Downloader(url=self.url, output_path=output_file)
            logger.info(f"下载器创建成功，输出文件: {output_file}")

            # 定义进度回调
            def progress_callback(downloaded, total, segment_size):
                self.downloaded_segments = downloaded
                self.total_segments = total
                self.progress = (downloaded / total * 100) if total > 0 else 0
                self.downloaded_size += segment_size

                # 计算下载速度和预计剩余时间
                elapsed_time = (datetime.now() - self.start_time).total_seconds()
                if elapsed_time > 0:
                    self.download_speed = self.downloaded_size / elapsed_time
                    if self.download_speed > 0:
                        remaining_segments = total - downloaded
                        estimated_remaining_size = (
                            (self.downloaded_size / downloaded) * remaining_segments
                            if downloaded > 0
                            else 0
                        )
                        self.estimated_time = (
                            estimated_remaining_size / self.download_speed
                        )

                self._sync_to_db()
                logger.debug(f"下载进度: {downloaded}/{total} ({self.progress:.1f}%)")

            # 开始下载
            logger.info("开始执行下载...")
            success = self.downloader.download_segment(
                progress_callback=progress_callback,
                cancel_event=self.cancel_event,
                pause_event=self.metadata_ready,  # 使用 metadata_ready 作为暂停事件
            )
            logger.info(f"下载执行结果: {success}")

            if success:
                self.status = "completed"
                self.end_time = datetime.now()
                logger.info(f"下载完成: task_id={self.task_id}")
            else:
                self.status = "failed"
                logger.error(f"下载失败: task_id={self.task_id}")

            self._sync_to_db()

        except Exception as e:
            self.status = "failed"
            error_msg = str(e)
            logger.error(f"下载失败: {error_msg}", exc_info=True)
            self._sync_to_db()
            raise

    def cancel(self):
        """取消任务"""
        if self.downloader:
            self.downloader.cancel()
        # 无论任务状态如何都可以取消
        self.status = "cancelled"
        self.cancel_event.set()
        self.end_time = datetime.now()  # 设置结束时间
        self._sync_to_db()

    def pause(self):
        """暂停任务"""
        if self.downloader:
            self.downloader.pause()
        self.status = "paused"
        self._sync_to_db()

    def resume(self):
        """恢复任务"""
        if self.downloader:
            self.downloader.resume()
        self.status = "downloading"
        self._sync_to_db()

    def get_status(self) -> Dict:
        """获取任务状态"""
        if self.downloader:
            self.progress = self.downloader.progress
            self.total_segments = self.downloader.total_segments
            self.downloaded_segments = self.downloader.downloaded_segments

        # 尝试读取视频信息
        info_path = os.path.join(self.temp_dir, "info.json")
        video_info = None
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    video_info = json.load(f)
            except Exception as e:
                logger.error(f"读取视频信息失败: {str(e)}")

        return {
            "task_id": self.task_id,
            "url": self.url,
            "filename": self.filename,
            "format_type": self.format_type,
            "status": self.status,
            "progress": self.progress,
            "segments": {
                "downloaded": self.downloaded_segments,
                "total": self.total_segments,
            },
            "video_metadata": video_info,  # 添加视频信息
            "preview_path": (
                video_info.get("preview_path") if video_info else None
            ),  # 从视频信息中获取预览图路径
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "downloaded_size": self.downloaded_size,
            "download_speed": self.download_speed,
            "estimated_time": self.estimated_time,
        }
