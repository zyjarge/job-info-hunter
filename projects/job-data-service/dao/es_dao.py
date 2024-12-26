#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, Any
from elasticsearch import AsyncElasticsearch
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElasticsearchDAO:
    """
    Elasticsearch 数据访问对象，处理职位数据的存储和检索
    """

    def __init__(self):
        # TODO: 从配置文件读取 ES 配置
        self.es_client = AsyncElasticsearch(
            hosts=["localhost:9200"],
            basic_auth=("elastic", "changeme"),  # 这里应该从配置文件读取
        )
        self.index_name = "job_posts"

    async def save_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        保存职位数据到 Elasticsearch

        Args:
            job_data: 职位数据字典

        Returns:
            bool: 是否保存成功
        """
        try:
            # 添加时间戳
            job_data["timestamp"] = datetime.utcnow().isoformat()

            # 生成文档ID (使用职位ID或其他唯一标识)
            doc_id = job_data.get("job_id") or job_data.get("id")

            if not doc_id:
                logger.error("No job_id found in job data")
                return False

            # 保存到 ES
            response = await self.es_client.index(
                index=self.index_name,
                id=doc_id,
                document=job_data,
                refresh=True,  # 实时刷新，生产环境可以设置为 False 以提高性能
            )

            logger.info(f"Successfully saved job data to ES with id: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving job data to ES: {str(e)}")
            return False

    async def close(self):
        """
        关闭 ES 客户端连接
        """
        await self.es_client.close()
