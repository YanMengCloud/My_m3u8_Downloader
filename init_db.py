from models.database import Base, engine


def init_db():
    """初始化数据库表"""
    Base.metadata.drop_all(engine)  # 删除所有表
    Base.metadata.create_all(engine)  # 创建所有表


if __name__ == "__main__":
    init_db()
