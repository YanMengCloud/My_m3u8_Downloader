import os
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime
from services.m3u8_downloader import M3U8Downloader
from models.task import Task, download_tasks, TaskModel
from models.database import get_session

logger = logging.getLogger(__name__)


def create_download_task(
    url: str, filename: str = None, format_type: str = "mp4"
) -> Dict:
    """创建下载任务"""
    try:
        task_id = str(uuid.uuid4())
        logger.info(
            f"创建下载任务: task_id={task_id}, url={url}, filename={filename}, format={format_type}"
        )

        # 创建任务
        task = Task(task_id, url, filename, format_type)

        # 获取任务状态
        task_status = task.get_status()
        logger.info(f"任务创建成功: {task_status}")

        return task_status
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}", exc_info=True)
        raise


def start_download_task(task_id: str) -> bool:
    """开始下载任务"""
    try:
        task = download_tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False

        if task.status != "pending":
            logger.warning(f"任务状态不正确: {task.status}")
            return False

        # 在新线程中启动下载
        import threading

        thread = threading.Thread(target=task.start)
        thread.daemon = True
        thread.start()

        logger.info(f"任务启动成功: {task_id}")
        return True
    except Exception as e:
        logger.error(f"启动任务失败: {str(e)}", exc_info=True)
        return False


def get_task_status(task_id: str) -> Optional[Dict]:
    """获取任务状态"""
    try:
        task = download_tasks.get(task_id)
        if task:
            return task.get_status()

        # 如果内存中没有，尝试从数据库获取
        session = get_session()
        try:
            task_model = session.query(TaskModel).filter_by(id=task_id).first()
            if task_model:
                return task_model.to_dict()
        finally:
            session.close()

        return None
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}", exc_info=True)
        return None


def get_all_tasks() -> Dict[str, Dict]:
    """获取所有任务"""
    try:
        tasks = {}
        # 获取数据库中的任务
        session = get_session()
        try:
            task_models = session.query(TaskModel).all()
            for task_model in task_models:
                tasks[task_model.id] = task_model.to_dict()

                # 如果内存中有这个任务，使用内存中的状态（因为可能更新）
                if task_model.id in download_tasks:
                    tasks[task_model.id].update(
                        download_tasks[task_model.id].get_status()
                    )
                # 如果内存中没有这个任务且状态是 downloading，说明可能是异常退出，更新状态为 failed
                elif task_model.status == "downloading":
                    task_model.status = "failed"
                    task_model.error_message = "下载意外中断"
                    session.commit()
                    tasks[task_model.id]["status"] = "failed"
                    tasks[task_model.id]["error_message"] = "下载意外中断"
        finally:
            session.close()

        # 检查内存中的任务是否都在数据库中
        for task_id, task in download_tasks.items():
            if task_id not in tasks:
                # 如果内存中的任务不在数据库中，说明数据库同步失败
                # 将任务保存到数据库
                session = get_session()
                try:
                    task_status = task.get_status()
                    task_model = TaskModel(
                        id=task_id,
                        url=task_status["url"],
                        filename=task_status["filename"],
                        format_type=task_status["format_type"],
                        status=task_status["status"],
                        progress=task_status["progress"],
                        segments=task_status.get(
                            "segments", {"downloaded": 0, "total": 0}
                        ),
                        video_metadata=task_status.get("metadata", {}),
                        preview_path=task_status.get("preview_path"),
                    )
                    session.add(task_model)
                    session.commit()
                    tasks[task_id] = task_status
                except Exception as e:
                    logger.error(f"同步任务到数据库失败: {str(e)}", exc_info=True)
                finally:
                    session.close()

        return tasks
    except Exception as e:
        logger.error(f"获取所有任务失败: {str(e)}", exc_info=True)
        return {}


def cancel_task(task_id: str) -> bool:
    """取消任务"""
    try:
        task = download_tasks.get(task_id)
        session = get_session()
        try:
            task_model = session.query(TaskModel).filter_by(id=task_id).first()
            if not task_model:
                return False

            if task:
                task.cancel()

            task_model.status = "cancelled"
            session.commit()
            return True
        finally:
            session.close()
    except Exception as e:
        logger.error(f"取消任务失败: {str(e)}", exc_info=True)
        return False


def pause_task(task_id: str) -> bool:
    """暂停任务"""
    try:
        task = download_tasks.get(task_id)
        session = get_session()
        try:
            task_model = session.query(TaskModel).filter_by(id=task_id).first()
            if not task_model:
                return False

            if task:
                task.pause()

            task_model.status = "paused"
            session.commit()
            return True
        finally:
            session.close()
    except Exception as e:
        logger.error(f"暂停任务失败: {str(e)}", exc_info=True)
        return False


def resume_task(task_id: str) -> bool:
    """恢复任务"""
    try:
        task = download_tasks.get(task_id)
        session = get_session()
        try:
            task_model = session.query(TaskModel).filter_by(id=task_id).first()
            if not task_model:
                return False

            if task:
                task.resume()

            task_model.status = "downloading"
            session.commit()
            return True
        finally:
            session.close()
    except Exception as e:
        logger.error(f"恢复任务失败: {str(e)}", exc_info=True)
        return False
