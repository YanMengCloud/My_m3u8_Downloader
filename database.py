import sqlite3
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file=None):
        self.db_file = db_file or os.getenv("DATABASE_PATH", "data/downloads.db")
        logger.info(f"Initializing database with file: {self.db_file}")
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        logger.info("Initializing database tables")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS downloads (
                    task_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    format_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    start_time TIMESTAMP,
                    total_size INTEGER DEFAULT 0,
                    downloaded_size INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
        logger.info("Database tables initialized successfully")

    def add_task(self, task_id, url, filename, format_type):
        logger.info(f"Adding task to database: {task_id}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO downloads 
                    (task_id, url, filename, format_type, status, start_time)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (task_id, url, filename, format_type, "pending"),
                )
                conn.commit()
                logger.info(f"Task {task_id} added successfully")
        except Exception as e:
            logger.error(f"Database error in add_task: {str(e)}")
            raise

    def save_task(self, task):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO downloads 
                (task_id, url, filename, format_type, status, progress, start_time, 
                total_size, downloaded_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task.task_id,
                    task.m3u8_url,
                    task.filename,
                    task.format_type,
                    task.status,
                    task.progress,
                    task.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    task.total_size,
                    task.downloaded_size,
                ),
            )
            conn.commit()

    def get_all_tasks(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads ORDER BY created_at DESC")
            return cursor.fetchall()

    def delete_task(self, task_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM downloads WHERE task_id = ?", (task_id,))
            conn.commit()

    def update_task_status(self, task_id, status, progress=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if progress is not None:
                cursor.execute(
                    """
                    UPDATE downloads 
                    SET status = ?, progress = ? 
                    WHERE task_id = ?
                """,
                    (status, progress, task_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE downloads 
                    SET status = ? 
                    WHERE task_id = ?
                """,
                    (status, task_id),
                )
            conn.commit()
