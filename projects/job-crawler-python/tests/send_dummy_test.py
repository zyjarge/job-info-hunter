import asyncio
import aio_pika
import json
import os
import sys
from pathlib import Path


async def send_test_message():

    # 获取项目根目录
    root_dir = Path(__file__).parent.parent

    # 读取配置文件
    with open(os.path.join(root_dir, "conf", "config.json"), "r") as f:
        config = json.load(f)
        mq_config = config["mq"]

    # 连接到RabbitMQ
    connection = await aio_pika.connect_robust(
        f"amqp://{mq_config['username']}:{mq_config['password']}@{mq_config['host']}:{mq_config['port']}/"
    )

    async with connection:
        # 创建channel
        channel = await connection.channel()

        # 声明交换机
        exchange = await channel.declare_exchange(
            mq_config["exchange"], aio_pika.ExchangeType.TOPIC, durable=True
        )

        # 测试消息
        message = {
            "site_id": "dummy.com",
            "keyword": "测试关键词",
            "location": "北京",
            "limit": 5,
        }

        # 发送消息
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=mq_config["routing_key"],
        )

        print(f"已发送测试消息: {message}")


if __name__ == "__main__":
    asyncio.run(send_test_message())
