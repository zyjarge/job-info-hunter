#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import Dict, Any

from .dao.es_dao import ElasticsearchDAO
from .dao.redis_dao import RedisDAO
from .monitor.monitor_service import MonitorService
import aio_pika

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrawlDataHandler:
    """
    爬虫数据处理类，负责处理从消息队列接收到的爬虫结果
    """

    def __init__(self):
        self.es_dao = ElasticsearchDAO()
        self.redis_dao = RedisDAO()
        self.monitor_service = MonitorService()

    async def handle_crawl_result(self, message: Dict[str, Any]) -> bool:
        """
        处理爬虫结果的主要方法

        Args:
            message: 包含爬虫结果的消息字典

        Returns:
            bool: 处理是否成功
        """
        try:
            logger.info(
                f"Received crawl result message: {json.dumps(message, ensure_ascii=False)}"
            )

            # 1. 存储到 Elasticsearch
            es_result = await self.es_dao.save_job_data(message)
            if not es_result:
                logger.error("保存数据到 Elasticsearch 失败")
                return False

            # 2. 存储到 Redis (暂时只打日志)
            await self.redis_dao.cache_job_data(message)

            # 3. 发送监控指标 (暂时只打日志)
            await self.monitor_service.send_metrics(
                metric_name="crawl_data_processed",
                value=1,
                tags={"source": message.get("source", "unknown")},
            )

            logger.info("爬虫结果处理成功")
            return True

        except Exception as e:
            logger.error(f"处理爬虫结果时出错: {str(e)}")
            return False

    async def start(self):
        """
        启动数据处理服务，监听消息队列
        """
        logger.info("Starting crawl data handler service...")
        try:
            # 从配置文件读取MQ配置
            with open("conf/mq.json", "r") as f:
                mq_config = json.load(f)

            # 构建RabbitMQ连接URL
            mq_url = f"amqp://{mq_config['username']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/"

            # 连接到RabbitMQ
            connection = await aio_pika.connect_robust(mq_url)

            async with connection:
                # 创建channel
                channel = await connection.channel()

                # 声明队列
                queue = await channel.declare_queue("crawl_results", durable=True)

                logger.info("开始监听爬虫结果队列...")

                # 开始接收消息
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            try:
                                body = json.loads(message.body.decode())
                                await self.handle_crawl_result(body)
                            except json.JSONDecodeError:
                                logger.error(f"消息格式错误: {message.body}")
                            except Exception as e:
                                logger.error(f"处理消息时出错: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"启动消息队列监听失败: {e}", exc_info=True)
            raise
