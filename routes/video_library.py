from flask import Blueprint, jsonify, request, send_file
from models.database import VideoLibrary, TaskModel, Session
import os
import shutil
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

video_library_bp = Blueprint("video_library", __name__)


@video_library_bp.route("/api/video-library/list", methods=["GET"])
def list_videos():
    session = Session()
    try:
        videos = session.query(VideoLibrary).all()
        return jsonify(
            {"status": "success", "videos": [video.to_dict() for video in videos]}
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        session.close()


@video_library_bp.route("/api/video-library/add/<task_id>", methods=["POST"])
def add_to_library(task_id):
    session = Session()
    try:
        # 获取任务信息
        task = session.query(TaskModel).filter_by(id=task_id).first()
        if not task:
            return jsonify({"status": "error", "error": "任务不存在"}), 404

        # 检查是否已经在视频库中
        existing = session.query(VideoLibrary).filter_by(task_id=task_id).first()
        if existing:
            return jsonify({"status": "error", "error": "该视频已在视频库中"}), 400

        # 创建video_library目录（如果不存在）
        library_base_path = os.path.join("static", "video_library")
        os.makedirs(library_base_path, exist_ok=True)

        # 创建该视频的目录
        video_dir = os.path.join(library_base_path, task_id)
        if os.path.exists(video_dir):
            shutil.rmtree(video_dir)  # 如果目录存在，先删除
        os.makedirs(video_dir)

        # 复制所有文件
        task_dir = os.path.join("temp", task_id)
        logger.info(f"源目录: {task_dir}")
        logger.info(f"目标目录: {video_dir}")

        if os.path.exists(task_dir):
            # 复制所有文件和目录
            for item in os.listdir(task_dir):
                source = os.path.join(task_dir, item)
                destination = os.path.join(video_dir, item)

                if os.path.isdir(source):
                    # 如果是目录（如preview目录），使用copytree
                    shutil.copytree(source, destination)
                    logger.info(f"复制目录: {source} -> {destination}")
                else:
                    # 如果是文件，使用copy2
                    shutil.copy2(source, destination)
                    logger.info(f"复制文件: {source} -> {destination}")

        # 读取info.json获取视频信息
        info_file = os.path.join(video_dir, "info.json")
        video_info = None
        if os.path.exists(info_file):
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    video_info = json.load(f)
            except Exception as e:
                logger.error(f"读取info.json失败: {str(e)}")

        # 创建视频库记录
        video = VideoLibrary(
            task_id=task_id,
            title=task.filename,  # 初始标题使用文件名
            original_filename=task.filename,
            file_path=os.path.join(
                "video_library", task_id, "output.mp4"
            ),  # 使用相对路径
            preview_path=os.path.join(
                "video_library", task_id, "preview"
            ),  # 预览图目录路径
            video_info=video_info,  # 保存完整的视频信息
        )

        session.add(video)
        session.commit()

        return jsonify({"status": "success", "video": video.to_dict()})

    except Exception as e:
        logger.error(f"添加到视频库失败: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        session.close()


@video_library_bp.route("/api/video-library/<int:video_id>", methods=["PUT"])
def update_video(video_id):
    session = Session()
    try:
        video = session.query(VideoLibrary).filter_by(id=video_id).first()
        if not video:
            return jsonify({"status": "error", "error": "视频不存在"}), 404

        data = request.get_json()
        if "title" in data:
            video.title = data["title"]

        video.updated_at = datetime.utcnow()
        session.commit()

        return jsonify({"status": "success", "video": video.to_dict()})

    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        session.close()


@video_library_bp.route("/api/video-library/<int:video_id>", methods=["DELETE"])
def delete_video(video_id):
    session = Session()
    try:
        video = session.query(VideoLibrary).filter_by(id=video_id).first()
        if not video:
            return jsonify({"status": "error", "error": "视频不存在"}), 404

        # 删除视频文件夹
        video_dir = os.path.join("static", "video_library", video.task_id)
        if os.path.exists(video_dir):
            shutil.rmtree(video_dir)

        # 删除数据库记录
        session.delete(video)
        session.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        session.close()


@video_library_bp.route("/api/video-library/<int:video_id>/download_previews")
def download_library_previews(video_id):
    """下载视频库中的预览图"""
    try:
        session = Session()
        try:
            video = session.query(VideoLibrary).filter_by(id=video_id).first()
            if not video:
                return jsonify({"error": "视频不存在"}), 404

            preview_dir = os.path.join("static", video.preview_path)
            if not os.path.exists(preview_dir):
                return jsonify({"error": "预览图目录不存在"}), 404

            # 创建临时zip文件
            temp_dir = os.path.join("temp", "downloads")
            os.makedirs(temp_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, f"previews_{video.task_id}.zip")

            # 压缩预览图文件夹
            shutil.make_archive(zip_path[:-4], "zip", preview_dir)

            return send_file(
                zip_path,
                as_attachment=True,
                download_name=f"previews_{video.task_id}.zip",
                mimetype="application/zip",
            )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"下载预览图失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@video_library_bp.route("/api/video-library/<int:video_id>/download_info")
def download_library_info(video_id):
    """下载视频库中的视频信息"""
    try:
        session = Session()
        try:
            video = session.query(VideoLibrary).filter_by(id=video_id).first()
            if not video:
                return jsonify({"error": "视频不存在"}), 404

            # 创建临时目录
            temp_dir = os.path.join("temp", "downloads")
            os.makedirs(temp_dir, exist_ok=True)
            info_path = os.path.join(temp_dir, f"video_info_{video.task_id}.json")

            # 准备视频信息
            video_info = {
                "title": video.title,
                "original_filename": video.original_filename,
                "technical_info": video.video_info.get("technical_info", {}),
                "preview_path": video.video_info.get("preview_path", {}),
                "created_at": (
                    video.created_at.isoformat() if video.created_at else None
                ),
                "updated_at": (
                    video.updated_at.isoformat() if video.updated_at else None
                ),
            }

            # 写入JSON文件
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(video_info, f, ensure_ascii=False, indent=2)

            return send_file(
                info_path,
                as_attachment=True,
                download_name=f"video_info_{video.task_id}.json",
                mimetype="application/json",
            )
        finally:
            session.close()
    except Exception as e:
        logger.error(f"下载视频信息失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
