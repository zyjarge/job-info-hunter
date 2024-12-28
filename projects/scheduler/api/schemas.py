from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


class JobBase(BaseModel):
    name: str
    description: Optional[str] = None
    cron_expression: str
    job_params: Dict


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    job_params: Optional[Dict] = None


class JobExecutionHistoryResponse(BaseModel):
    id: int
    job_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    result: Optional[Dict]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class JobResponse(JobBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    execution_history: List[JobExecutionHistoryResponse]


# APScheduler相关的模型
class APSchedulerJobTrigger(BaseModel):
    """APScheduler触发器信息"""

    type: str
    expression: str
    next_run_time: Optional[datetime]


class APSchedulerJobState(BaseModel):
    """APScheduler任务状态"""

    id: str
    name: str
    func: str
    args: List[Any]
    kwargs: Dict[str, Any]
    trigger: APSchedulerJobTrigger
    next_run_time: Optional[datetime]
    pending: bool
    paused: bool
