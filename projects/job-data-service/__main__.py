#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from crawl_data_handler import CrawlDataHandler

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """
    服务主入口
    """
    handler = CrawlDataHandler()
    try:
        await handler.start()
    except KeyboardInterrupt:
        logger.info("收到退出信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务运行出错: {e}", exc_info=True)
        raise
    finally:
        # 确保资源被正确关闭
        await handler.search_dao.close()


if __name__ == "__main__":
    asyncio.run(main())
