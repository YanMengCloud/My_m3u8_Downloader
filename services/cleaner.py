import os
import time
from datetime import datetime, timedelta
from config import Config
import logging
import shutil
from models.database import TaskModel, get_session

logger = logging.getLogger(__name__)

# 任务过期天数
TASK_EXPIRY_DAYS = 7  # 可以从配置文件读取


class TempCleaner:
    @staticmethod
    def clean_temp_files():
        try:
            temp_days = Config.get_temp_file_days()
            if temp_days <= 0:  # 如果设置为0或负数，不清理
                return

            cutoff_time = datetime.now() - timedelta(days=temp_days)
            temp_dir = "temp"

            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path):
                    # 获取目录的最后修改时间
                    mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                    if mtime < cutoff_time:
                        try:
                            shutil.rmtree(item_path)
                            logger.info(f"已清理过期临时目录: {item_path}")
                        except Exception as e:
                            logger.error(f"清理临时目录失败 {item_path}: {str(e)}")

        except Exception as e:
            logger.error(f"清理临时文件时发生错误: {str(e)}")

    @staticmethod
    def clean_expired_tasks():
        """清理过期任务"""
        try:
            logger.info("开始清理过期任务")
            session = get_session()
            try:
                tasks = (
                    session.query(TaskModel)
                    .filter(TaskModel.status.in_(["completed", "failed", "cancelled"]))
                    .all()
                )

                for task in tasks:
                    # 检查任务是否已过期
                    if task.end_time:
                        elapsed_time = datetime.now() - task.end_time
                        if elapsed_time.days >= TASK_EXPIRY_DAYS:
                            logger.info(f"清理过期任务: {task.id}")

                            # 删除任务目录
                            task_dir = os.path.join("temp", task.id)
                            if os.path.exists(task_dir):
                                shutil.rmtree(task_dir)

                            # 删除数据库记录
                            session.delete(task)

                session.commit()
            finally:
                session.close()

            logger.info("清理过期任务完成")
        except Exception as e:
            logger.error(f"清理过期任务失败: {str(e)}")
