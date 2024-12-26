import asyncio
import aio_pika
import json
from datetime import datetime


async def process_message(message: aio_pika.IncomingMessage):
    """处理接收到的消息"""
    async with message.process():
        try:
            body = message.body.decode()
            data = json.loads(body)
            print(f"收到爬虫结果:")
            print(f"站点: {data['site_id']}")
            print(f"时间: {data['timestamp']}")
            print(f"数据条数: {len(data['data'])}")

        except Exception as e:
            print(f"处理消息时出错: {e}")


async def main():
    # 连接到RabbitMQ
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")

    async with connection:
        # 创建channel
        channel = await connection.channel()

        # 声明队列
        queue = await channel.declare_queue("crawl_results", durable=True)

        print(" [*] 等待爬虫结果消息. 按 CTRL+C 退出")

        # 开始接收消息
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_message(message)


if __name__ == "__main__":
    asyncio.run(main())
