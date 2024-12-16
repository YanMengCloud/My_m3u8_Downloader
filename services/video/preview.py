import cv2
import numpy as np
from typing import Optional
import ffmpeg
import os
import tempfile
import logging
from services.video.detector import VideoDetector

logger = logging.getLogger(__name__)


class VideoPreviewService:
    def __init__(self):
        self.detector = VideoDetector()
        self.preview_dir = "static/previews"
        os.makedirs(self.preview_dir, exist_ok=True)

    def generate_preview(self, video_path):
        """生成视频预览"""
        try:
            logger.info(f"开始生成视频预览: {video_path}")
            video_info = self.detector.detect_from_file(video_path)

            if not video_info:
                logger.error("无法获取视频信息")
                return None

            preview_path = video_info.get("preview_path")
            if preview_path and os.path.exists(preview_path):
                logger.info(f"预览图生成成功: {preview_path}")
                return preview_path
            else:
                logger.error("预览图生成失败")
                return None

        except Exception as e:
            logger.error(f"生成预览失败: {str(e)}", exc_info=True)
            return None

    def get_video_stream(self, video_url: str) -> Optional[dict]:
        """
        获取视频流信息
        :param video_url: 视频URL
        :return: 视频流信息
        """
        try:
            probe = ffmpeg.probe(video_url)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
            return video_info
        except Exception as e:
            logger.error(f"获取视频流失败: {str(e)}")
            return None
