class Config:
    MAX_CONCURRENT_DOWNLOADS = 3  # 最大并发下载数
    SPEED_LIMIT = 0  # 下载速度限制 (bytes/s)，0表示不限制
    AUTO_CLEANUP_DAYS = 7  # 临时文件保留天数
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    VERIFY_SSL = True  # SSL证书验证
    MAX_RETRIES = 3  # 最大重试次数
    CHUNK_SIZE = 8192  # 下载块大小
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"m3u8", "txt"}

    # 视频预览设置
    PREVIEW_MAX_FRAMES = 6  # 预览图最大帧数
    PREVIEW_FRAME_WIDTH = 320  # 预览图帧宽度
    PREVIEW_FRAME_HEIGHT = 180  # 预览图帧高度
    PREVIEW_SAMPLE_DURATION = 5  # 预览视频采样时长（秒）

    # 静态文件设置
    STATIC_FOLDER = "static"
    PREVIEW_FOLDER = "static/previews"
    TEMP_FOLDER = "temp"

    # 日志设置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def init_app(cls, app):
        """
        初始化应用配置
        """
        import os
        import logging

        # 创建必要的目录
        for folder in [cls.UPLOAD_FOLDER, cls.PREVIEW_FOLDER, cls.TEMP_FOLDER]:
            os.makedirs(folder, exist_ok=True)

        # 配置日志
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL), format=cls.LOG_FORMAT
        )

        # 配置Flask应用
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
        app.config["UPLOAD_FOLDER"] = cls.UPLOAD_FOLDER
        app.config["STATIC_FOLDER"] = cls.STATIC_FOLDER
