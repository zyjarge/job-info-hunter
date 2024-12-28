import logging
from datetime import datetime
import json
import pika
import time
from sqlalchemy.exc import OperationalError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from models.job import SchedulerJob, JobExecutionHistory
from schemas.job import JobCreate, JobUpdate
from conf.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_VHOST,
)


class JobScheduler:
    def __init__(self, db: Session):
        self.scheduler = BackgroundScheduler(
            timezone="Asia/Shanghai",  # 设置时区
            job_defaults={
                "coalesce": True,  # 错过的任务只执行一次
                "max_instances": 1,  # 同一个任务同时只能有一个实例在运行
                "misfire_grace_time": 60,  # 任务错过执行时间的容错范围（秒）
            },
        )
        self.db = db
        self.logger = logging.getLogger(__name__)

        # 启动调度器
        self.scheduler.start()

        # 启动后等待一段时间再加载任务，确保数据库连接就绪
        self._init_with_retry()

    def _init_with_retry(self, max_retries=5, retry_interval=5):
        """初始化时进行重试"""
        for attempt in range(max_retries):
            try:
                self.logger.info("尝试从数据库加载任务...")
                self._load_jobs_from_db()
                self.logger.info("成功加载所有任务")
                return
            except OperationalError as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"数据库连接失败，{retry_interval}秒后重试: {str(e)}"
                    )
                    time.sleep(retry_interval)
                else:
                    self.logger.error(f"数据库连接失败，已达到最大重试次数: {str(e)}")
                    raise
            except Exception as e:
                self.logger.error(f"加载任务时发生错误: {str(e)}")
                raise

    def _load_jobs_from_db(self):
        """从数据库加载所有活跃的任务"""
        try:
            # 先清理当前的任务
            for job in self.scheduler.get_jobs():
                job.remove()

            # 加载数据库中的活跃任务
            active_jobs = (
                self.db.query(SchedulerJob).filter(SchedulerJob.is_active == True).all()
            )

            loaded_count = 0
            for job in active_jobs:
                self.logger.info(f"正在从数据库加载任务 {job.id}: {job.name}")
                try:
                    self.scheduler.add_job(
                        self._execute_job,
                        CronTrigger.from_crontab(job.cron_expression),
                        args=[job.id, job.job_params],
                        id=str(job.id),
                        name=job.name,
                        replace_existing=True,  # 如果任务已存在则替换
                        misfire_grace_time=60,  # 错过执行时间的容错范围
                    )
                    loaded_count += 1
                except Exception as e:
                    self.logger.error(f"加载任务 {job.id} 失败: {str(e)}")

            self.logger.info(f"成功加载 {loaded_count}/{len(active_jobs)} 个任务")
        except Exception as e:
            self.logger.error(f"从数据库加载任务失败: {str(e)}")

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

            # 声明交换机和队列
            channel.exchange_declare(
                exchange="job_crawler",
                exchange_type="topic",
                durable=True,
            )
            channel.queue_declare(queue="crawler-jobs", durable=True)
            channel.queue_bind(
                exchange="job_crawler", queue="crawler-jobs", routing_key="crawler.job"
            )

            # 发送消息
            message = json.dumps(job_params)
            channel.basic_publish(
                exchange="job_crawler",
                routing_key="crawler.job",
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 消息持久化
                ),
            )

            connection.close()

            # 更新执行历史为成功
            history.status = "SUCCESS"
            history.end_time = datetime.now()
            history.result = {"message": "任务已成功发送到队列"}

        except Exception as e:
            # 更新执行历史为失败
            history.status = "FAILED"
            history.end_time = datetime.now()
            history.error_message = str(e)
            self.logger.error(f"任务 {job_id} 执行失败: {str(e)}")

        finally:
            self.db.commit()

    def create_job(self, job: JobCreate) -> SchedulerJob:
        """创建新的定时任务"""
        # 创建任务记录
        db_job = SchedulerJob(
            name=job.name,
            description=job.description,
            cron_expression=job.cron_expression,
            job_params=job.job_params,
            is_active=True,
        )
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)

        # 添加到调度器
        self.scheduler.add_job(
            self._execute_job,
            CronTrigger.from_crontab(job.cron_expression),
            args=[db_job.id, job.job_params],
            id=str(db_job.id),
            name=job.name,
            replace_existing=True,  # 如果任务已存在则替换
            misfire_grace_time=60,  # 错过执行时间的容错范围
        )
        return db_job

    def get_jobs(self) -> list[SchedulerJob]:
        """获取所有任务"""
        return self.db.query(SchedulerJob).all()

    def get_job(self, job_id: str) -> SchedulerJob:
        """获取指定任务"""
        return (
            self.db.query(SchedulerJob).filter(SchedulerJob.id == int(job_id)).first()
        )

    def update_job(self, job_id: str, job_update: JobUpdate) -> SchedulerJob:
        """更新任务"""
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == int(job_id)).first()
        if not job:
            return None

        # 更新数据库中的任务信息
        if job_update.name is not None:
            job.name = job_update.name
        if job_update.description is not None:
            job.description = job_update.description
        if job_update.cron_expression is not None:
            job.cron_expression = job_update.cron_expression
        if job_update.job_params is not None:
            job.job_params = job_update.job_params

        self.db.commit()

        # 更新调度器中的任务
        if job_update.cron_expression is not None or job_update.job_params is not None:
            self.scheduler.add_job(
                self._execute_job,
                CronTrigger.from_crontab(job.cron_expression),
                args=[job.id, job.job_params],
                id=str(job.id),
                name=job.name,
                replace_existing=True,  # 如果任务已存在则替换
                misfire_grace_time=60,  # 错过执行时间的容错范围
            )

        return job

    def delete_job(self, job_id: str) -> bool:
        """删除任务"""
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == int(job_id)).first()
        if not job:
            return False

        try:
            # 尝试从APScheduler中删除任务
            try:
                self.scheduler.remove_job(str(job_id))
            except Exception as e:
                self.logger.warning(f"从APScheduler中删除任务 {job_id} 失败: {str(e)}")

            # 从数据库中删除任务
            self.db.delete(job)
            self.db.commit()
            return True

        except Exception as e:
            self.logger.error(f"删除任务 {job_id} 失败: {str(e)}")
            self.db.rollback()
            return False

    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == int(job_id)).first()
        if not job:
            return False

        try:
            # 更新数据库状态
            job.is_active = False
            self.db.commit()

            # 暂停APScheduler中的任务
            scheduler_job = self.scheduler.get_job(str(job_id))
            if scheduler_job:
                scheduler_job.pause()
            return True

        except Exception as e:
            self.logger.error(f"暂停任务 {job_id} 失败: {str(e)}")
            self.db.rollback()
            return False

    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == int(job_id)).first()
        if not job:
            return False

        try:
            # 更新数据库状态
            job.is_active = True
            self.db.commit()

            # 恢复APScheduler中的任务
            scheduler_job = self.scheduler.get_job(str(job_id))
            if scheduler_job:
                scheduler_job.resume()
            else:
                # 如果任务不存在于APScheduler中，重新添加
                self.scheduler.add_job(
                    self._execute_job,
                    CronTrigger.from_crontab(job.cron_expression),
                    args=[job.id, job.job_params],
                    id=str(job.id),
                    name=job.name,
                )
            return True

        except Exception as e:
            self.logger.error(f"恢复任务 {job_id} 失败: {str(e)}")
            self.db.rollback()
            return False

    def run_job(self, job_id: str) -> bool:
        """立即执行任务"""
        job = self.db.query(SchedulerJob).filter(SchedulerJob.id == int(job_id)).first()
        if not job:
            return False

        try:
            self._execute_job(int(job_id), job.job_params)
            return True
        except Exception as e:
            self.logger.error(f"执行任务 {job_id} 失败: {str(e)}")
            return False

    def get_scheduler_jobs(self):
        """获取APScheduler中所有任务的状态"""
        jobs = self.scheduler.get_jobs()
        result = []
        for job in jobs:
            # 获取触发器信息
            trigger_info = self._get_trigger_info(job.trigger, job)

            # 构建任务状态
            job_state = {
                "id": job.id,
                "name": job.name,
                "func": job.func.__name__,
                "args": list(job.args),
                "kwargs": job.kwargs,
                "trigger": trigger_info,
                "next_run_time": job.next_run_time,
                "pending": getattr(job, "pending", False),
                "paused": job.next_run_time is None,
            }
            result.append(job_state)
        return result

    def get_scheduler_job(self, job_id: str):
        """获取APScheduler中特定任务的状态

        Args:
            job_id: 任务ID（字符串类型）
        """
        try:
            # 先尝试直接用字符串ID获取
            job = self.scheduler.get_job(job_id)
            if not job:
                # 如果找不到，尝试将整数ID转换为字符串后再查找
                job = self.scheduler.get_job(str(int(job_id)))

            if not job:
                return None

            # 获取触发器信息
            trigger_info = self._get_trigger_info(job.trigger, job)

            # 构建任务状态
            return {
                "id": job.id,
                "name": job.name,
                "func": job.func.__name__,
                "args": list(job.args),
                "kwargs": job.kwargs,
                "trigger": trigger_info,
                "next_run_time": job.next_run_time,
                "pending": getattr(job, "pending", False),
                "paused": job.next_run_time is None,
            }
        except ValueError:
            # 如果 job_id 不能转换为整数，返回 None
            self.logger.warning(f"无效的任务ID格式: {job_id}")
            return None
        except Exception as e:
            self.logger.error(f"获取任务 {job_id} 状态失败: {str(e)}")
            return None

    def _get_trigger_info(self, trigger, job):
        """获取触发器信息

        Args:
            trigger: APScheduler的触发器对象
            job: APScheduler的任务对象
        """
        trigger_type = trigger.__class__.__name__
        if trigger_type == "CronTrigger":
            # 使用 get_jobs() 返回的字段值
            fields = {
                "second": trigger.fields[0],
                "minute": trigger.fields[1],
                "hour": trigger.fields[2],
                "day": trigger.fields[3],
                "month": trigger.fields[4],
                "day_of_week": trigger.fields[5],
            }
            # 重建 cron 表达式
            trigger_expr = f"{fields['minute']} {fields['hour']} {fields['day']} {fields['month']} {fields['day_of_week']}"
        else:
            trigger_expr = str(trigger)

        return {
            "type": trigger_type,
            "expression": trigger_expr,
            "next_run_time": job.next_run_time,  # 从 job 对象获取下次运行时间
            "timezone": str(trigger.timezone),  # 添加时区信息
        }
