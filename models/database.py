from datetime import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

# 从环境变量获取数据库配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ymbox")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# 创建数据库引擎
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# 创建所有表
Base.metadata.create_all(engine)

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
