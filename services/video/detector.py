import ffmpeg
import m3u8
import requests
from typing import Optional, Dict
import re
from pathlib import Path
import logging
import os
import time
import cv2

logger = logging.getLogger(__name__)


class VideoDetector:
    """视频信息检测器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_from_file(self, video_path: str) -> dict:
        """从文件中检测视频信息"""
        try:
            if not os.path.exists(video_path):
                self.logger.error(f"文件不存在: {video_path}")
                return None

            # 确保文件可读
            if not os.access(video_path, os.R_OK):
                self.logger.error(f"文件无法读取: {video_path}")
                return None

            self.logger.info(f"开始检测视频文件: {video_path}")

            try:
                probe = ffmpeg.probe(video_path)
            except ffmpeg._run.Error as e:
                self.logger.error(f"FFprobe 检测失败: {str(e)}")
                return None

            if not probe or "streams" not in probe:
                self.logger.error("FFprobe 返回数据无效")
                return None

            # 获取任务ID（从文件路径中提取）
            task_id = os.path.basename(os.path.dirname(video_path))
            task_dir = os.path.dirname(video_path)

            # 提取视频信息
            video_info = {
                "format": probe.get("format", {}),
                "streams": probe.get("streams", []),
                "technical_info": self._extract_technical_info(probe),
                "metadata": probe.get("format", {}).get("tags", {}),
            }

            # 生成预览图并记录时间戳信息
            preview_info = self._generate_previews(video_path, video_info)
            if preview_info:
                video_info["preview_path"] = preview_info

            # 保存视频信息到JSON文件
            info_path = os.path.join(task_dir, "info.json")
            try:
                import json

                with open(info_path, "w", encoding="utf-8") as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=2)
                self.logger.info(f"视频信息已保存到: {info_path}")
            except Exception as e:
                self.logger.error(f"保存视频信息失败: {str(e)}")

            return video_info

        except Exception as e:
            self.logger.error(f"获取视频信息失败: {str(e)}", exc_info=True)
            return None

    def _extract_technical_info(self, probe):
        """提取技术信息"""
        try:
            # 查找视频流
            video_stream = next(
                (
                    stream
                    for stream in probe["streams"]
                    if stream["codec_type"] == "video"
                ),
                None,
            )

            if not video_stream:
                return {}

            return {
                "codec": video_stream.get("codec_name", "unknown"),
                "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                "duration": float(probe["format"].get("duration", 0)),
                "bitrate": int(probe["format"].get("bit_rate", 0)),
                "size": int(probe["format"].get("size", 0)),
                "fps": self._calculate_fps(video_stream),
            }
        except Exception as e:
            self.logger.error(f"提取技术信息失败: {str(e)}")
            return {}

    def _calculate_fps(self, video_stream):
        """计算FPS"""
        try:
            # 尝试从avg_frame_rate中获取
            if "avg_frame_rate" in video_stream:
                fps_parts = video_stream["avg_frame_rate"].split("/")
                if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                    return round(float(fps_parts[0]) / float(fps_parts[1]), 2)

            # 尝试从r_frame_rate中获取
            if "r_frame_rate" in video_stream:
                fps_parts = video_stream["r_frame_rate"].split("/")
                if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                    return round(float(fps_parts[0]) / float(fps_parts[1]), 2)

            return 0
        except Exception as e:
            self.logger.error(f"计算FPS失败: {str(e)}")
            return 0

    def _generate_previews(self, video_path: str, video_info: dict) -> dict:
        """生成预览图并返回预览信息"""
        try:
            task_id = os.path.basename(os.path.dirname(video_path))
            preview_dir = os.path.join("temp", task_id, "preview")
            os.makedirs(preview_dir, exist_ok=True)

            # 获取视频总时长
            duration = float(video_info.get("technical_info", {}).get("duration", 0))
            if not duration:
                return None

            # 生成10张预览图
            preview_info = {}
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            for i in range(10):
                # 计算时间戳
                timestamp = (duration * i) / 9  # 平均分配时间点
                frame_pos = int((total_frames * i) / 9)

                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if ret:
                    preview_path = f"{task_id}/preview/preview_{i}.jpg"
                    output_path = os.path.join("temp", preview_path)
                    cv2.imwrite(output_path, frame)

                    # 记录预览图信息
                    preview_info[str(i)] = {
                        "path": preview_path,
                        "timestamp": timestamp,
                    }

            cap.release()

            return preview_info

        except Exception as e:
            logger.error(f"生成预览图失败: {str(e)}", exc_info=True)
            return None
