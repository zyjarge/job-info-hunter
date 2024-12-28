import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from models.base import engine, Base, SessionLocal
from conf.config import API_HOST, API_PORT
from core.scheduler import JobScheduler
from core.scheduler_instance import set_scheduler, clear_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Scheduler API",
    description="API for managing scheduled crawler jobs",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化调度器"""
    db = SessionLocal()
    scheduler = JobScheduler(db)
    set_scheduler(scheduler)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    clear_scheduler()


# 注册路由
app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)
