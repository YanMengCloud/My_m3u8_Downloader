from models.database import get_session, TaskModel
import logging
from sqlalchemy import text
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置数据库连接信息
os.environ["DB_HOST"] = "postgres"  # 如果使用 Docker
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "ymbox"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "postgres"

# 打印连接信息
logger.info(f"数据库连接信息:")
logger.info(f"Host: {os.environ['DB_HOST']}")
logger.info(f"Port: {os.environ['DB_PORT']}")
logger.info(f"Database: {os.environ['DB_NAME']}")
logger.info(f"User: {os.environ['DB_USER']}")


def check_db_tasks():
    logger.info("开始检查数据库任务...")
    session = get_session()
    try:
        # 首先测试数据库连接
        session.execute(text("SELECT 1"))
        logger.info("数据库连接成功")

        tasks = session.query(TaskModel).all()
        logger.info(f"找到 {len(tasks)} 个任务")

        print("\n数据库中的任务：")
        for task in tasks:
            print(f"ID: {task.id}")
            print(f"文件名: {task.filename}")
            print(f"URL: {task.url}")
            print(f"状态: {task.status}")
            print("---")
    except Exception as e:
        logger.error(f"数据库操作失败: {str(e)}")
        # 打印更详细的错误信息
        import traceback

        logger.error(traceback.format_exc())
        raise
    finally:
        session.close()


if __name__ == "__main__":
    try:
        check_db_tasks()
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")
