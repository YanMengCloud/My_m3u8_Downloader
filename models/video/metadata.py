from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class VideoMetadata:
    title: str
    description: Optional[str] = None
    episode: Optional[int] = None
    season: Optional[int] = None
    year: Optional[int] = None
    resolution: Optional[str] = None
    duration: Optional[float] = None
    codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    fps: Optional[float] = None
    tags: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def update(self, **kwargs):
        """
        更新元数据
        :param kwargs: 要更新的字段和值
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """
        转换为字典格式
        :return: 字典格式的元数据
        """
        return {
            "title": self.title,
            "description": self.description,
            "episode": self.episode,
            "season": self.season,
            "year": self.year,
            "resolution": self.resolution,
            "duration": self.duration,
            "codec": self.codec,
            "width": self.width,
            "height": self.height,
            "bitrate": self.bitrate,
            "fps": self.fps,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoMetadata":
        """
        从字典创建元数据对象
        :param data: 字典格式的元数据
        :return: VideoMetadata实例
        """
        if "created_at" in data and data["created_at"]:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and data["updated_at"]:
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
