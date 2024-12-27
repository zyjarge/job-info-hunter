from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.scheduler import JobScheduler
from models.base import SessionLocal
from api import schemas

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_scheduler(db: Session = Depends(get_db)):
    return JobScheduler(db)


@router.post("/jobs/", response_model=schemas.JobResponse)
def create_job(
    job: schemas.JobCreate, scheduler: JobScheduler = Depends(get_scheduler)
):
    try:
        return scheduler.add_job(
            name=job.name,
            description=job.description,
            cron_expression=job.cron_expression,
            job_params=job.job_params,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/", response_model=List[schemas.JobResponse])
def list_jobs(scheduler: JobScheduler = Depends(get_scheduler)):
    return scheduler.get_all_jobs()


@router.get("/jobs/{job_id}", response_model=schemas.JobDetailResponse)
def get_job(job_id: int, scheduler: JobScheduler = Depends(get_scheduler)):
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 获取执行历史
    history = scheduler.get_job_history(job_id)

    # 构建响应
    response = schemas.JobDetailResponse(**job.__dict__, execution_history=history)
    return response


@router.put("/jobs/{job_id}", response_model=schemas.JobResponse)
def update_job(
    job_id: int,
    job_update: schemas.JobUpdate,
    scheduler: JobScheduler = Depends(get_scheduler),
):
    try:
        return scheduler.update_job(
            job_id=job_id,
            name=job_update.name,
            description=job_update.description,
            cron_expression=job_update.cron_expression,
            job_params=job_update.job_params,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, scheduler: JobScheduler = Depends(get_scheduler)):
    try:
        scheduler.delete_job(job_id)
        return {"message": "Job deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: int, scheduler: JobScheduler = Depends(get_scheduler)):
    try:
        scheduler.pause_job(job_id)
        return {"message": "Job paused successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: int, scheduler: JobScheduler = Depends(get_scheduler)):
    try:
        scheduler.resume_job(job_id)
        return {"message": "Job resumed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/jobs/{job_id}/history", response_model=List[schemas.JobExecutionHistoryResponse]
)
def get_job_history(job_id: int, scheduler: JobScheduler = Depends(get_scheduler)):
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return scheduler.get_job_history(job_id)
