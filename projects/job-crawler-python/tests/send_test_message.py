import asyncio
import aio_pika
import json


async def send_test_message():
    # 连接到RabbitMQ
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")

    async with connection:
        # 创建channel
        channel = await connection.channel()

        # 声明交换机，设置 durable=True 使其持久化
        exchange = await channel.declare_exchange(
            "job_crawler",
            aio_pika.ExchangeType.TOPIC,
            durable=True,  # 添加此参数，确保与已存在的 exchange 配置一致
        )

        # 测试消息
        message = {
            "site_id": "liepin.com",
            "keyword": "数据中台产品经理",
            "location": "北京",
            "limit": 5,
        }

        # 发送消息
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key="crawler.job",
        )

        print(f"已发送测试消息: {message}")


if __name__ == "__main__":
    asyncio.run(send_test_message())
