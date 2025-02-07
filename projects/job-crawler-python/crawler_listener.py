import asyncio
import json
import os
import importlib
from typing import Dict, Any
import aio_pika
from utils.logger import setup_logger
import sys
from pathlib import Path
from utils.mq_publisher import MQPublisher
from datetime import datetime
from utils.config_manager import ConfigManager

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 初始化日志记录器
logger = setup_logger("crawler_listener")


class CrawlerListener:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.publisher = None
        self.connection = None
        self.channel = None

    async def init_configs(self):
        """初始化配置"""
        try:
            # 启动配置管理器，并设置配置更新回调
            await self.config_manager.start(self._on_config_update)
            # 获取初始配置
            self.site_mapping = self.config_manager.site_mapping
            self.mq_config = await self.config_manager.get_mq_config()

            # 初始化 MQ 发布者
            self.publisher = MQPublisher(self.mq_config)

            logger.info("配置初始化成功")
        except Exception as e:
            logger.error(f"配置初始化失败: {e}")
            raise

    async def _on_config_update(self, new_site_mapping: Dict[str, Any]):
        """配置更新回调"""
        logger.info("检测到站点配置变更")
        self.site_mapping = new_site_mapping
        logger.info(f"已更新站点配置，当前有 {len(self.site_mapping)} 个有效站点")

    async def connect(self):
        """连接到RabbitMQ"""
        try:

            # 构建RabbitMQ连接URL
            mq_url = (
                f"amqp://{self.mq_config['username']}:{self.mq_config['password']}@"
                f"{self.mq_config['host']}:{self.mq_config['port']}/"
            )
            logger.info(
                f"正在连接 RabbitMQ，地址: {self.mq_config['host']}:{self.mq_config['port']}"
            )

            self.connection = await aio_pika.connect_robust(mq_url)
            self.channel = await self.connection.channel()

            # 声明交换机
            exchange = await self.channel.declare_exchange(
                self.mq_config["exchange"], aio_pika.ExchangeType.TOPIC, durable=True
            )

            # 声明队列
            queue = await self.channel.declare_queue(
                self.mq_config["queue_name"], durable=True
            )

            # 绑定队列到交换机
            await queue.bind(exchange, routing_key=self.mq_config["routing_key"])

            logger.info("RabbitMQ连接成功")
            return queue

        except Exception as e:
            logger.error(f"RabbitMQ连接失败: {e}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        """处理接收到的消息"""
        async with message.process():
            try:
                # 解析消息内容
                body = message.body.decode()
                data = json.loads(body)
                logger.info(f"收到爬虫任务: {data}")

                # 提取必要参数
                site_id = data.get("site_id")
                keyword = data.get("keyword")
                location = data.get("location")
                limit = data.get("limit", 100)

                if not site_id or not keyword:
                    logger.error(f"消息格式错误，缺少必要参数: {data}")
                    return

                # 获取对应站点的爬虫配置
                site_config = self.site_mapping.get(site_id)
                if not site_config:
                    logger.error(f"未找到站点配置: {site_id}")
                    return

                # 动态导入并实例化爬虫类
                results = await self.run_crawler(site_config, keyword, location, limit)

                # 发送爬取结果到消息队列
                if results:
                    await self.publisher.publish_results(
                        results, site_config["site_id"]
                    )
                    logger.info(f"已发送 {len(results)} 条数据到结果队列")

            except json.JSONDecodeError:
                logger.error(f"消息格式错误: {body}")
            except Exception as e:
                logger.error(f"处理消息时出错: {e}", exc_info=True)

    async def run_crawler(
        self,
        site_config: Dict[str, str],
        keyword: str,
        location: str = None,
        limit: int = 100,
    ):
        """运行指定的爬虫"""
        results = []
        try:
            # 动态导入登录模块和类
            login_module = importlib.import_module(site_config["login_module"])
            login_class = getattr(login_module, site_config["login_class"])
            logger.debug(f"登录模块: {login_module}, 登录类: {login_class}")

            # 动态导入爬虫模块和类
            crawler_module = importlib.import_module(site_config["module"])
            crawler_class = getattr(crawler_module, site_config["class"])
            logger.debug(f"爬虫模块: {crawler_module}, 爬虫类: {crawler_class}")

            # 实例化登录类
            login_instance = login_class()
            await login_instance.init_browser()

            try:
                # 执行登录
                if await login_instance.login():
                    logger.info("登录成功，开始爬取数据")

                    # 实例化爬虫类
                    crawler = crawler_class(login_instance)

                    # 执行爬取
                    results = await crawler.search(
                        keyword=keyword, location=location, limit=limit
                    )
                    logger.info(f"爬取完成，获取到 {len(results)} 条数据")
                else:
                    logger.error("登录失败")

            finally:
                # 确保浏览器正确关闭
                await login_instance.close()
                return results

        except Exception as e:
            logger.error(f"运行爬虫时出错: {e}", exc_info=True)

    async def start(self):
        """启动消息监听"""
        try:
            logger.info("爬虫监听器启动中...")

            # 初始化配置
            await self.init_configs()

            # 连接到消息队列
            queue = await self.connect()
            logger.info(f"开始监听队列: {self.mq_config['queue_name']}")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.process_message(message)

        except Exception as e:
            logger.error(f"消息监听出错: {e}", exc_info=True)
        finally:
            if self.connection:
                await self.connection.close()
            if self.publisher:
                await self.publisher.close()

    async def close(self):
        """关闭资源"""
        if self.connection:
            await self.connection.close()
        if self.publisher:
            await self.publisher.close()
        await self.config_manager.stop()


async def main():
    listener = CrawlerListener()
    await listener.start()


if __name__ == "__main__":
    asyncio.run(main())
