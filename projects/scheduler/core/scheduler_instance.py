"""全局调度器实例管理"""

from typing import Optional
from .scheduler import JobScheduler

# 全局调度器实例
_scheduler: Optional[JobScheduler] = None


def get_scheduler() -> Optional[JobScheduler]:
    """获取全局调度器实例"""
    global _scheduler
    return _scheduler


def set_scheduler(scheduler: JobScheduler):
    """设置全局调度器实例"""
    global _scheduler
    _scheduler = scheduler


def clear_scheduler():
    """清理全局调度器实例"""
    global _scheduler
    if _scheduler:
        _scheduler.scheduler.shutdown(wait=True)  # 等待所有正在运行的任务完成
        _scheduler.db.close()
        _scheduler = None
