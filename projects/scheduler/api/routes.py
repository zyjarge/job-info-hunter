from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from models.base import SessionLocal
from models.job import SchedulerJob
from schemas.job import JobCreate, JobUpdate, JobResponse
from core.scheduler_instance import get_scheduler

router = APIRouter()


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/jobs/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """创建新的定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    return scheduler.create_job(job)


@router.get("/jobs/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    """获取所有定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    return scheduler.get_jobs()


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """获取指定定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务未找到")
    return job


@router.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: str, job_update: JobUpdate, db: Session = Depends(get_db)):
    """更新定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    job = scheduler.update_job(job_id, job_update)
    if not job:
        raise HTTPException(status_code=404, detail="任务未找到")
    return job


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """删除定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    if not scheduler.delete_job(job_id):
        raise HTTPException(status_code=404, detail="任务未找到")
    return {"message": "任务已删除"}


@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: str, db: Session = Depends(get_db)):
    """暂停定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    if not scheduler.pause_job(job_id):
        raise HTTPException(status_code=404, detail="任务未找到")
    return {"message": "任务已暂停"}


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: str, db: Session = Depends(get_db)):
    """恢复定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    if not scheduler.resume_job(job_id):
        raise HTTPException(status_code=404, detail="任务未找到")
    return {"message": "任务已恢复"}


@router.post("/jobs/{job_id}/run")
def run_job(job_id: str, db: Session = Depends(get_db)):
    """立即执行定时任务"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    if not scheduler.run_job(job_id):
        raise HTTPException(status_code=404, detail="任务未找到")
    return {"message": "任务已触发执行"}


# APScheduler 相关路由
@router.get("/scheduler/jobs")
def list_scheduler_jobs(db: Session = Depends(get_db)):
    """获取 APScheduler 中所有任务的状态"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")
    return scheduler.get_scheduler_jobs()


@router.get("/scheduler/jobs/{job_id}")
def get_scheduler_job(job_id: str, db: Session = Depends(get_db)):
    """获取 APScheduler 中特定任务的状态"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="调度器未初始化")

    job = scheduler.get_scheduler_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="APScheduler 中未找到该任务")

    return job  # 返回任务状态
