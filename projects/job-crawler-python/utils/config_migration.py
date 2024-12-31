import json
import etcd3
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger("config_migration")


def migrate_config_to_etcd(
    config_file: str = "conf/config.json",
    etcd_host: str = "job_hunter_etcd",
    etcd_port: int = 2379,
):
    """将配置从 JSON 文件迁移到 etcd

    Args:
        config_file: 配置文件路径
        etcd_host: etcd 服务器地址
        etcd_port: etcd 服务器端口
    """
    try:
        # 连接到 etcd
        client = etcd3.client(host=etcd_host, port=etcd_port)

        # 读取配置文件
        config_path = Path(__file__).parent.parent / config_file
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # 迁移站点配置
        for site_id, site_config in config["site_mapping"].items():
            # 构建新的配置格式
            new_site_config = {
                "name": site_id,
                "description": f"Crawler for {site_id}",
                "homepage": site_id,
                "enabled": True,
                "config": site_config,  # 原有配置作为 config 字段的值
            }

            key = f"/crawlers/sites/{site_id}"
            value = json.dumps(new_site_config)
            client.put(key, value)
            logger.info(f"已迁移站点配置: {site_id}")

        # 迁移 MQ 配置
        client.put("/crawlers/mq", json.dumps(config["mq"]))
        logger.info("已迁移 MQ 配置")

        logger.info("配置迁移完成")

    except Exception as e:
        logger.error(f"配置迁移失败: {e}")
        raise


if __name__ == "__main__":
    migrate_config_to_etcd()
