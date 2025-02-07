from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.crawler import Crawler


def test_database_connection():
    """测试数据库连接"""
    db: Session = next(get_db())
    try:
        # 执行一个简单的查询
        result = db.execute("SELECT 1").scalar()
        assert result == 1
    finally:
        db.close()


def test_crawler_table():
    """测试爬虫表操作"""
    db: Session = next(get_db())
    try:
        # 创建测试数据
        crawler = Crawler(
            name="测试爬虫",
            description="用于测试的爬虫",
            homepage="https://example.com",
            enabled=False,
            config={
                "module": "test_module",
                "class": "TestCrawler",
                "login_module": "test_login",
                "login_class": "TestLogin",
                "site_id": "test_site",
            },
        )
        db.add(crawler)
        db.commit()

        # 查询测试数据
        db_crawler = db.query(Crawler).filter(Crawler.name == "测试爬虫").first()
        assert db_crawler is not None
        assert db_crawler.name == "测试爬虫"
        assert db_crawler.config["site_id"] == "test_site"

        # 清理测试数据
        db.delete(db_crawler)
        db.commit()
    finally:
        db.close()
