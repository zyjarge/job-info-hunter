from typing import List, Optional
import json
import etcd3
from sqlalchemy.orm import Session
from app.models.crawler import Crawler
from app.schemas.crawler import CrawlerCreate, CrawlerUpdate
from app.core.config import settings

# 创建 etcd 客户端
etcd_client = etcd3.client(host=settings.ETCD_HOST, port=settings.ETCD_PORT)


def sync_to_etcd(crawler_data: dict) -> None:
    """将爬虫数据同步到 etcd"""
    site_id = crawler_data["config"]["site_id"]
    key = f"/crawlers/sites/{site_id}"
    # 将数据转换为 JSON 字符串
    value = json.dumps(crawler_data, ensure_ascii=False)
    etcd_client.put(key, value)


def get_crawler(db: Session, crawler_id: int) -> Optional[Crawler]:
    return db.query(Crawler).filter(Crawler.id == crawler_id).first()


def get_crawler_by_name(db: Session, name: str) -> Optional[Crawler]:
    return db.query(Crawler).filter(Crawler.name == name).first()


def get_crawlers(db: Session, skip: int = 0, limit: int = 100) -> List[Crawler]:
    return db.query(Crawler).offset(skip).limit(limit).all()


def create_crawler(db: Session, crawler: CrawlerCreate) -> Crawler:
    config_data = crawler.config.dict(by_alias=True)
    if "class_" in config_data:
        config_data["class"] = config_data.pop("class_")

    db_crawler = Crawler(
        name=crawler.name,
        description=crawler.description,
        homepage=crawler.homepage,
        enabled=crawler.enabled,
        config=config_data,
    )
    db.add(db_crawler)
    db.commit()
    db.refresh(db_crawler)

    # 同步到 etcd
    crawler_data = {
        "name": db_crawler.name,
        "description": db_crawler.description,
        "homepage": db_crawler.homepage,
        "enabled": db_crawler.enabled,
        "config": db_crawler.config,
    }
    sync_to_etcd(crawler_data)

    return db_crawler


def update_crawler(
    db: Session, crawler_id: int, crawler: CrawlerUpdate
) -> Optional[Crawler]:
    db_crawler = get_crawler(db, crawler_id)
    if not db_crawler:
        return None

    update_data = crawler.dict(exclude_unset=True)
    if "config" in update_data:
        config_data = update_data["config"]
        if "class_" in config_data:
            config_data["class"] = config_data.pop("class_")
        update_data["config"] = config_data

    for field, value in update_data.items():
        setattr(db_crawler, field, value)

    db.commit()
    db.refresh(db_crawler)
    return db_crawler


def delete_crawler(db: Session, crawler_id: int) -> bool:
    db_crawler = get_crawler(db, crawler_id)
    if not db_crawler:
        return False

    # 从 etcd 中删除
    site_id = db_crawler.config["site_id"]
    key = f"/crawlers/sites/{site_id}"
    etcd_client.delete(key)

    # 从数据库中删除
    db.delete(db_crawler)
    db.commit()
    return True
