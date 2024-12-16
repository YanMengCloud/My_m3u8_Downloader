import ffmpeg
import m3u8
import requests
from typing import Optional, Dict
import re
from pathlib import Path
import logging
import os
import time

logger = logging.getLogger(__name__)


class VideoDetector:
    """视频信息检测器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_from_file(self, file_path):
        """从文件中检测视频信息"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return None

            # 确保文件可读
            if not os.access(file_path, os.R_OK):
                self.logger.error(f"文件无法读取: {file_path}")
                return None

            self.logger.info(f"开始检测视频文件: {file_path}")

            try:
                probe = ffmpeg.probe(file_path)
            except ffmpeg._run.Error as e:
                self.logger.error(f"FFprobe 检测失败: {str(e)}")
                return None

            if not probe or "streams" not in probe:
                self.logger.error("FFprobe 返回数据无效")
                return None

            # 获取任务ID（从文件路径中提取）
            task_id = os.path.basename(os.path.dirname(file_path))
            task_dir = os.path.dirname(file_path)

            # 提取视频信息
            video_info = {
                "format": probe.get("format", {}),
                "streams": probe.get("streams", []),
                "technical_info": self._extract_technical_info(probe),
                "metadata": probe.get("format", {}).get("tags", {}),
            }

            # 生成预览图
            preview_path = self._generate_preview(file_path, task_id)
            if preview_path:
                video_info["preview_path"] = preview_path

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
            self.logger.error(f"获取���频信息失败: {str(e)}", exc_info=True)
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

    def _generate_preview(self, file_path, task_id):
        """生成预览图"""
        try:
            # 使用任务目录下的preview目录
            preview_dir = os.path.join(os.path.dirname(file_path), "preview")
            os.makedirs(preview_dir, exist_ok=True)

            # 获取视频时长
            probe = ffmpeg.probe(file_path)
            duration = float(probe["format"]["duration"])

            # 生成10张预览图，分别在视频的不同时间点
            preview_paths = []
            for i in range(10):
                # 计算时间戳（在整个视频长度上均匀分布）
                timestamp = duration * i / 9  # 使用9而不是10确保最后一帧在视频结尾
                preview_path = os.path.join(preview_dir, f"preview_{timestamp:.1f}.jpg")

                # 使用ffmpeg生成预览图
                stream = ffmpeg.input(file_path, ss=timestamp)
                stream = ffmpeg.filter(stream, "scale", 480, -1)
                stream = ffmpeg.output(stream, preview_path, vframes=1)

                try:
                    ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
                    if os.path.exists(preview_path):
                        preview_paths.append(preview_path)
                        self.logger.info(f"生成预览图成功: {preview_path}")
                except ffmpeg.Error as e:
                    self.logger.error(f"生成预览图失败: {str(e)}")
                    continue

            if preview_paths:
                # 创建软链接到static目录
                static_preview_dir = os.path.join("static/previews", task_id)
                os.makedirs(static_preview_dir, exist_ok=True)

                # 为每个预览图创建软链接
                for preview_path in preview_paths:
                    preview_name = os.path.basename(preview_path)
                    static_preview_path = os.path.join(static_preview_dir, preview_name)

                    # 如果已存在软链接，先删除
                    if os.path.exists(static_preview_path):
                        os.remove(static_preview_path)

                    # 创建新的软链接
                    os.symlink(os.path.abspath(preview_path), static_preview_path)

                # 返回第一张预览图的Web访问路径
                return (
                    f"/static/previews/{task_id}/{os.path.basename(preview_paths[0])}"
                )
            else:
                self.logger.error("没有成功生成任何预览图")
                return None

        except Exception as e:
            self.logger.error(f"生成预览失败: {str(e)}")
            return None
