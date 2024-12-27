from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base


class SchedulerJob(Base):
    __tablename__ = "scheduler_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(String(1000), nullable=True)
    cron_expression = Column(String(100))
    job_params = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class JobExecutionHistory(Base):
    __tablename__ = "job_execution_history"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20))  # SUCCESS, FAILED, RUNNING
    result = Column(JSON, nullable=True)
    error_message = Column(String(1000), nullable=True)
