import etcd3
import json
from typing import Dict, Any, Optional, Callable
from utils.logger import setup_logger
import asyncio
from functools import partial

logger = setup_logger("config_manager")


class ConfigManager:
    def __init__(self, host: str = "job_hunter_etcd", port: int = 2379):
        """初始化配置管理器"""
        self.client = etcd3.client(host=host, port=port)
        self.sites_prefix = "/crawlers/sites/"
        self._site_mapping: Dict[str, Any] = {}
        self._watch_id: Optional[int] = None
        self._watch_thread = None
        self._config_update_callback: Optional[Callable] = None
        self._main_loop = None  # 添加主事件循环引用

    async def start(self, config_update_callback: Callable = None):
        """启动配置管理器"""
        self._config_update_callback = config_update_callback
        self._main_loop = asyncio.get_running_loop()  # 保存主事件循环
        # 初始加载配置
        self._site_mapping = await self.get_site_mapping()
        # 启动配置监听
        await self.start_watch()
        logger.info("配置管理器启动完成")

    async def stop(self):
        """停止配置管理器"""
        if self._watch_id:
            self.client.cancel_watch(self._watch_id)
            self._watch_id = None
        logger.info("配置管理器已停止")

    def _watch_callback(self, response):
        """处理配置变更事件"""
        try:
            # response 包含多个事件
            for event in response.events:
                # 提取变更的键和值
                key = event.key.decode("utf-8")
                site_id = key.replace(self.sites_prefix, "")

                # 根据事件类型处理
                if hasattr(event, "delete"):  # 删除事件
                    if site_id in self._site_mapping:
                        del self._site_mapping[site_id]
                        logger.info(f"站点配置已删除: {site_id}")
                elif hasattr(event, "value"):  # 更新或新增事件
                    try:
                        if event.value:  # 确保 value 不为空
                            site_info = json.loads(event.value.decode("utf-8"))
                            if site_info.get("enabled", False):
                                site_config = site_info.get("config", {})
                                if site_config:
                                    self._site_mapping[site_id] = site_config
                                    logger.info(f"站点配置已更新: {site_id}")
                            else:
                                # 如果站点被禁用，从映射中删除
                                self._site_mapping.pop(site_id, None)
                                logger.info(f"站点已禁用: {site_id}")
                    except json.JSONDecodeError as e:
                        logger.error(f"解析配置 JSON 失败: {e}")
                        return

                # 触发回调
                if self._config_update_callback and self._main_loop:
                    # 使用保存的主事件循环来调度回调
                    self._main_loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(
                            self._config_update_callback(self._site_mapping)
                        )
                    )

        except Exception as e:
            logger.error(f"处理配置变更事件失败: {e}", exc_info=True)

    async def start_watch(self):
        """启动配置监听"""
        try:
            # 使用 watch_prefix 监听指定前缀的所有键
            self._watch_id = self.client.add_watch_prefix_callback(
                self.sites_prefix, self._watch_callback
            )
            logger.info(f"开始监听配置变更: {self.sites_prefix}")
        except Exception as e:
            logger.error(f"启动配置监听失败: {e}")
            raise

    @property
    def site_mapping(self) -> Dict[str, Any]:
        """获取当前的站点映射"""
        return self._site_mapping.copy()

    async def get_site_mapping(self) -> Dict[str, Any]:
        """从 etcd 获取所有站点配置"""
        try:
            site_mapping = {}
            # 获取 /crawlers/sites/ 下的所有键值对
            items = self.client.get_prefix(self.sites_prefix)

            for item in items:
                value, meta = item
                if value:
                    # 从键名中提取 site_id
                    site_id = meta.key.decode("utf-8").replace(self.sites_prefix, "")
                    try:
                        # 解析完整的站点信息
                        site_info = json.loads(value.decode("utf-8"))

                        # 检查站点是否启用
                        if not site_info.get("enabled", False):
                            logger.info(f"站点 {site_id} 未启用，跳过")
                            continue

                        # 获取配置信息
                        site_config = site_info.get("config", {})
                        if not site_config:
                            logger.warning(f"站点 {site_id} 缺少配置信息")
                            continue

                        # 将配置信息添加到映射中
                        site_mapping[site_id] = site_config
                        logger.debug(f"加载站点配置: {site_id}")

                    except json.JSONDecodeError as e:
                        logger.error(f"解析站点配置失败 {site_id}: {e}")
                        continue
                    except KeyError as e:
                        logger.error(f"站点配置格式错误 {site_id}: {e}")
                        continue

            logger.info(f"成功加载 {len(site_mapping)} 个有效站点配置")
            return site_mapping

        except Exception as e:
            logger.error(f"从 etcd 获取配置失败: {e}")
            raise

    async def get_mq_config(self) -> Dict[str, Any]:
        """获取 MQ 配置"""
        try:
            value, _ = self.client.get("/crawlers/mq")
            if value:
                return json.loads(value.decode("utf-8"))
            raise ValueError("MQ 配置不存在")
        except Exception as e:
            logger.error(f"从 etcd 获取 MQ 配置失败: {e}")
            raise
