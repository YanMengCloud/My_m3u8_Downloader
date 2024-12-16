from flask import Blueprint, jsonify, request, make_response
import psutil
import logging
import time
from collections import deque
import uuid
from datetime import datetime

system_bp = Blueprint("system", __name__, url_prefix="/api")

# 创建一个环形缓冲区来存储日志
log_buffer = deque(maxlen=1000)  # 最多保存1000条日志


class BufferHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "level": record.levelname,
            "message": self.format(record),
            "logger": record.name,
            "function": record.funcName,
            "line": record.lineno,
        }
        log_buffer.append(log_entry)


# 配置日志处理器
buffer_handler = BufferHandler()
buffer_handler.setFormatter(logging.Formatter("%(message)s"))
logging.getLogger().addHandler(buffer_handler)


@system_bp.route("/logs")
def get_logs():
    """获取系统日志"""
    try:
        return jsonify(list(log_buffer))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@system_bp.route("/logs/clear", methods=["POST"])
def clear_logs():
    """清空日志缓冲区"""
    try:
        log_buffer.clear()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"清空日志失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@system_bp.route("/logs/export")
def export_logs():
    """导出日志"""
    try:
        # 将日志格式化为文本
        log_text = ""
        for log in log_buffer:
            timestamp = datetime.fromtimestamp(log["timestamp"] / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            log_text += f"{timestamp} [{log['level']}] {log['message']}\n"

        # 创建响应
        response = make_response(log_text)
        response.headers["Content-Type"] = "text/plain"
        response.headers["Content-Disposition"] = (
            f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        return response
    except Exception as e:
        logger.error(f"导出日志失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@system_bp.route("/system_resources")
def get_system_resources():
    """获取系统资源使用情况"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return jsonify(
            {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_usage": disk.percent,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@system_bp.route("/config", methods=["GET", "POST"])
def handle_config():
    """处理配置"""
    from config import Config

    if request.method == "GET":
        return jsonify(
            {
                "max_concurrent": Config.MAX_CONCURRENT_DOWNLOADS,
                "speed_limit": Config.SPEED_LIMIT,
                "cleanup_days": Config.AUTO_CLEANUP_DAYS,
                "verify_ssl": Config.VERIFY_SSL,
            }
        )

    try:
        data = request.json
        if "max_concurrent" in data:
            Config.MAX_CONCURRENT_DOWNLOADS = int(data["max_concurrent"])
        if "speed_limit" in data:
            Config.SPEED_LIMIT = int(data["speed_limit"])
        if "cleanup_days" in data:
            Config.AUTO_CLEANUP_DAYS = int(data["cleanup_days"])
        if "verify_ssl" in data:
            Config.VERIFY_SSL = bool(data["verify_ssl"])

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
