import asyncio
from utils.logger import setup_logger

logger = setup_logger("dummy_login")


class DummyLogin:
    async def init_browser(self):
        """模拟初始化浏览器"""
        logger.info("模拟初始化浏览器")
        return True

    async def login(self):
        """模拟登录"""
        logger.info("模拟登录成功")
        return True

    async def close(self):
        """模拟关闭浏览器"""
        logger.info("模拟关闭浏览器")
        return True
