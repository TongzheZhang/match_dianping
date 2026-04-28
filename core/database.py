"""数据库连接与初始化"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
from utils.logger import logger

# 确保数据目录存在
os.makedirs(os.path.dirname(settings.database_path), exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.database_path}",
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    from core.models import Match, RawArticle, Analysis  # noqa
    Base.metadata.create_all(bind=engine)
    logger.info(f"数据库已初始化: {settings.database_path}")
