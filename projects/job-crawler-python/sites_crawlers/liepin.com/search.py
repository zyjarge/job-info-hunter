import asyncio
import os
from typing import List, Dict, Optional
import json
from datetime import datetime
import random
from login import LiepinLogin,logger

class LiepinSearchSelectors:
    """猎聘网搜索相关的选择器"""
    # 搜索相关
    SEARCH_INPUT = '.s5T1r input'  # 搜索输入框
    SEARCH_BUTTON = '.s5T1r .HUbbP'  # 搜索按钮
    
    # 列表页
    JOB_LIST_BOX = '.job-list-box'  # 职位列表容器
    JOB_ITEMS = 'div[class*="job-card-pc-container"]'  # 单个职位项
    JOB_LINK = '.job-detail-box a'  # 职位详情链接
    
    # 详情页
    DETAIL_JOB_TITLE = '.job-title'  # 职位名称
    DETAIL_SALARY = '.salary'  # 薪资
    DETAIL_COMPANY_NAME = '.company-info-container .company-card .name'  # 公司名称
    DETAIL_JOB_DESC = '.job-intro-container .paragraph dd[data-selector="job-intro-content"]'  # 职位描述
    DETAIL_COMPANY_DESC = '.paragraph-box .inner'  # 公司介绍
    DETAIL_LOCATION = '.job-properties span:first-child'  # 地域
    DETAIL_EXPERIENCE = '.job-properties span:nth-child(3)'  # 经验要求
    DETAIL_EDUCATION = '.job-properties span:nth-child(5)'  # 学历要求
    DETAIL_BENEFITS = '.job-apply-container-left .labels span'  # 福利标签
    # DETAIL_UPDATE_TIME = '.job-properties span:nth-child(5)'  # 更新时间
    
    # 公司信息
    DETAIL_LEGAL_REPRESENTATIVE = ''  # 法人代表
    DETAIL_ESTABLISH_DATE = '.register-info .label-box:first-child .text'  # 成立日期
    DETAIL_COMPANY_TYPE = '.company-other .label-box:first-child .text'  # 企业类型
    DETAIL_BUSINESS_STATUS = '.company-other .label-box:nth-child(3) .text'  # 人数规模
    DETAIL_REGISTERED_CAPITAL = '.register-info .label-box:nth-child(2) .text'  # 注册资本
    DETAIL_COMPANY_ADDRESS = '.company-other .label-box:nth-child(4) .text'  # 公司地址
    
    # HR信息相关
    HR_NAME = '.recruiter-info .name'  # HR姓名
    HR_COMPANY = '.recruiter-info .title'  # HR所在公司
    HR_AVATAR = '.recruiter-info .avatar img'  # HR头像URL

class LiepinSpiderConfig:
    """爬虫配置"""
    # 并发控制
    MAX_CONCURRENT_TABS = 5  # 最大同时打开的标签页数
    
    # 延时设置（秒）
    DELAY_MIN = 1  # 最小延时
    DELAY_MAX = 3  # 最大延时
    DELAY_AFTER_ERROR_MIN = 5  # 错误后最小延时
    DELAY_AFTER_ERROR_MAX = 10  # 错误后最大延时
    
    # 重试设置
    MAX_RETRIES = 3  # 最大重试次数

class LiepinSearcher:
    def __init__(self, login_instance: LiepinLogin, config: LiepinSpiderConfig = None):
        self.login = login_instance
        self.page = login_instance.page
        self.context = login_instance.context
        self.config = config or LiepinSpiderConfig()
        self.semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_TABS)
    
    async def search(self, keyword: str, location: str = None, limit: int = 10) -> List[Dict]:
        """执行搜索并返回结果"""
        try:
            logger.info(f"开始搜索任务 - 关键词: {keyword}, 地区: {location}, 数据上限: {limit}")
            
            # 输入搜索关键词
            await self._input_search_keyword(keyword)

            # 执行搜索
            await self._perform_search()
            
            # 获取搜索结果
            results = await self._get_search_results_by_limit(limit)
            
            # 保存结果
            self.save_results(results, keyword=keyword, location=location)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索过程出现错误: {e}", exc_info=True)
            return []
    
    async def _input_search_keyword(self, keyword: str):
        """输入搜索关键词"""
        await self.page.fill(LiepinSearchSelectors.SEARCH_INPUT, keyword)
        logger.info(f"输入搜索关键词: {keyword}")
    
    async def _set_location(self, location: str):
        """设置地区筛选"""
        pass
    
    async def _perform_search(self):
        """执行搜索操作"""
        try:
            # 点击搜索按钮
            await self.page.click(LiepinSearchSelectors.SEARCH_BUTTON)
            logger.info("点击搜索按钮")
            
            # 等待搜索结果加载
            await self.page.wait_for_selector('.job-list-box', timeout=10000)
            logger.info("搜索结果加载完成")
            
            # 随机延迟,避免操作过快
            delay = random.uniform(self.config.DELAY_MIN, self.config.DELAY_MAX)
            await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"执行搜索操作失败: {e}")
            # 发生错误时增加延迟
            error_delay = random.uniform(
                self.config.DELAY_AFTER_ERROR_MIN,
                self.config.DELAY_AFTER_ERROR_MAX
            )
            await asyncio.sleep(error_delay)
            raise e
        pass
    
    async def _get_search_results_by_limit(self, limit: int) -> List[Dict]:
        """按数量限制获取搜索结果"""
        logger.info(f"开始获取搜索结果,目标数量: {limit}")
        results = []
        page_num = 1
        
        try:
            while len(results) < limit:
                logger.debug(f"等待职位列表容器加载 - 第 {page_num} 页")
                await self.page.wait_for_selector(LiepinSearchSelectors.JOB_LIST_BOX)
                logger.debug("职位列表容器加载完成")
                
                remaining = limit - len(results)
                logger.debug(f"当前还需获取 {remaining} 条数据")
                
                page_jobs = await self._extract_page_jobs(remaining)
                if not page_jobs or len(page_jobs) == 0:
                    logger.info("当前页面没有更多职位信息，停止获取")
                    break
                
                logger.debug(f"开始并发获取 {len(page_jobs)} 个职位的详细信息")
                detailed_jobs = []
                tasks = []
                for job in page_jobs:
                    if 'url' in job:
                        logger.debug(f"创建获取详情任务: {job.get('title', 'Unknown')} - {job['url']}")
                        task = asyncio.create_task(self._fetch_job_detail_with_retry(job['url']))
                        tasks.append(task)
                
                if tasks:
                    logger.debug(f"开始执行 {len(tasks)} 个并发任务")
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in batch_results:
                        if isinstance(result, Exception):
                            # 可能的失败原因:
                            # 1. 网络连接超时
                            # 2. 页面加载失败
                            # 3. 反爬虫机制触发
                            # 4. 页面结构变化
                            # 5. IP被封禁
                            logger.error(f"获取职位详情失败: {result}")
                            logger.error("可能原因: 网络问题、反爬限制、页面结构变化等")
                            continue
                        if result:
                            logger.debug(f"成功获取职位详情: {result.get('job_info', {}).get('title', 'Unknown')}")
                            detailed_jobs.append(result)
                
                results.extend(detailed_jobs)
                logger.info(f"当前页处理完成，已获取 {len(results)}/{limit} 条结果")
                
                if len(results) < limit:
                    logger.debug("检查是否有下一页")
                    next_button = await self.page.query_selector('.ant-pagination-next:not(.ant-pagination-disabled)')
                    if not next_button:
                        logger.info("已到达最后一页，结束获取")
                        break
                    
                    logger.debug(f"准备翻到第 {page_num + 1} 页")
                    await next_button.click()
                    page_num += 1
                    logger.info(f"成功翻到第 {page_num} 页")
                    delay = random.uniform(2, 4)
                    logger.debug(f"随机延迟 {delay:.2f} 秒")
                    await asyncio.sleep(delay)
            
            logger.info(f"搜索结果获取完成，共获取 {len(results)} 条数据")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"获取搜索结果过程出错: {e}", exc_info=True)
            return results[:limit] if results else []

    async def _fetch_job_detail_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """带重试机制的详情页获取"""
        logger.debug(f"开始获取职位详情（最大重试 {max_retries} 次）: {url}")
        
        # 在最大重试次数范围内进行尝试
        for attempt in range(max_retries):
            try:
                # 使用信号量控制并发请求数
                async with self.semaphore:
                    # 记录当前是第几次尝试
                    logger.debug(f"第 {attempt + 1} 次尝试获取详情")
                    
                    # 调用实际的详情页获取方法
                    result = await self._fetch_job_detail(url)
                    
                    # 如果成功获取到结果
                    if result:
                        # 记录成功日志,从结果中提取职位标题(如果不存在则显示Unknown)
                        logger.debug(f"成功获取职位详情: {result.get('job_info', {}).get('title', 'Unknown')}")
                        return result
                        
                    # 如果result为空,记录警告日志
                    logger.warning(f"获取到空结果: {url}")
                    
            except Exception as e:
                # 捕获异常并记录警告日志
                logger.warning(f"第 {attempt + 1} 次获取详情失败: {url}, 错误: {e}")
                
                # 如果还有重试机会
                if attempt < max_retries - 1:
                    # 生成2-4秒的随机延迟
                    delay = random.uniform(2, 4)
                    logger.debug(f"等待 {delay:.2f} 秒后重试")
                    # 等待随机延迟时间
                    await asyncio.sleep(delay)
                continue
                
            # 所有重试都失败后,记录错误日志
            logger.error(f"职位详情获取失败，已达到最大重试次数: {url}")
            return None

    async def _fetch_job_detail(self, url: str) -> Dict:
        """获取职位详情信息"""
        try:
            page = await self.context.new_page()
            try:
                await page.goto(url, wait_until='networkidle')
                
                logger.debug("开始提取职位基本信息")
                job_info = {
                    'title': await self._get_text(page, LiepinSearchSelectors.DETAIL_JOB_TITLE),
                    'salary': await self._get_text(page, LiepinSearchSelectors.DETAIL_SALARY),
                    'company': await self._get_text(page, LiepinSearchSelectors.DETAIL_COMPANY_NAME),
                    'description': await self._get_text(page, LiepinSearchSelectors.DETAIL_JOB_DESC),
                    'location': await self._get_text(page, LiepinSearchSelectors.DETAIL_LOCATION),
                    'experience': await self._get_text(page, LiepinSearchSelectors.DETAIL_EXPERIENCE),
                    'education': await self._get_text(page, LiepinSearchSelectors.DETAIL_EDUCATION),
                    'benefits': await self._get_tags(page, LiepinSearchSelectors.DETAIL_BENEFITS),
                    'detail_url': url
                }
                logger.debug(f"职位基本信息提取完成: {job_info['title']}")
                
                logger.debug("开始提取公司信息")
                company_info = {
                    'company_name': job_info['company'],
                    'establish_date': await self._get_text(page, LiepinSearchSelectors.DETAIL_ESTABLISH_DATE),
                    'company_type': await self._get_text(page, LiepinSearchSelectors.DETAIL_COMPANY_TYPE),
                    'business_status': await self._get_text(page, LiepinSearchSelectors.DETAIL_BUSINESS_STATUS),
                    'registered_capital': await self._get_text(page, LiepinSearchSelectors.DETAIL_REGISTERED_CAPITAL),
                    'company_desc': await self._get_text(page, LiepinSearchSelectors.DETAIL_COMPANY_DESC),
                    'company_address': await self._get_text(page, LiepinSearchSelectors.DETAIL_COMPANY_ADDRESS)
                }
                logger.debug(f"公司信息提取完成: {company_info['company_name']}")
                
                # HR信息抽取
                logger.debug("开始提取HR信息")
                hr_info = {
                    'name': await self._get_text(page, LiepinSearchSelectors.HR_NAME),
                    'company': await self._get_text(page, LiepinSearchSelectors.HR_COMPANY),
                    'avatar': await self._get_image_url(page, LiepinSearchSelectors.HR_AVATAR)
                }
                logger.debug(f"HR信息提取完成: {hr_info['name']}")
                
                # 组装完整的详情信息
                detail_info = {
                    "job_info": job_info,
                    "company_info": company_info,
                    "hr_info": hr_info,
                    "update_time": datetime.now().strftime("%Y-%m-%d"),
                    "job_id": url.split('/')[-1].split('.')[0],
                    "site_id": "www.liepin.com"
                }
                
                return detail_info
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"获取职位详情失败: {url}, 错误: {e}", exc_info=True)
            return {}

    async def _get_text(self, page, selector: str) -> str:
        """获取元素文本内容"""
        try:
            element = await page.query_selector(selector)
            if element:
                return (await element.text_content()).strip()
            return ""
        except Exception as e:
            logger.debug(f"获取文本失败 - 选择器: {selector}, 错误: {e}")
            return ""

    async def _get_tags(self, page, selector: str) -> List[str]:
        """获取标签列表"""
        try:
            elements = await page.query_selector_all(selector)
            tags = []
            for element in elements:
                text = await element.text_content()
                tags.append(text.strip())
            return list(set(tags))  # 去重
        except Exception as e:
            logger.debug(f"获取标签失败 - 选择器: {selector}, 错误: {e}")
            return []
    
    async def _extract_page_jobs(self, remaining_limit: int = None) -> List[Dict]:
        """提取当前页面的所有职位信息"""
        logger.debug("开始提取当前页面职位信息")
        jobs = []
        try:
            # 获取所有职位卡片
            job_cards = await self.page.query_selector_all(LiepinSearchSelectors.JOB_ITEMS)
            
            # 限制提取数量
            if remaining_limit:
                job_cards = job_cards[:remaining_limit]
            
            for card in job_cards:
                job_info = {}
                # 只提取详情页URL
                title_link = await card.query_selector('a[data-nick="job-detail-job-info"]')
                # 提取职位标题
                title_text = await title_link.text_content()
                if title_text:
                    job_info['title'] = title_text.strip()
                if title_link:
                    job_info['url'] = await title_link.get_attribute('href')
                    if job_info['url'] and not job_info['url'].startswith('http'):
                        job_info['url'] = 'https://www.liepin.com' + job_info['url']
                    jobs.append(job_info)
            
            logger.debug(f"成功提取 {len(jobs)} 个职位信息")
            return jobs
            
        except Exception as e:
            logger.error(f"提取职位信息时出错: {e}", exc_info=True)
            return jobs
        pass
    
    def save_results(self, results: List[Dict], keyword: str = "", location: str = "", filename: str = None):
        """保存搜索结果到文件"""
        if not results:
            logger.warning("没有结果需要保存")
            return
        
        if not filename:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            keyword = keyword.replace('/', '_').replace('\\', '_').strip()
            location = location.replace('/', '_').replace('\\', '_').strip() if location else "全国"
            data_dir = os.path.join('data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            filename = os.path.join(data_dir, f"liepin_{keyword}_{location}_{current_time}.json")
        logger.info(f"开始保存搜索结果到文件: {filename}")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果保存成功，共 {len(results)} 条数据")
            
        except Exception as e:
            logger.error(f"保存结果时出错: {e}", exc_info=True)

    async def _get_image_url(self, page, selector: str) -> str:
        """获取图片URL"""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.get_attribute('src') or ""
            return ""
        except Exception as e:
            logger.debug(f"获取图片URL失败 - 选择器: {selector}, 错误: {e}")
            return ""

async def main():
    # 示例使用
    login = LiepinLogin()
    await login.init_browser()
    
    if await login.login():
        logger.info("登录成功，开始搜索")
        
        searcher = LiepinSearcher(login)
        results = await searcher.search(
            keyword="数据架构师",
            location="北京",
            limit=10
        )
        
        logger.info(f"搜索完成，共获取 {len(results)} 条结果")
    
    await login.close()

if __name__ == "__main__":
    asyncio.run(main()) 