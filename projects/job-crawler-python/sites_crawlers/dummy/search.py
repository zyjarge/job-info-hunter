import asyncio
import json
from utils.logger import setup_logger
import os

logger = setup_logger("dummy_search")


class DummySearcher:
    def __init__(self, login_instance):
        self.login = login_instance
        self.mock_data_path = "data/liepin_数据仓库架构师_北京_20241225_160705.json"

    async def search(
        self, keyword: str = None, location: str = None, limit: int = None
    ):
        """模拟搜索操作，返回预设的数据"""
        try:
            logger.info(
                f"模拟搜索任务 - 关键词: {keyword}, 地区: {location}, 数据上限: {limit}"
            )

            # 读取模拟数据
            if os.path.exists(self.mock_data_path):
                with open(self.mock_data_path, "r", encoding="utf-8") as f:
                    mock_data = json.load(f)
                    logger.info(f"成功加载模拟数据，共 {len(mock_data)} 条记录")

                    # 如果设置了limit，则只返回指定数量的数据
                    if limit and isinstance(limit, int):
                        mock_data = mock_data[:limit]
                        logger.info(f"根据限制返回 {len(mock_data)} 条记录")

                    return mock_data
            else:
                logger.error(f"模拟数据文件不存在: {self.mock_data_path}")
                return []

        except Exception as e:
            logger.error(f"模拟搜索过程出现错误: {e}", exc_info=True)
            return []


async def main(keyword: str = "测试", location: str = "北京", limit: int = 10):
    """主函数，用于测试"""
    try:
        # 初始化登录实例
        login = DummyLogin()
        await login.init_browser()

        try:
            # 执行登录
            if await login.login():
                logger.info("登录成功，开始搜索")

                # 创建搜索实例
                searcher = DummySearcher(login)

                # 执行搜索
                results = await searcher.search(
                    keyword=keyword, location=location, limit=limit
                )

                logger.info(f"搜索完成，共获取 {len(results)} 条结果")
                return results
            else:
                logger.error("登录失败")
                return []

        finally:
            # 确保浏览器正确关闭
            await login.close()

    except Exception as e:
        logger.error(f"执行过程出现错误: {e}", exc_info=True)
        return []


if __name__ == "__main__":
    asyncio.run(main())
