from flask import (
    Flask,
    render_template,
    send_from_directory,
    request,
    jsonify,
    send_file,
)
from flask_cors import CORS
import logging
import os
import sys
import mimetypes
import json
import time
from sqlalchemy import text


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from routes.video import video_bp
from routes.task import task_bp
from routes.system import system_bp
from models.database import Base, engine, Session
from routes.video_library import video_library_bp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置werkzeug日志级别为WARNING
logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_app():
    app = Flask(__name__)

    # 添加CORS支持
    CORS(app, resources={r"/*": {"origins": "*"}})

    # 初始化配置
    Config.init_app(app)

    # 确保必要的目录存在
    os.makedirs(os.path.join("static", "video_library"), exist_ok=True)

    # 等待数据库就绪
    def wait_for_db():
        max_retries = 30
        retry_interval = 2

        for i in range(max_retries):
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    logger.info("数据库连接成功")
                    break
            except Exception as e:
                if i < max_retries - 1:
                    logger.warning(f"等待数据库就绪... ({i+1}/{max_retries})")
                    time.sleep(retry_interval)
                else:
                    logger.error("数据库连接失败")
                    raise

    # 等待数据库
    wait_for_db()

    # 确保数据库表存在
    logger.info("正在初始化数据库表...")
    Base.metadata.create_all(engine)
    logger.info("数据库表初始化完成")

    # 注册蓝图
    app.register_blueprint(video_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(video_library_bp)

    @app.route("/")
    def index():
        logger.info("访问首页")
        return render_template("index.html")

    # 添加访问temp目录的路由
    @app.route("/temp/<path:filename>")
    def serve_temp(filename):
        """提供temp目录下的文件访问"""
        return send_from_directory("temp", filename)

    @app.route("/api/task/<task_id>/video")
    def serve_video(task_id):
        """提供视频文件访问"""
        try:
            # 首先尝试从info.json获取文件名
            info_path = os.path.join("temp", task_id, "info.json")
            if os.path.exists(info_path):
                with open(info_path, "r") as f:
                    info = json.load(f)
                    if "format" in info and "filename" in info["format"]:
                        video_file = info["format"]["filename"]
                        video_path = os.path.join("temp", task_id)
                        full_path = os.path.join(video_path, video_file)
                        if os.path.exists(full_path):
                            logger.info(f"从info.json找到视频文件: {full_path}")
                            return send_from_directory(video_path, video_file)

            # 如果info.json不存在或没有找到文件名，尝试默认的output.mp4
            video_path = os.path.join("temp", task_id)
            video_file = "output.mp4"
            full_path = os.path.join(video_path, video_file)

            logger.info(f"尝试访问视频文件: {full_path}")

            if not os.path.exists(video_path):
                logger.error(f"视频目录不存在: {video_path}")
                return jsonify({"error": "视频目录不存在"}), 404

            if not os.path.exists(full_path):
                logger.error(f"视频文件不存在: {full_path}")
                return jsonify({"error": "视频文件不存在"}), 404

            # 获取文件的MIME类型
            mime_type, _ = mimetypes.guess_type(video_file)
            if not mime_type:
                mime_type = "video/mp4"  # 默认MIME类型

            logger.info(f"提供视频文件: {full_path}, MIME类型: {mime_type}")
            return send_from_directory(
                video_path, video_file, mimetype=mime_type, as_attachment=False
            )

        except Exception as e:
            logger.error(f"视频访问错误: {str(e)}")
            return jsonify({"error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    logger.info("启动服务器...")
    logger.info(f'Flask 环境: {os.getenv("FLASK_ENV")}')
    logger.info(f'Flask 端口: {os.getenv("FLASK_RUN_PORT", 7101)}')
    logger.info(f'Flask 主机: {os.getenv("FLASK_RUN_HOST", "0.0.0.0")}')
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_RUN_PORT", 7101)), debug=True)
