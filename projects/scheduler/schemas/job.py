from pydantic import BaseModel
from typing import Optional, Dict
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


class JobResponse(JobBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
