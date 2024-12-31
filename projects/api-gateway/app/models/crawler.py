from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from app.db.base_class import Base


class Crawler(Base):
    __tablename__ = "crawlers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    homepage = Column(String, nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(JSON, nullable=False)  # 存储爬虫配置信息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
