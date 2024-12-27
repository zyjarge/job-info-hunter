import logging
from datetime import datetime
import json
import pika
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from models.job import SchedulerJob, JobExecutionHistory
from conf.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VHOST,
)


class JobScheduler:
    def __init__(self, db: Session):
        self.scheduler = BackgroundScheduler()
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.scheduler.start()

    def _get_rabbitmq_connection(self):
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=RABBITMQ_VHOST,
            credentials=credentials,
        )
        return pika.BlockingConnection(parameters)

    def _execute_job(self, job_id: int, job_params: dict):
        # 记录任务开始执行
        history = JobExecutionHistory(
            job_id=job_id, start_time=datetime.now(), status="RUNNING"
        )
        self.db.add(history)
        self.db.commit()

        try:
            # 连接RabbitMQ并发送消息
            connection = self._get_rabbitmq_connection()
            channel = connection.channel()

            # 确保队列存在
            channel.queue_declare(queue="crawler_tasks", durable=True)

            # 发送消息
            message = json.dumps(job_params)
            channel.basic_publish(
                exchange="",
                routing_key="crawler_tasks",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 消息持久化
                ),
            )

            connection.close()

            # 更新执行历史为成功
            history.status = "SUCCESS"
            history.end_time = datetime.now()
            history.result = {"message": "Task sent to queue successfully"}

        except Exception as e:
            # 更新执行历史为失败
            history.status = "FAILED"
            history.end_time = datetime.now()
            history.error_message = str(e)
            self.logger.error(f"Job {job_id} execution failed: {str(e)}")

        finally:
            self.db.commit()

    def add_job(
        self, name: str, description: str, cron_expression: str, job_params: dict
    ):
        # 创建任务记录
        job = SchedulerJob(
            name=name,
            description=description,
            cron_expression=cron_expression,
            job_params=job_params,
            is_active=True,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # 添加到调度器
        self.scheduler.add_job(
            self._execute_job,
            CronTrigger.from_crontab(cron_expression),
            args=[job.id, job_params],
            id=str(job.id),
            name=name,
        )
        return job

    def update_job(
        self,
        job_id: int,
        name: str = None,
        description: str = None,
        cron_expression: str = None,
        job_params: dict = None,
    ):
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # 更新数据库中的任务信息
        if name:
            job.name = name
        if description:
            job.description = description
        if cron_expression:
            job.cron_expression = cron_expression
        if job_params:
            job.job_params = job_params

        self.db.commit()

        # 更新调度器中的任务
        if cron_expression or job_params:
            self.scheduler.remove_job(str(job_id))
            self.scheduler.add_job(
                self._execute_job,
                CronTrigger.from_crontab(job.cron_expression),
                args=[job.id, job.job_params],
                id=str(job.id),
                name=job.name,
            )

        return job

    def delete_job(self, job_id: int):
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # 从调度器中移除任务
        self.scheduler.remove_job(str(job_id))

        # 从数据库中删除任务
        self.db.delete(job)
        self.db.commit()

    def pause_job(self, job_id: int):
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.is_active = False
        self.db.commit()
        self.scheduler.pause_job(str(job_id))

    def resume_job(self, job_id: int):
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.is_active = True
        self.db.commit()
        self.scheduler.resume_job(str(job_id))

    def get_job(self, job_id: int):
        return self.db.query(SchedulerJob).filter(SchedulerJob.id == job_id).first()

    def get_all_jobs(self):
        return self.db.query(SchedulerJob).all()

    def get_job_history(self, job_id: int):
        return (
            self.db.query(JobExecutionHistory)
            .filter(JobExecutionHistory.job_id == job_id)
            .order_by(JobExecutionHistory.start_time.desc())
            .all()
        )
