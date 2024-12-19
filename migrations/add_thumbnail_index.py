from sqlalchemy import create_engine, text
from models.database import DATABASE_URL
import logging

logger = logging.getLogger(__name__)


def migrate():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # 添加 thumbnail_index 列
            connection.execute(
                text(
                    """
                ALTER TABLE video_library 
                ADD COLUMN IF NOT EXISTS thumbnail_index INTEGER DEFAULT 0
            """
                )
            )
            connection.commit()
            logger.info("成功添加 thumbnail_index 列")
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        raise
