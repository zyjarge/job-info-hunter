import asyncio
import logging
from typing import List, Dict, Optional
import json
import time
from login import BossLogin, setup_logger
from asyncio import Semaphore
import random
from datetime import datetime

logger = setup_logger()

class BossSearchSelectors:
    """搜索相关的选择器"""
    # 列表页
    JOB_LIST = '.job-list-box'  # 职位列表容器
    JOB_ITEMS = '.job-card-wrapper'  # 单个职位项
    JOB_LINK = 'a[href*="job_detail"]'  # 职位详情链接
    
    # 详情页选择器
    DETAIL_JOB_TITLE = '.job-title'  # 职位名称
    DETAIL_SALARY = '.salary'  # 薪资
    
    DETAIL_JOB_DESC = '.job-sec-text'  # 职位描述
    DETAIL_COMPANY_DESC = '.detail-section-item.company-info-box .job-sec-text'  # 公司介绍
    DETAIL_REQUIREMENTS = '.job-requirements'  # 职位要求
    
    # 新增详情页选择器
    DETAIL_JOB_STATUS = '.job-status'  # 职位状态容器
    DETAIL_HEADHUNTER_ICON = '.job-status .job-medium-icon'  # 猎头图标
    DETAIL_LOCATION = '.text-desc.text-city'  # 地域
    DETAIL_EXPERIENCE = '.text-desc.text-experiece'  # 经验要求
    DETAIL_EDUCATION = '.text-desc.text-degree'  # 学历要求
    DETAIL_BENEFITS = '.job-tags span'  # 福利标签
    DETAIL_UPDATE_TIME = '.gray'  # 更新时间
    
    # TODO: 需要您提供实际的选择器
    SEARCH_INPUT = '.ipt-search'  # 搜索输入框
    SEARCH_BUTTON = '.btn-search'  # 搜索按钮
    
    # 职位详情相关
    JOB_TITLE = ''  # 职位名称
    SALARY_RANGE = ''  # 薪资范围
    COMPANY_NAME = ''  # 公司名称
    LOCATION = ''  # 工作地点
    EXPERIENCE = ''  # 工作经验要求
    EDUCATION = ''  # 学历要求
    COMPANY_TYPE = ''  # 公司类型
    COMPANY_SIZE = ''  # 公司规模
    
    # 分页相关
    NEXT_PAGE = ''  # 下一页按钮
    PAGE_NUMBER = ''  # 当前页码
    
    # 公司详细信息选择器
    DETAIL_COMPANY_NAME = '.level-list .company-name'  # 公司名称
    DETAIL_LEGAL_REPRESENTATIVE = '.company-user'  # 法人代表
    DETAIL_ESTABLISH_DATE = '.res-time'  # 成立日期
    DETAIL_COMPANY_TYPE = '.company-type'  # 企业类型
    DETAIL_BUSINESS_STATUS = '.manage-state'  # 经营状态
    DETAIL_REGISTERED_CAPITAL = '.company-fund'  # 注册资金
    DETAIL_COMPANY_ADDRESS = '.location-address'  # 公司地址
    
    # HR信息相关
    HR_NAME = '.job-boss-info .name'  # HR姓名,包含完整的HTML内容
    HR_TITLE = '.job-boss-info .boss-info-attr'  # HR职位
    HR_ACTIVE = '.job-boss-info .boss-online-tag'  # HR在线状态
    HR_AVATAR = '.job-boss-info .detail-figure img'  # HR头像URL

class BossSpiderConfig:
    """爬虫配置"""
    # 并发控制
    MAX_CONCURRENT_TABS = 3  # 最大同时打开的标签页数
    
    # 延时设置（秒）
    DELAY_MIN = 1  # 最小延时
    DELAY_MAX = 3  # 最大延时
    DELAY_AFTER_ERROR_MIN = 5  # 错误后最小延时
    DELAY_AFTER_ERROR_MAX = 10  # 错误后最大延时
    
    # 重试设置
    MAX_RETRIES = 3  # 最大重试次数
    
    # 保存设置
    SAVE_INTERVAL = 10  # 每抓取多少条数据保存一次
    
    # 请求超时设置（毫秒）
    PAGE_TIMEOUT = 30000  # 页面加载超时
    ELEMENT_TIMEOUT = 5000  # 元素等待超时
    
    # 数据文件
    RESULT_FILE = "boss_jobs.json"  # 结果文件
    PROGRESS_FILE = "spider_progress.json"  # 进度文件

class BossSearcher:
    def __init__(self, login_instance: BossLogin, config: BossSpiderConfig = None):
        logger.info("初始化BossSearcher")
        self.login = login_instance
        self.page = login_instance.page
        self.context = login_instance.context
        self.search_results = []
        self.config = config or BossSpiderConfig()
        self.semaphore = Semaphore(5)  # 同时允许5个并发请求
        logger.debug(f"设置最大并发标签页数: 5")
        
    async def search(self, keyword: str, location: str = None, limit: int = 100) -> List[Dict]:
        """执行搜索并返回结果"""
        try:
            logger.info(f"开始搜索任务 - 关键词: {keyword}, 地区: {location}, 数据上限: {limit}")
            
            # 输入搜索关键词
            await self._input_search_keyword(keyword)
            
            # 如果指定了地区，设置地区筛选
            if location:
                logger.debug(f"设置地区筛选: {location}")
                await self._set_location(location)
            
            # 执行搜索
            await self._perform_search()
            
            # 获取搜索结果
            results = await self._get_search_results_by_limit(limit)
            
            # 保存结果时传入搜索参数
            self.save_results(results, keyword=keyword, location=location)
            
            logger.info(f"搜索完成 - 共获取 {len(results)} 条职位信息")
            return results
            
        except Exception as e:
            logger.error(f"搜索过程出现错误: {e}", exc_info=True)
            return []
    
    async def _input_search_keyword(self, keyword: str):
        """输入搜索关键词"""
        # TODO: 需要实际的选择器和操作步骤

        logger.debug(f"输入搜索关键词: {keyword}")
        try:
            # 等待搜索输入框出现
            logger.debug("等待搜索输入框出现")
            await self.page.wait_for_selector(BossSearchSelectors.SEARCH_INPUT)
            
            # 清空输入框
            await self.page.click(BossSearchSelectors.SEARCH_INPUT, click_count=3)
            await self.page.keyboard.press('Backspace')
            
            # 模拟人类输入行为
            logger.debug("开始输入关键词")
            for char in keyword:
                await self.page.type(BossSearchSelectors.SEARCH_INPUT, char)
                await self.random_delay(0.1, 0.3)
            
            # 等待一小段时间,模拟人类思考
            await self.random_delay(0.5, 1)
            
            logger.debug("关键词输入完成")
            
        except Exception as e:
            logger.error(f"输入搜索关键词失败: {e}")
            raise
        pass
    
    async def _set_location(self, location: str):
        """设置地区筛选"""
        # TODO: 需要实际的选择器和操作步骤
        logger.debug(f"设置搜索地区: {location}")
        pass
    
    async def _perform_search(self):
        """执行搜索操作"""
        try:
            logger.debug("等待搜索按钮出现")
            await self.page.wait_for_selector(BossSearchSelectors.SEARCH_BUTTON)
            
            # 模拟人类行为 - 随机移动鼠标到搜索按钮
            await self.page.hover(BossSearchSelectors.SEARCH_BUTTON)
            await self.random_delay(0.5, 1)
            
            # 点击搜索按钮
            await self.page.click(BossSearchSelectors.SEARCH_BUTTON)
            
            # 等待搜索结果加载
            await self.page.wait_for_selector(BossSearchSelectors.JOB_LIST)
            await self.random_delay()
            
            logger.debug("搜索操作执行完成")
            
        except Exception as e:
            logger.error(f"执行搜索操作失败: {e}")
            raise
        logger.debug("点击搜索按钮")
        pass
    
    async def _get_search_results_by_limit(self, limit: int) -> List[Dict]:
        """按数据条数限制获取搜索结果"""
        results = []
        current_page = 1
        
        logger.info(f"开始获取搜索结果，计划抓取 {limit} 条数据")
        
        while len(results) < limit:
            logger.info(f"正在抓取第 {current_page} 页 (当前已获取 {len(results)}/{limit} 条)")
            
            # 等待职位列表加载
            await self._wait_for_job_list()
            
            # 计算剩余需要抓取的数量
            remaining = limit - len(results)
            
            # 获取当前页的职位，传入剩余数量限制
            page_results = await self._extract_page_jobs(remaining)
            results.extend(page_results)
            
            logger.debug(f"第 {current_page} 页抓取完成，当前共有 {len(results)}/{limit} 条数据")
            
            # 如果已经达到目标数量，退出循环
            if len(results) >= limit:
                logger.info(f"已达到目标数量 {limit} 条，停止抓取")
                break
            
            # 如果当前页数据为空，说明没有更多数据了
            if not page_results:
                logger.info("没有更多数据，提前结束抓取")
                break
            
            # 尝试翻到下一页
            if not await self._goto_next_page():
                logger.info("没有更多页面，提前结束抓取")
                break
            
            current_page += 1
        
        logger.info(f"所有数据抓取完成，共获取 {len(results)} 条数据")
        return results[:limit]  # 确保不超过限制
    
    async def _wait_for_job_list(self):
        """等待职位列表加载完成"""
        # TODO: 需要实际的选择器和操作步骤
        logger.debug("等待职位列表加载")
        pass
    
    async def _extract_page_jobs(self, remaining_limit: int = None) -> List[Dict]:
        """提取当前页面的所有职位信息"""
        logger.debug("开始提取当前页面的职位信息")
        jobs = []
        
        # 获取所有职位卡片
        job_cards = await self.page.query_selector_all(BossSearchSelectors.JOB_ITEMS)
        total_cards = len(job_cards)
        logger.debug(f"找到 {total_cards} 个职位卡片")
        
        # 收集所有职位的URL和job_id，不限制数量
        job_urls = []
        for job_card in job_cards:
            try:
                job_url, job_id = await self._get_job_url(job_card)
                if job_url:
                    job_urls.append((job_url, job_id))
            except Exception as e:
                logger.error(f"获取职位URL时出错: {e}", exc_info=True)
        
        logger.info(f"收集到 {len(job_urls)} 个职位URL")
        
        # 并发抓取详情，但限制并发数
        async def process_job(url: str, job_id: str) -> Optional[Dict]:
            async with self.semaphore:
                result = await self._fetch_job_detail_with_retry(url, job_id)
                if result:
                    # 验证是否包含公司信息
                    company_info = result.get('company_info', {})
                    if company_info and company_info.get('company_name'):
                        logger.debug(f"成功获取职位信息: {result.get('job_info', {}).get('title')}")
                        return result
                    else:
                        logger.warning(f"职位缺少公司信息，已丢弃: {url}")
                        return None
                return None
        
        # 分批处理，直到达到目标数量或处理完所有URL
        processed_count = 0
        valid_jobs = []
        batch_size = 3  # 每批处理的任务数
        
        while processed_count < len(job_urls) and (remaining_limit is None or len(valid_jobs) < remaining_limit):
            # 计算本批次需要处理的数量
            remaining_needed = remaining_limit - len(valid_jobs) if remaining_limit else float('inf')
            current_batch_size = min(batch_size, len(job_urls) - processed_count, remaining_needed)
            
            if current_batch_size <= 0:
                break
            
            # 获取当前批次的URL
            current_batch = job_urls[processed_count:processed_count + current_batch_size]
            logger.debug(f"处理第 {processed_count//batch_size + 1} 批，"
                        f"当前有效职位数: {len(valid_jobs)}/{remaining_limit if remaining_limit else '不限'}")
            
            # 创建并执行当前批次的任务
            batch_tasks = [process_job(url, job_id) for url, job_id in current_batch]
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # 处理结果
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"抓取职位详情失败: {result}")
                    continue
                if result:  # 只添加有效的结果（包含公司信息的职位）
                    valid_jobs.append(result)
                    logger.debug(f"添加有效职位，当前数量: {len(valid_jobs)}")
            
            processed_count += len(current_batch)
            
            # 批次间延时
            await asyncio.sleep(random.uniform(2, 4))
            
            # 如果已经达到目标数量，退出循环
            if remaining_limit and len(valid_jobs) >= remaining_limit:
                logger.info(f"已达到目标数量 {remaining_limit}，停止获取")
                break
        
        logger.info(f"职位处理完成，成功获取 {len(valid_jobs)} 个有效职位信息")
        return valid_jobs[:remaining_limit] if remaining_limit else valid_jobs
    
    async def _get_job_url(self, job_card) -> tuple[str, str]:
        """获取职位详情页URL和job_id
        Returns:
            tuple: (url, job_id)
        """
        try:
            logger.debug("尝试获取职位详情页URL")
            # 修改选择器，确保能准确定位到链接元素
            link_element = await job_card.query_selector(BossSearchSelectors.JOB_LINK)
            if not link_element:
                logger.warning(f"未找到职位链接元素 (选择器: {BossSearchSelectors.JOB_LINK})")
                return "", ""
            
            href = await link_element.get_attribute('href')
            if not href:
                logger.warning("职位链接href属性为空")
                return "", ""
            
            # 提取job_id
            job_id = ""
            if "/job_detail/" in href:
                job_id = href.split("/job_detail/")[1].split(".html")[0]
                logger.debug(f"提取到job_id: {job_id}")
            
            # 如果是相对URL，转换为绝对URL
            if href.startswith('/'):
                href = f"https://www.zhipin.com{href}"
            
            logger.debug(f"成功获取职位URL: {href}")
            return href, job_id
        
        except Exception as e:
            logger.error(f"获取职位URL时出错: {e}", exc_info=True)
            return "", ""
    
    async def _fetch_job_detail(self, url: str) -> Dict:
        """获取职位详情信息"""
        try:
            page = await self.context.new_page()
            try:
                await page.goto(url, wait_until='networkidle')
                
                # 首先获取职位基本信息
                job_info = {
                    'title': await self._get_text(page, BossSearchSelectors.DETAIL_JOB_TITLE),
                    'salary': await self._get_text(page, BossSearchSelectors.DETAIL_SALARY),
                    'description': await self._get_text(page, BossSearchSelectors.DETAIL_JOB_DESC),
                    'requirements': await self._get_text(page, BossSearchSelectors.DETAIL_REQUIREMENTS),
                    'location': await self._get_text(page, BossSearchSelectors.DETAIL_LOCATION),
                    'experience': await self._get_text(page, BossSearchSelectors.DETAIL_EXPERIENCE),
                    'education': await self._get_text(page, BossSearchSelectors.DETAIL_EDUCATION),
                    'benefits': await self._get_tags(page, BossSearchSelectors.DETAIL_BENEFITS),
                    'is_headhunter': await self._check_is_headhunter(page),
                    'detail_url': url
                }
                
                # 验证职位信息的基本完整性
                if not job_info['title']:
                    logger.warning(f"未能获取到职位标题，跳过: {url}")
                    return {}
                
                # 尝试获取公司信息，如果失败则使用空字典
                try:
                    company_info = await self._get_company_info(page)
                    # 如果获取到公司名称，则更新job_info中的company字段
                    if company_info and company_info.get('company_name'):
                        job_info['company'] = company_info['company_name']
                    else:
                        job_info['company'] = ''
                        company_info = {
                            'company_name': '',
                            'legal_representative': '',
                            'establish_date': '',
                            'company_type': '',
                            'business_status': '',
                            'registered_capital': '',
                            'company_desc': '',
                            'company_address': ''
                        }
                        logger.warning(f"未能获取到公司信息: {url}")
                except Exception as e:
                    logger.error(f"获取公司信息失败，使用空值: {e}")
                    job_info['company'] = ''
                    company_info = {
                        'company_name': '',
                        'legal_representative': '',
                        'establish_date': '',
                        'company_type': '',
                        'business_status': '',
                        'registered_capital': '',
                        'company_desc': '',
                        'company_address': ''
                    }
                
                # 添加HR信息抽取
                logger.debug("开始提取HR信息")
                hr_info = {
                    'name': (await self._get_text(page, BossSearchSelectors.HR_NAME)).split('\n')[0],
                    'title': (await self._get_text(page, BossSearchSelectors.HR_TITLE)).split('\n·\n')[-1],
                    'active': await self._get_text(page, BossSearchSelectors.HR_ACTIVE),
                    'avatar': await self._get_image_url(page, BossSearchSelectors.HR_AVATAR)
                }
                logger.debug(f"HR信息提取完成: {hr_info['name']}")
                
                detail_info = {
                    "job_info": job_info,
                    "company_info": company_info,
                    "hr_info": hr_info,  # 添加HR信息
                    "update_time": (await self._get_text(page, BossSearchSelectors.DETAIL_UPDATE_TIME))
                        .replace('更新于：', '').strip(),
                    "job_id": "",
                    "site_id": "www.zhipin.com"
                }
                
                return detail_info
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"获取职位详情失败: {url}, 错误: {e}", exc_info=True)
            return {}
    
    async def _extract_job_detail(self, job_element) -> Dict:
        """提取单个职位的详细信息"""
        # TODO: 需要实际的选择器和操作步骤
        job_info = {}
        return job_info
    
    async def _goto_next_page(self) -> bool:
        """跳转到下一页"""
        # TODO: 需要实际的选择器和操作步骤
        logger.debug("尝试跳转到下一页")
        return False
    
    def save_results(self, results: List[Dict], keyword: str = "", location: str = "", filename: str = None):
        """
        保存搜索结果到文件
        Args:
            results: 搜索结果列表
            keyword: 搜索关键词
            location: 搜索地区
            filename: 自定义文件名（可选）
        """
        if not results:
            logger.warning("没有结果需要保存")
            return
        
        # 如果没有提供文件名，则根据搜索参数生成
        if not filename:
            # 获取当前时间
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 清理关键词和地区中的特殊字符
            keyword = keyword.replace('/', '_').replace('\\', '_').strip()
            location = location.replace('/', '_').replace('\\', '_').strip() if location else "全国"
            # 生成文件名
            filename = f"zhipin_{keyword}_{location}_{current_time}.json"
        
        logger.info(f"开始保存搜索结果到文件: {filename}")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果保存成功，共 {len(results)} 条数据")
            
        except Exception as e:
            logger.error(f"保存结果时出错: {e}", exc_info=True)
    
    async def _fetch_job_detail_with_retry(self, url: str, job_id: str, max_retries: int = 3) -> Optional[Dict]:
        """带重试机制的详情页获取"""
        logger.debug(f"开始获取职位详情（最大重试次数：{max_retries}）: {url}")
        
        for attempt in range(max_retries):
            try:
                async with self.semaphore:  # 使用信号量控制并发
                    logger.debug(f"第 {attempt + 1} 次尝试获取详情")
                    result = await self._fetch_job_detail(url)
                    if result:
                        result['job_id'] = job_id
                    logger.debug("详情获取成功")
                    return result
            except Exception as e:
                logger.warning(f"第 {attempt + 1} 次获取详情失败: {url}, 错误: {e}")
                if attempt < max_retries - 1:
                    delay_time = random.uniform(
                        self.config.DELAY_AFTER_ERROR_MIN,
                        self.config.DELAY_AFTER_ERROR_MAX
                    )
                    logger.debug(f"等待 {delay_time:.2f} 秒后重试")
                    await asyncio.sleep(delay_time)
                continue
        
        logger.error(f"职位详情获取失败，已达到最大重试次数: {url}")
        return None
    
    async def _get_text(self, element, selector: str) -> str:
        """从元素中提取文本"""
        try:
            el = await element.query_selector(selector)
            if el:
                # return (await el.text_content()).strip()
                return (await el.inner_text()).strip()
            return ""
        except Exception as e:
            logger.debug(f"提取文本失败 - 选择器: {selector}, 错误: {e}")
            return ""
    
    async def _get_tags(self, element, selector: str) -> List[str]:
        """提取标签列表，并去重"""
        try:
            tags_el = await element.query_selector_all(selector)
            # 使用集合去重
            tags = set()
            for tag in tags_el:
                text = await tag.text_content()
                tags.add(text.strip())
            # 转回列表并排序，确保输出顺序一致
            return sorted(list(tags))
        except Exception as e:
            logger.debug(f"提取标签失败 - 选择器: {selector}, 错误: {e}")
            return []
    
    async def _get_attribute(self, element, selector: str, attr: str) -> str:
        """获取元素属性值"""
        try:
            el = await element.query_selector(selector)
            if el:
                return await el.get_attribute(attr) or ""
            return ""
        except Exception as e:
            logger.debug(f"获取属性失败 - 选择器: {selector}, 属性: {attr}, 错误: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        # 移除多余空白字符
        text = " ".join(text.split())
        # 可以添加其他文本清理规则
        return text
    
    async def _safe_operation(self, operation, error_msg: str, default=None):
        """安全执行操作"""
        try:
            return await operation
        except Exception as e:
            logger.debug(f"{error_msg}: {e}")
            return default
            
    async def random_delay(self, min_seconds=1, max_seconds=3):
        """随机延时"""
        delay_time = random.uniform(min_seconds, max_seconds)
        logger.debug(f"随机延时 {delay_time:.2f} 秒")
        await asyncio.sleep(delay_time)
    
    async def _check_is_headhunter(self, page) -> bool:
        """检查是否是猎头职位"""
        try:
            # 检查是否存在猎头图标
            headhunter_icon = await page.query_selector(BossSearchSelectors.DETAIL_HEADHUNTER_ICON)
            return headhunter_icon is not None
        except Exception as e:
            logger.debug(f"检查猎头职位状态失败: {e}")
            return False
    
    async def _get_company_info(self, page) -> Dict:
        """提取公司详细信息"""
        try:
            # 等待公司信息加载完成，但设置较短的超时时间
            try:
                await page.wait_for_selector(BossSearchSelectors.DETAIL_COMPANY_NAME, timeout=3000)
            except Exception:
                logger.warning("等待公司信息超时")
                return {}
            
            # 获取并清理各项公司信息
            company_name = await self._get_text(page, BossSearchSelectors.DETAIL_COMPANY_NAME)
            company_name = company_name.replace('公司名称', '').strip()
            
            # 如果没有公司名称，返回空字典
            if not company_name:
                return {}
            
            legal_representative = await self._get_text(page, BossSearchSelectors.DETAIL_LEGAL_REPRESENTATIVE)
            legal_representative = legal_representative.replace('法定代表人', '').strip()
            
            establish_date = await self._get_text(page, BossSearchSelectors.DETAIL_ESTABLISH_DATE)
            establish_date = establish_date.replace('成立日期', '').strip()
            
            company_type = await self._get_text(page, BossSearchSelectors.DETAIL_COMPANY_TYPE)
            company_type = company_type.replace('企业类型', '').strip()
            
            business_status = await self._get_text(page, BossSearchSelectors.DETAIL_BUSINESS_STATUS)
            business_status = business_status.replace('经营状态', '').strip()
            
            registered_capital = await self._get_text(page, BossSearchSelectors.DETAIL_REGISTERED_CAPITAL)
            registered_capital = registered_capital.replace('注册资金', '').strip()
            
            company_desc = await self._get_text(page, BossSearchSelectors.DETAIL_COMPANY_DESC)
            company_address = await self._get_text(page, BossSearchSelectors.DETAIL_COMPANY_ADDRESS)
            
            return {
                'company_name': company_name,
                'legal_representative': legal_representative,
                'establish_date': establish_date,
                'company_type': company_type,
                'business_status': business_status,
                'registered_capital': registered_capital,
                'company_desc': company_desc,
                'company_address': company_address
            }
        except Exception as e:
            logger.error(f"获取公司信息失败: {e}", exc_info=True)
            return {}
    
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
    boss_login = BossLogin()
    await boss_login.init_browser()
    
    if await boss_login.login():
        logger.info("登录成功，开始搜索")
        
        searcher = BossSearcher(boss_login)
        results = await searcher.search(
            keyword="数据产品经理",
            location="北京",
            limit=3  # 限制最多抓取100条数据
        )
        
        searcher.save_results(results)
        logger.info(f"搜索完成，共获取 {len(results)} 条结果")
    
    await boss_login.close()

if __name__ == "__main__":
    asyncio.run(main()) 