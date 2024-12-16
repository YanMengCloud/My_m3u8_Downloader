from flask import Blueprint, request, jsonify
from services.video.preview import VideoPreviewService
from services.video.detector import VideoDetector
from models.video.metadata import VideoMetadata
from models.task import download_tasks
import os

video_bp = Blueprint("video", __name__, url_prefix="/api/video")
video_preview_service = VideoPreviewService()
video_info_detector = VideoDetector()


@video_bp.route("/preview", methods=["POST"])
def generate_video_preview():
    try:
        video_url = request.json.get("video_url")
        if not video_url:
            return jsonify({"error": "缺少视频URL"}), 400

        preview_path = video_preview_service.generate_preview(video_url)
        if preview_path:
            return jsonify(
                {
                    "status": "success",
                    "preview_url": f"/static/previews/{os.path.basename(preview_path)}",
                }
            )
        return jsonify({"error": "生成预览失败"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@video_bp.route("/info", methods=["POST"])
def detect_video_info():
    try:
        video_url = request.json.get("video_url")
        if not video_url:
            return jsonify({"error": "缺少视频URL"}), 400

        video_info = video_info_detector.detect_from_url(video_url)
        return jsonify({"status": "success", "video_info": video_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@video_bp.route("/metadata/<task_id>", methods=["GET", "PUT"])
def handle_video_metadata(task_id):
    task = download_tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    if request.method == "GET":
        try:
            metadata = task.metadata if hasattr(task, "metadata") else None
            if metadata:
                return jsonify(metadata.to_dict())
            return jsonify({"error": "元数据不存在"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == "PUT":
        try:
            metadata_dict = request.json
            if not hasattr(task, "metadata"):
                task.metadata = VideoMetadata.from_dict(metadata_dict)
            else:
                task.metadata.update(**metadata_dict)
            return jsonify(task.metadata.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
