"""数据库模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from core.database import Base


class Match(Base):
    """比赛信息"""
    __tablename__ = "matches"

    id = Column(String(32), primary_key=True)
    competition = Column(String(100), nullable=False)
    competition_code = Column(String(20))
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    match_date = Column(String(20), nullable=False)
    match_time = Column(String(10))
    status = Column(String(20), default="SCHEDULED")  # SCHEDULED, FINISHED, etc.
    home_team_id = Column(Integer)
    away_team_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    analyzed = Column(Integer, default=0)  # 0=未分析, 1=已分析


class RawArticle(Base):
    """采集的原始文章"""
    __tablename__ = "raw_articles"

    id = Column(String(32), primary_key=True)
    match_id = Column(String(32), nullable=False, index=True)
    title = Column(String(500))
    source = Column(String(200))
    url = Column(String(1000))
    content = Column(Text)
    publish_date = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)


class Analysis(Base):
    """AI生成的分析报告"""
    __tablename__ = "analyses"

    id = Column(String(32), primary_key=True)
    match_id = Column(String(32), nullable=False, index=True)
    home_team = Column(String(100))
    away_team = Column(String(100))
    competition = Column(String(100))
    content = Column(Text)  # Markdown 内容
    predicted_score = Column(String(50))
    prediction_direction = Column(String(50))  # 主胜/客胜/平局/让球等
    confidence = Column(String(20))  # 高/中/低
    model_used = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
