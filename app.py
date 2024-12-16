from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import logging
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from routes.video import video_bp
from routes.task import task_bp
from routes.system import system_bp
from models.database import Base, engine

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

    # 确保数据库表存在
    logger.info("正在初始化数据库表...")
    Base.metadata.create_all(engine)
    logger.info("数据库表初始化完成")

    # 注册蓝图
    app.register_blueprint(video_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(system_bp)

    @app.route("/")
    def index():
        logger.info("访问首页")
        return render_template("index.html")

    # 添加访问temp目录的路由
    @app.route("/temp/<path:filename>")
    def serve_temp(filename):
        """提供temp目录下的文件访问"""
        return send_from_directory("temp", filename)

    return app


if __name__ == "__main__":
    app = create_app()
    logger.info("启动服务器...")
    logger.info(f'Flask 环境: {os.getenv("FLASK_ENV")}')
    logger.info(f'Flask 端口: {os.getenv("FLASK_RUN_PORT", 7101)}')
    logger.info(f'Flask 主机: {os.getenv("FLASK_RUN_HOST", "0.0.0.0")}')
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_RUN_PORT", 7101)), debug=True)
