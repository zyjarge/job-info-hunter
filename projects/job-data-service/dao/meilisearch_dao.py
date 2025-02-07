#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
from typing import Dict, Any, List, Union
from datetime import datetime
from meilisearch_python_async import Client
from meilisearch_python_async.errors import MeilisearchApiError
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeilisearchDAO:
    """
    Meilisearch 数据访问对象，处理职位数据的存储和检索
    """

    def __init__(self):
        # 从环境变量获取配置
        ms_host = os.getenv("MEILISEARCH_HOST", "http://localhost:7700")
        ms_key = os.getenv("MEILISEARCH_MASTER_KEY", "masterKey")

        self.client = Client(ms_host, ms_key)
        self.index_name = "job_posts"

    async def init_index(self):
        """
        初始化索引和设置
        """
        try:
            # 创建索引（如果不存在）
            index = await self.client.create_index(self.index_name, primary_key="id")
            logger.info("Created new index: job_posts")

            # 设置搜索字段的权重
            await index.update_searchable_attributes(
                [
                    "job_info.title",
                    "job_info.description",
                    "job_info.company",
                    "job_info.location",
                ]
            )

            # 设置过滤和排序字段
            await index.update_filterable_attributes(
                ["site_id", "job_info.company", "job_info.location", "timestamp"]
            )

            # 设置排序字段
            await index.update_sortable_attributes(["timestamp"])

            logger.info("Meilisearch index initialized successfully")
            return True
        except MeilisearchApiError as e:
            if "already exists" in str(e):
                # 如果索引已存在，获取它并更新设置
                try:
                    index = await self.client.get_index(self.index_name)

                    # 更新设置
                    await index.update_searchable_attributes(
                        [
                            "job_info.title",
                            "job_info.description",
                            "job_info.company",
                            "job_info.location",
                        ]
                    )
                    await index.update_filterable_attributes(
                        [
                            "site_id",
                            "job_info.company",
                            "job_info.location",
                            "timestamp",
                        ]
                    )
                    await index.update_sortable_attributes(["timestamp"])

                    logger.info("Updated existing index settings")
                    return True
                except Exception as inner_e:
                    logger.error(f"Error updating existing index: {str(inner_e)}")
                    return False
            else:
                logger.error(f"Error initializing Meilisearch index: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error initializing Meilisearch index: {str(e)}")
            return False

    async def save_job_data(
        self, job_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """
        保存职位数据到 Meilisearch，支持单条数据或数据列表

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
            documents = []
            for job_item in job_data_list:
                job_id = job_item.get("job_id")
                site_id = job_item.get("site_id")

                if not job_id or not site_id:
                    logger.error(
                        f"Missing required fields. job_id: {job_id}, site_id: {site_id}"
                    )
                    continue

                # 在 Meilisearch 中，我们需要一个唯一的 id 字段
                # 将点号替换为下划线以符合 Meilisearch 的 ID 规则
                doc_id = f"{site_id.replace('.', '_')}_{job_id}"
                job_item["id"] = doc_id
                job_item["timestamp"] = datetime.utcnow().isoformat()
                documents.append(job_item)

            if not documents:
                logger.error("No valid job data to save")
                return False

            # 使用批量操作保存数据
            try:
                index = await self.client.get_index(self.index_name)
                # 添加文档并等待操作完成
                await index.add_documents(documents)
                logger.info(f"Successfully saved {len(documents)} documents")
                return True

            except MeilisearchApiError as e:
                logger.error(f"Meilisearch operation failed: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Error saving job data batch to Meilisearch: {str(e)}")
            return False

    async def search_jobs(
        self,
        query: str = None,
        filters: Dict[str, Any] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        搜索职位数据

        Args:
            query: 搜索关键词
            filters: 过滤条件
            offset: 分页偏移
            limit: 每页数量

        Returns:
            Dict: 搜索结果
        """
        try:
            index = await self.client.get_index(self.index_name)

            # 构建过滤条件
            filter_str = []
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_str.append(f"{key} IN {json.dumps(value)}")
                    else:
                        filter_str.append(f"{key} = {json.dumps(value)}")

            # 执行搜索
            search_results = await index.search(
                query,
                {
                    "filter": " AND ".join(filter_str) if filter_str else None,
                    "offset": offset,
                    "limit": limit,
                    "sort": ["timestamp:desc"],
                },
            )

            return search_results
        except MeilisearchApiError as e:
            logger.error(f"Meilisearch search failed: {str(e)}")
            return {"hits": [], "total": 0, "error": str(e)}
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return {"hits": [], "total": 0, "error": str(e)}

    async def close(self):
        """
        关闭 Meilisearch 客户端连接
        """
        # Meilisearch 客户端不需要显式关闭
        pass
