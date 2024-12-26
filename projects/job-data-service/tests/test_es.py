#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
from elasticsearch import AsyncElasticsearch
from datetime import datetime


async def test_es_connection():
    """测试 ES 连接和基本操作"""

    # 创建 ES 客户端
    es_client = AsyncElasticsearch(
        hosts=["http://localhost:9200"],
        basic_auth=("elastic", "changeme"),
        verify_certs=False,
        request_timeout=30,
    )

    try:
        # 1. 测试连接
        print("Testing ES connection...")
        info = await es_client.info()
        print(f"ES info: {json.dumps(info, indent=2)}")

        # 2. 创建测试索引
        index_name = "test_jobs"
        if await es_client.indices.exists(index=index_name):
            print(f"Deleting existing index {index_name}")
            await es_client.indices.delete(index=index_name)

        print(f"Creating index {index_name}")
        await es_client.indices.create(
            index=index_name,
            mappings={
                "properties": {
                    "title": {"type": "text"},
                    "company": {"type": "keyword"},
                    "salary": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                }
            },
        )

        # 3. 插入测试数据
        test_docs = [
            {
                "title": "Python开发工程师",
                "company": "测试公司A",
                "salary": "20k-30k",
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "title": "数据工程师",
                "company": "测试公司B",
                "salary": "25k-35k",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]

        print("Inserting test documents...")
        for i, doc in enumerate(test_docs):
            response = await es_client.index(
                index=index_name, id=f"test_{i+1}", document=doc, refresh=True
            )
            print(f"Document {i+1} inserted: {response['result']}")

        # 4. 查询测试
        # 4.1 查询所有文档
        print("\nQuerying all documents:")
        response = await es_client.search(index=index_name, query={"match_all": {}})
        print(f"Total hits: {response['hits']['total']['value']}")
        for hit in response["hits"]["hits"]:
            print(f"Document: {json.dumps(hit['_source'], indent=2)}")

        # 4.2 搜索特定职位
        print("\nSearching for Python positions:")
        response = await es_client.search(
            index=index_name, query={"match": {"title": "Python"}}
        )
        print(f"Found {response['hits']['total']['value']} Python positions:")
        for hit in response["hits"]["hits"]:
            print(f"Document: {json.dumps(hit['_source'], indent=2)}")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise

    finally:
        await es_client.close()


if __name__ == "__main__":
    asyncio.run(test_es_connection())
