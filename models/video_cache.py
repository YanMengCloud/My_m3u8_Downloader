from typing import Dict, Optional
import threading


class VideoCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.cache = {}
            return cls._instance

    def get(self, video_id: int) -> Optional[Dict]:
        """获取视频信息"""
        return self.cache.get(video_id)

    def set(self, video_id: int, video_info: Dict):
        """设置视频信息"""
        self.cache[video_id] = video_info

    def delete(self, video_id: int):
        """删除视频信息"""
        if video_id in self.cache:
            del self.cache[video_id]

    def update(self, video_id: int, video_info: Dict):
        """更新视频信息"""
        if video_id in self.cache:
            self.cache[video_id].update(video_info)

    def clear(self):
        """清空缓存"""
        self.cache.clear()


video_cache = VideoCache()
