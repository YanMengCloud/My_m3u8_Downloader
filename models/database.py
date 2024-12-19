from datetime import datetime
import json
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

# 从环境变量获取数据库配置
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ymbox")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# 创建数据库引擎
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "client_encoding": "utf8",
        "application_name": "ymbox_m3u8_downloader",
    },
)

# 创建会话工厂
Session = sessionmaker(bind=engine)


def get_session():
    return Session()


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)  # UUID
    url = Column(String(1024), nullable=False)
    filename = Column(String(255))
    format_type = Column(String(10))
    status = Column(String(20))  # pending, downloading, completed, failed, cancelled
    progress = Column(Float, default=0)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    downloaded_size = Column(Integer, default=0)
    segments = Column(JSON)  # {"downloaded": 0, "total": 0}
    video_metadata = Column(JSON)  # 视频元数据
    preview_path = Column(String(255))  # 预览图路径
    error_message = Column(String(1024))  # 错误信息

    def to_dict(self):
        segments_info = self.segments or {"downloaded": 0, "total": 0}

        # 尝试读取视频信息
        info_path = os.path.join("temp", self.id, "info.json")
        video_info = None
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    video_info = json.load(f)
            except Exception as e:
                logger.error(f"读取视频信息失败: {str(e)}")

        return {
            "task_id": self.id,
            "url": self.url,
            "filename": self.filename,
            "format_type": self.format_type,
            "status": self.status,
            "progress": self.progress,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "downloaded_size": self.downloaded_size,
            "segments": segments_info,
            "total_segments": segments_info.get("total", 0),
            "video_metadata": video_info,  # 添加视频信息
            "preview_path": (
                video_info.get("preview_path") if video_info else None
            ),  # 从视频信息中获取预览图路径
            "error_message": self.error_message,
        }


class VideoLibrary(Base):
    __tablename__ = "video_library"

    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True)  # 关联的任务ID
    title = Column(String)  # 视频标题
    original_filename = Column(String)  # 原始文件名
    file_path = Column(String)  # 视频文件路径
    preview_path = Column(String)  # 预览图文件夹路径
    video_info = Column(JSON)  # 视频信息（分辨率、时长等）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    thumbnail_index = Column(Integer, default=0)  # 添加封面图索引字段

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "preview_path": self.preview_path,
            "video_info": self.video_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "thumbnail_index": self.thumbnail_index,
        }
