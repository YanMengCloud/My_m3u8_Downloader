from flask import Blueprint, request, jsonify, send_file
from handlers.task_handler import (
    create_download_task,
    start_download_task,
    get_task_status,
    get_all_tasks,
    cancel_task_handler,
    pause_task_handler,
    resume_task,
)
from models.database import get_session, TaskModel
from models.task import download_tasks
import logging
import os
import shutil
import json
from datetime import datetime

task_bp = Blueprint("task", __name__, url_prefix="/api/task")
logger = logging.getLogger(__name__)


@task_bp.route("/create", methods=["POST"])
def create_task():
    """创建下载任务"""
    try:
        data = request.get_json()
        url = data.get("url")
        filename = data.get("filename")
        format_type = data.get("format", "mp4")

        if not url:
            return jsonify({"error": "缺少URL参数"}), 400

        task = create_download_task(url, filename, format_type)
        if task:
            # 启动任务
            start_download_task(task["task_id"])
            return jsonify({"status": "success", "task": task})
        else:
            return jsonify({"error": "创建任务失败"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@task_bp.route("/list", methods=["GET"])
def list_tasks():
    """获取任务列表"""
    try:
        tasks = get_all_tasks()
        logger.info(f"获取任务列表: {tasks}")
        return jsonify({"status": "success", "tasks": tasks})
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>/status", methods=["GET"])
def get_task_info(task_id):
    """获取任务状态"""
    try:
        status = get_task_status(task_id)
        if status:
            return jsonify({"status": "success", "task": status})
        else:
            return jsonify({"error": "任务不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id):
    """取消任务"""
    try:
        if not cancel_task_handler(task_id):
            return jsonify({"status": "error", "error": "任务不存在或无法取消"}), 404

        return jsonify({"status": "success", "message": "任务已取消"})
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


@task_bp.route("/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    """暂停任务"""
    try:
        if not pause_task_handler(task_id):
            return jsonify({"status": "error", "error": "任务不存在或无法暂停"}), 404

        return jsonify({"status": "success", "message": "任务已暂停"})
    except Exception as e:
        logger.error(f"暂停任务失败: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


@task_bp.route("/<task_id>/resume", methods=["POST"])
def resume_task_route(task_id):
    """恢复任务"""
    try:
        if resume_task(task_id):
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "任务不存在或无法恢复"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>", methods=["DELETE"])
def delete_task_route(task_id):
    """删除任务"""
    try:
        session = get_session()
        try:
            # 从数据库中删除任务
            task_model = session.query(TaskModel).filter_by(id=task_id).first()
            if task_model:
                session.delete(task_model)
                session.commit()

            # 从内存中删除任务
            if task_id in download_tasks:
                task = download_tasks[task_id]
                if task.status == "downloading":
                    task.cancel()  # 如果任务在下载，先取消它
                del download_tasks[task_id]

            # 清理临时文件
            task_temp_dir = os.path.join("temp", task_id)
            if os.path.exists(task_temp_dir):
                try:
                    logger.info(f"正在清理临时文件: {task_temp_dir}")
                    shutil.rmtree(task_temp_dir)
                    logger.info(f"临时文件清理完成: {task_temp_dir}")
                except Exception as e:
                    logger.error(f"清理临时文件失败: {str(e)}", exc_info=True)
                    # 即使清理失败也继续返回成功，因为任务本身已经删除
                    pass

            return jsonify({"status": "success"})
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>/download")
def download_task_file(task_id):
    """下载任务文件"""
    try:
        session = get_session()
        try:
            task = session.query(TaskModel).filter_by(id=task_id).first()
            if not task:
                return jsonify({"error": "任务不存在"}), 404

            if task.status != "completed":
                return jsonify({"error": "任务未完成"}), 400

            # 构建文件路径 - 使用temp目录下的输出文件
            file_path = os.path.join(
                "temp", task_id, f"output.{task.format_type or 'mp4'}"
            )
            if not os.path.exists(file_path):
                return jsonify({"error": "文件不存在"}), 404

            return send_file(
                file_path,
                as_attachment=True,
                download_name=task.filename or f"video.{task.format_type or 'mp4'}",
                mimetype=(
                    "video/mp4"
                    if task.format_type == "mp4"
                    else (
                        "video/x-matroska"
                        if task.format_type == "mkv"
                        else "video/MP2T"
                    )
                ),
            )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>/previews")
def get_task_previews(task_id):
    """获取任务的预览图列表"""
    try:
        preview_dir = os.path.join("temp", task_id, "preview")
        if not os.path.exists(preview_dir):
            return jsonify({"error": "预览图目录不存在"}), 404

        # 获取预览目录下的所有图片文件
        preview_files = [
            f
            for f in os.listdir(preview_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        ]

        if not preview_files:
            return jsonify({"error": "没有找到预览图"}), 404

        # 构建预览图信息
        previews = []
        for file in preview_files:
            # 从文件名中提取时间戳（如果文件名格式为 preview_123.jpg，其中123为时间戳）
            try:
                timestamp = float(file.split("_")[1].split(".")[0])
            except (IndexError, ValueError):
                timestamp = 0

            previews.append(
                {"url": f"/temp/{task_id}/preview/{file}", "timestamp": timestamp}
            )

        # 按时间戳排序
        previews.sort(key=lambda x: x["timestamp"])

        return jsonify({"status": "success", "previews": previews})

    except Exception as e:
        logger.error(f"获取预览图列表失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>/download_previews")
def download_previews(task_id):
    """下载预览图文件夹"""
    try:
        preview_dir = os.path.join("temp", task_id, "preview")
        if not os.path.exists(preview_dir):
            return jsonify({"error": "预览图目录不存在"}), 404

        # 创建临时zip文件
        zip_path = os.path.join("temp", task_id, "previews.zip")
        shutil.make_archive(zip_path[:-4], "zip", preview_dir)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"previews_{task_id}.zip",
            mimetype="application/zip",
        )
    except Exception as e:
        logger.error(f"下载预览图失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@task_bp.route("/<task_id>/download_info")
def download_info(task_id):
    """下载视频信息（脱敏）"""
    try:
        info_path = os.path.join("temp", task_id, "info.json")
        if not os.path.exists(info_path):
            return jsonify({"error": "视频信息文件不存在"}), 404

        # 读取并脱敏信息
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        # 脱敏处理
        sanitized_info = {
            "technical_info": info.get("technical_info", {}),
            "format": {
                "duration": info.get("format", {}).get("duration"),
                "size": info.get("format", {}).get("size"),
                "bit_rate": info.get("format", {}).get("bit_rate"),
            },
            "created_at": datetime.now().isoformat(),
        }

        # 创建临时json文件
        output_path = os.path.join("temp", task_id, "video_info.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sanitized_info, f, ensure_ascii=False, indent=2)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"video_info_{task_id}.json",
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"下载视频信息失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
