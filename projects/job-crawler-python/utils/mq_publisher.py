import json
import aio_pika
import logging
from datetime import datetime
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)


class MQPublisher:
    def __init__(self, mq_config: Dict[str, Any]):
        """初始化MQ发布者
        Args:
            mq_config: MQ配置信息
        """
        self.mq_config = mq_config
        self.connection = None
        self.channel = None
        self.exchange = None

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

            # 声明结果交换机
            self.exchange = await self.channel.declare_exchange(
                self.mq_config["exchange"], aio_pika.ExchangeType.TOPIC, durable=True
            )

            # 声明结果队列
            queue = await self.channel.declare_queue(
                self.mq_config["result_queue_name"], durable=True
            )

            # 绑定队列到交换机
            await queue.bind(
                self.exchange, routing_key=self.mq_config["result_routing_key"]
            )

            logger.info("RabbitMQ连接成功")

        except Exception as e:
            logger.error(f"RabbitMQ连接失败: {e}")
            raise

    async def publish_results(self, results: Dict[str, Any], site_id: str):
        """发布爬取结果到消息队列
        Args:
            results: 爬取结果
            site_id: 来源网站ID
        """
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()

            message = {
                "site_id": site_id,
                "timestamp": datetime.now().isoformat(),
                "data": results,
            }

            # 发送消息到结果队列
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=self.mq_config["result_routing_key"],
            )

            logger.info(f"结果发送成功: {site_id}, {len(results)} 条数据")

        except Exception as e:
            logger.error(f"发送结果失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
