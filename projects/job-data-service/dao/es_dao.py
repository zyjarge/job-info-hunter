#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import Dict, Any, List, Union
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from datetime import datetime
import asyncio
from elasticsearch import ConnectionTimeout, ConnectionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElasticsearchDAO:
    """
    Elasticsearch 数据访问对象，处理职位数据的存储和检索
    """

    def __init__(self):
        # TODO: 从配置文件读取 ES 配置
        self.es_client = AsyncElasticsearch(
            hosts=["http://localhost:9200"],
            basic_auth=("elastic", "changeme"),
            verify_certs=False,
            request_timeout=30,  # 请求超时时间
            max_retries=3,  # 最大重试次数
            retry_on_timeout=True,  # 超时时重试
        )
        self.index_name = "job_posts"

    async def save_job_data(
        self, job_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """
        保存职位数据到 Elasticsearch，支持单条数据或数据列表

        Args:
            job_data: 单个职位数据字典或职位数据字典列表

        Returns:
            bool: 是否全部保存成功
        """
        try:
            # 将单个数据转换为列表，统一处理
            job_data_list = job_data if isinstance(job_data, list) else [job_data]
            logger.info(f"Processing {len(job_data_list)} job posts")

            # 准备批量操作的数据
            operations = []
            for job_item in job_data_list:
                job_id = job_item.get("job_id")
                site_id = job_item.get("site_id")

                if not job_id or not site_id:
                    logger.error(
                        f"Missing required fields. job_id: {job_id}, site_id: {site_id}"
                    )
                    continue

                doc_id = f"{site_id}_{job_id}"
                job_item["timestamp"] = datetime.utcnow().isoformat()

                operations.append(
                    {"_index": self.index_name, "_id": doc_id, "_source": job_item}
                )

            if not operations:
                logger.error("No valid job data to save")
                return False

            # 使用批量操作保存数据
            try:
                success, failed = await async_bulk(
                    self.es_client,
                    operations,
                    chunk_size=100,  # 每批处理的文档数
                    max_retries=3,  # 最大重试次数
                    raise_on_error=False,  # 不抛出错误，而是返回失败计数
                    raise_on_exception=False,  # 不抛出异常
                    refresh=True,  # 实时刷新
                )

                total = len(operations)
                logger.info(
                    f"Bulk save completed: {success} succeeded, {failed} failed out of {total}"
                )
                # 检查成功数量是否等于总数量
                return success == total

            except Exception as e:
                logger.error(f"Bulk save operation failed: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Error saving job data batch to ES: {str(e)}")
            return False

    async def close(self):
        """
        关闭 ES 客户端连接
        """
        await self.es_client.close()
