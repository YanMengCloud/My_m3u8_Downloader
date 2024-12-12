from flask import Flask, render_template, request, send_file, jsonify, Response
from flask_cors import CORS
import m3u8
import requests
import os
from urllib.parse import urljoin, urlparse
import concurrent.futures
import time
import threading
import json
from datetime import datetime, timedelta
import psutil
import schedule
import shutil
import ssl
import certifi
from werkzeug.utils import secure_filename
import glob
from Crypto.Cipher import AES
import base64
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# 添加更详细的 CORS 配置
CORS(app, resources={r"/*": {"origins": "*"}})

# 全局变量存储下载状态
download_tasks = {}


# 添加全局配置
class Config:
    MAX_CONCURRENT_DOWNLOADS = 3  # 最大并发下载数
    SPEED_LIMIT = 0  # 下载速度限制 (bytes/s)，0表示不限制
    AUTO_CLEANUP_DAYS = 7  # 临时文件保留天数
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    VERIFY_SSL = True  # SSL证书验证
    MAX_RETRIES = 3  # 最大重试次数
    CHUNK_SIZE = 8192  # 下载块大小
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"m3u8", "txt"}


config = Config()

# 添加信号量来控制并发下载数
download_semaphore = threading.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)

# 创建上传目录
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)


class M3U8Downloader:
    def __init__(self, url, output_path, key_info=None):
        self.url = url
        self.output_path = output_path
        self.key_info = key_info
        self.session = requests.Session()
        self.session.verify = config.VERIFY_SSL  # 使用配置中的 SSL 验证设置
        self.base_url = self._get_base_url(url)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
        }
        self.playlist = None
        self.key = None
        self.iv = None

    def _get_base_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{os.path.dirname(parsed.path)}/"

    def _get_key(self, key_uri):
        try:
            if key_uri.startswith("http"):
                key_url = key_uri
            else:
                key_url = urljoin(self.base_url, key_uri)

            logger.info(f"Fetching decryption key from: {key_url}")
            response = self.session.get(key_url, headers=self.headers)
            if response.status_code == 200:
                return response.content
            raise Exception(f"Failed to get decryption key: {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting decryption key: {str(e)}")
            raise

    def _decrypt_segment(self, encrypted_data, key, iv):
        try:
            cipher = AES.new(key, AES.MODE_CBC, iv)
            return cipher.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting segment: {str(e)}")
            raise

    def get_total_size(self):
        try:
            # 下载并解析 M3U8 文件
            response = self.session.get(
                self.url,
                headers=self.headers,
                verify=config.VERIFY_SSL,  # 使用配置中的 SSL 验证设置
                timeout=10,  # 添加超时设置
            )
            if response.status_code != 200:
                raise Exception(f"Failed to download M3U8 file: {response.status_code}")

            self.playlist = m3u8.loads(response.text)

            # 获取第一个分片的大小作为预估
            if self.playlist.segments:
                segment = self.playlist.segments[0]
                segment_url = urljoin(self.base_url, segment.uri)
                try:
                    response = self.session.head(
                        segment_url,
                        headers=self.headers,
                        verify=config.VERIFY_SSL,  # 使用配置中的 SSL 验证设置
                        timeout=10,  # 添加超时设置
                    )
                    if response.status_code == 200:
                        segment_size = int(response.headers.get("content-length", 0))
                        return segment_size * len(self.playlist.segments)
                except Exception as e:
                    logger.warning(f"Failed to get segment size: {str(e)}")
                    return 0
            return 0
        except Exception as e:
            logger.error(f"Failed to get total size: {str(e)}")
            return 0

    def download_segment(self, progress_callback, cancel_event, pause_event):
        try:
            if not self.playlist:
                # 如果还没有下载 M3U8 文件，先下载
                response = self.session.get(
                    self.url,
                    headers=self.headers,
                    verify=config.VERIFY_SSL,  # 使用配置中的 SSL 验证设置
                    timeout=10,  # 添加超时设置
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to download M3U8 file: {response.status_code}"
                    )
                self.playlist = m3u8.loads(response.text)

            # 处理加密
            if self.playlist.keys and self.playlist.keys[0]:
                key_info = self.playlist.keys[0]
                if key_info.method == "AES-128":
                    self.key = self._get_key(key_info.uri)
                    self.iv = key_info.iv or b"\0" * 16
                    if isinstance(self.iv, str):
                        self.iv = (
                            bytes.fromhex(self.iv[2:])
                            if self.iv.startswith("0x")
                            else bytes.fromhex(self.iv)
                        )

            # 创建临时目录
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            # 下载所有分片
            for i, segment in enumerate(self.playlist.segments):
                if cancel_event.is_set():
                    return False

                while pause_event.is_set():
                    time.sleep(1)
                    if cancel_event.is_set():
                        return False

                segment_url = urljoin(self.base_url, segment.uri)
                response = self.session.get(segment_url, headers=self.headers)

                if response.status_code != 200:
                    raise Exception(f"Failed to download segment {i}")

                segment_data = response.content
                segment_size = len(segment_data)

                # 解密（如果需要）
                if self.key:
                    segment_data = self._decrypt_segment(
                        segment_data, self.key, self.iv
                    )

                # 写入分片
                with open(f"{self.output_path}_{i}.ts", "wb") as f:
                    f.write(segment_data)

                # 更新进度
                if progress_callback:
                    progress_callback(segment_size)

            # 合并分片
            output_file = f"{self.output_path}_output.ts"
            with open(output_file, "wb") as outfile:
                for i in range(len(self.playlist.segments)):
                    ts_file = f"{self.output_path}_{i}.ts"
                    if os.path.exists(ts_file):
                        with open(ts_file, "rb") as infile:
                            outfile.write(infile.read())
                        os.remove(ts_file)  # 删除临时分片文件

            return True

        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            return False


class DownloadTask:
    def __init__(self, task_id, url, filename, format_type, downloader=None):
        self.task_id = task_id
        self.m3u8_url = url
        self.filename = filename
        self.format_type = format_type
        self.downloader = downloader or M3U8Downloader(
            url=url, output_path=f"temp/{task_id}", key_info=None
        )
        self.status = "pending"
        self.progress = 0
        self.start_time = datetime.now()
        self.download_speed = 0
        self.estimated_time = 0
        self.total_size = 0
        self.downloaded_size = 0
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self._last_update_time = time.time()
        self._last_downloaded_size = 0

    def _update_progress(self, segment_size):
        self.downloaded_size += segment_size
        current_time = time.time()
        time_diff = current_time - self._last_update_time

        if time_diff >= 1:  # 每秒更新一次
            size_diff = self.downloaded_size - self._last_downloaded_size
            self.download_speed = size_diff / time_diff

            if self.total_size > 0:
                self.progress = (self.downloaded_size / self.total_size) * 100
                if self.download_speed > 0:
                    remaining_size = self.total_size - self.downloaded_size
                    self.estimated_time = int(remaining_size / self.download_speed)

            self._last_update_time = current_time
            self._last_downloaded_size = self.downloaded_size

    def start(self):
        try:
            self.status = "downloading"

            # 获取总大小
            total_size = self.downloader.get_total_size()
            if total_size:
                self.total_size = total_size

            # 开始下载
            success = self.downloader.download_segment(
                self._update_progress, self.cancel_event, self.pause_event
            )

            if success:
                self.status = "completed"
                self.progress = 100
            else:
                self.status = "failed"

        except Exception as e:
            logger.error(f"Task {self.task_id} failed: {str(e)}")
            self.status = "failed"


def cleanup_temp_files():
    """定期清理临时文件"""
    try:
        cutoff_date = datetime.now() - timedelta(days=config.AUTO_CLEANUP_DAYS)
        for root, dirs, files in os.walk("temp"):
            for file in files:
                file_path = os.path.join(root, file)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_modified < cutoff_date:
                    os.remove(file_path)
    except Exception as e:
        print(f"清理临时文件失败: {str(e)}")


def get_system_resources():
    """获取系统资源使用情况"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("temp").percent,
    }


@app.route("/")
def index():
    logger.info("访问首页")
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    try:
        urls = request.form.getlist("m3u8_url")
        format_type = request.form.get("format_type", "mp4")
        custom_filename = request.form.get("filename")
        key_url = request.form.get("key_url")
        iv = request.form.get("iv")

        if not urls or not any(url.strip() for url in urls):
            return (
                jsonify({"status": "failed", "error": "请提供至少一个有效的URL"}),
                400,
            )

        tasks = []
        for url in urls:
            if url.strip():
                try:
                    task_id = str(uuid.uuid4())
                    filename = custom_filename or f"video_{task_id[:8]}"
                    output_path = f"temp/{task_id}_output.{format_type}"

                    os.makedirs("temp", exist_ok=True)

                    key_info = {"url": key_url, "iv": iv} if key_url else None
                    downloader = M3U8Downloader(
                        url=url.strip(),
                        output_path=f"temp/{task_id}",
                        key_info=key_info,
                    )

                    task = DownloadTask(
                        task_id=task_id,
                        url=url.strip(),
                        filename=filename,
                        format_type=format_type,
                        downloader=downloader,
                    )

                    download_tasks[task_id] = task
                    threading.Thread(target=task.start).start()
                    tasks.append({"task_id": task_id})

                except Exception as e:
                    return jsonify({"status": "failed", "error": str(e)}), 500

        return jsonify({"status": "success", "tasks": tasks})

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500


@app.route("/tasks")
def get_tasks():
    tasks_info = []
    for task_id, task in download_tasks.items():
        tasks_info.append(
            {
                "task_id": task.task_id,
                "url": task.m3u8_url,
                "status": task.status,
                "progress": task.progress,
                "start_time": task.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "filename": task.filename,
                "speed": (
                    f"{task.download_speed/1024/1024:.2f} MB/s"
                    if task.download_speed > 0
                    else "0 MB/s"
                ),
                "estimated_time": (
                    f"{task.estimated_time//60}分{task.estimated_time%60}秒"
                    if task.estimated_time > 0
                    else "计算中"
                ),
                "total_size": f"{task.total_size/1024/1024:.2f} MB",
                "downloaded_size": f"{task.downloaded_size/1024/1024:.2f} MB",
            }
        )
    return jsonify(tasks_info)


@app.route("/task/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    task = download_tasks.get(task_id)
    if task and task.status == "downloading":
        task.pause_event.set()
        task.status = "paused"
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})


@app.route("/task/<task_id>/resume", methods=["POST"])
def resume_task(task_id):
    task = download_tasks.get(task_id)
    if task and task.status == "paused":
        task.pause_event.clear()
        task.status = "downloading"
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})


@app.route("/task/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id):
    try:
        task = download_tasks.get(task_id)
        if task and task.status in ["downloading", "paused"]:
            # 设置取消标志
            task.cancel_event.set()
            task.pause_event.clear()  # 确保任务不会卡在暂停状态
            task.status = "cancelled"

            # 删除临时文件
            try:
                # 删除所有相关的 .ts 文件
                ts_pattern = f"temp/{task_id}_*.ts"
                for ts_file in glob.glob(ts_pattern):
                    try:
                        os.remove(ts_file)
                        logger.info(f"已删除临时文件: {ts_file}")
                    except Exception as e:
                        logger.error(f"删除临时文件失败: {ts_file}, 错误: {str(e)}")

                # 删除输出文件（如果存在）
                output_file = f"temp/{task_id}_output.{task.format_type}"
                if os.path.exists(output_file):
                    os.remove(output_file)
                    logger.info(f"已删除输出文件: {output_file}")

            except Exception as e:
                logger.error(f"清理临时文件失败: {str(e)}")

            return jsonify({"status": "success"})

    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}")
        return jsonify({"status": "failed", "error": str(e)}), 500

    return jsonify({"status": "failed", "error": "任务不存在或状态错误"}), 400


@app.route("/download_file/<task_id>")
def download_file(task_id):
    task = download_tasks.get(task_id)
    if task and task.status == "completed":
        file_path = f"temp/{task_id}_output.{task.format_type}"
        if os.path.exists(file_path):
            return send_file(
                file_path, as_attachment=True, download_name=f"video.{task.format_type}"
            )
    return "文件不存在", 404


# 添加新的路由
@app.route("/config", methods=["GET", "POST"])
def handle_config():
    if request.method == "POST":
        data = request.get_json()
        config.MAX_CONCURRENT_DOWNLOADS = int(data.get("max_concurrent", 3))
        config.SPEED_LIMIT = int(data.get("speed_limit", 0))
        config.AUTO_CLEANUP_DAYS = int(data.get("cleanup_days", 7))
        config.VERIFY_SSL = bool(data.get("verify_ssl", True))

        # 更新信号量
        global download_semaphore
        download_semaphore = threading.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)

        return jsonify({"status": "success"})

    return jsonify(
        {
            "max_concurrent": config.MAX_CONCURRENT_DOWNLOADS,
            "speed_limit": config.SPEED_LIMIT,
            "cleanup_days": config.AUTO_CLEANUP_DAYS,
            "verify_ssl": config.VERIFY_SSL,
        }
    )


@app.route("/system_resources")
def get_resources():
    return jsonify(get_system_resources())


# 启动定时清理任务
def start_cleanup_scheduler():
    schedule.every().day.at("00:00").do(cleanup_temp_files)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


# 添加新的路由和功能
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "没有文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "没有选择文件"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 读取文件内容获取M3U8地址
        with open(filepath, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        # 创建下载任务
        task_ids = []
        for url in urls:
            if url:
                task_id = str(int(time.time())) + str(len(task_ids))
                task = DownloadTask(
                    task_id=task_id,
                    m3u8_url=url,
                    format_type=request.form.get("format_type", "mp4"),
                    filename=request.form.get("filename", ""),
                )
                download_tasks[task_id] = task
                task.thread = threading.Thread(target=download_video, args=(task,))
                task.thread.start()
                task_ids.append(task_id)

        os.remove(filepath)  # 删除上传的文件
        return jsonify({"task_ids": task_ids})

    return jsonify({"error": "不支持的文件类型"}), 400


# 添加新的路由用于删除任务
@app.route("/task/<task_id>/delete", methods=["POST"])
def delete_task(task_id):
    try:
        if task_id in download_tasks:
            # 如果任务正在下载，先取消
            task = download_tasks[task_id]
            if task.status == "downloading":
                task.cancel_event.set()

            # 清理临时文件
            temp_pattern = f"temp/{task_id}_segment_*.ts"
            for temp_file in glob.glob(temp_pattern):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logger.error(f"删除临时文件失败: {temp_file}, 错误: {str(e)}")

            # 从内存和数据库中删除任务
            del download_tasks[task_id]

            return jsonify({"status": "success"})
        return jsonify({"status": "failed", "error": "任务不存在"}), 404
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500


# 添加新的路由用于处理 m3u 文件
@app.route("/load_m3u", methods=["POST"])
def load_m3u():
    m3u_url = request.form.get("m3u_url")
    try:
        # 下载并解析 m3u 文件
        response = requests.get(m3u_url)
        if response.status_code == 200:
            channels = []
            lines = response.text.splitlines()
            current_channel = {}

            for line in lines:
                if line.startswith("#EXTINF:"):
                    # 解析频道信息
                    info = line.split(",", 1)
                    if len(info) > 1:
                        current_channel["title"] = info[1].strip()
                elif line.startswith("#"):
                    continue
                elif line.strip():
                    # 这是流媒体URL
                    if current_channel:
                        current_channel["url"] = line.strip()
                        channels.append(current_channel.copy())
                        current_channel = {}

            return jsonify({"status": "success", "channels": channels})
        return jsonify({"status": "failed", "error": "无法加载M3U文件"}), 400
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500


# 在主程序启动时调用
if __name__ == "__main__":
    logger.info("启动服务器...")
    start_cleanup_scheduler()
    logger.info(f"Flask 环境: {os.getenv('FLASK_ENV')}")
    logger.info(f"Flask 端口: {os.getenv('FLASK_RUN_PORT', 7101)}")
    logger.info(f"Flask 主机: {os.getenv('FLASK_RUN_HOST', '0.0.0.0')}")
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_RUN_PORT", 7101)), debug=True)
