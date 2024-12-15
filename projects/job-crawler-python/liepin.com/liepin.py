from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import json
import os
import logging
from datetime import datetime
import random

# 全局配置
HEADLESS_MODE = True
COOKIES_FILE = "liepin_cookies.json"
SEARCH_KEYWORD = "北京 数据分析 数据挖掘"

# 配置日志
def setup_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    log_filename = f'logs/liepin_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)

logger = setup_logger()

def save_cookies(cookies):
    """保存 cookies 到文件"""
    try:
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"Cookies 已保存到文件: {COOKIES_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存 cookies 时发生错误：{str(e)}")
        return False

def load_cookies():
    """从文件加载 cookies"""
    try:
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"读取 cookies 时发生错误：{str(e)}")
        return None

def get_job_detail(page, job_link, search_url):
    """获取职位详细信息"""
    try:
        page.set_default_timeout(60000)
        
        # 访问职位详情页
        page.goto(job_link, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)
        
        # 随机延迟
        delay = random.uniform(3, 5)
        page.wait_for_timeout(int(delay * 1000))
        
        # 等待职位描述加载
        page.wait_for_selector(".job-description", timeout=60000)
        
        # 提取职位描述
        job_desc = page.query_selector(".job-description")
        job_description = job_desc.inner_text() if job_desc else ""
        
        # 返回搜索结果页
        page.goto(search_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)
        
        return {"job_description": job_description}
    except Exception as e:
        logger.error(f"获取职位详情时发生错误：{str(e)}")
        try:
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("networkidle")
        except:
            logger.error("返回搜索页面失败")
        return None

def search_jobs(page, keyword=SEARCH_KEYWORD):
    """搜索职位并提取信息"""
    try:
        # 点击搜索框
        search_input = page.wait_for_selector('input[placeholder*="搜索职位"]')
        search_input.click()
        search_input.fill(keyword)
        
        # 点击搜索按钮
        search_button = page.wait_for_selector('button[data-nick="search-btn"]')
        search_button.click()
        
        # 等待搜索结果加载
        page.wait_for_load_state("networkidle")
        logger.info("搜索结果加载完成")
        
        # 保存搜索结果页面URL
        search_url = page.url
        
        # 等待职位列表出现
        page.wait_for_selector(".job-list-item")
        
        # 存储所有职位信息
        job_details = []
        
        # 获取职位列表
        job_items = page.query_selector_all(".job-list-item")[:10]
        total_jobs = len(job_items)
        logger.info(f"找到 {total_jobs} 个职位")
        
        for index, item in enumerate(job_items, 1):
            try:
                # 提取职位基本信息
                job_info = {
                    "index": index,
                    "job_name": item.query_selector(".job-title")?.inner_text() or "N/A",
                    "company_name": item.query_selector(".company-name")?.inner_text() or "N/A",
                    "salary": item.query_selector(".salary")?.inner_text() or "N/A",
                    "job_area": item.query_selector(".job-area")?.inner_text() or "N/A"
                }
                
                # 获取职位链接
                job_link = item.query_selector("a.job-title")?.get_attribute("href")
                if job_link:
                    job_info["job_link"] = job_link
                    # 获取详细描述
                    detail_info = get_job_detail(page, job_link, search_url)
                    if detail_info:
                        job_info.update(detail_info)
                
                job_details.append(job_info)
                logger.info(f"已提取第 {index} 个职位信息")
                
                # 随机延迟
                delay = random.uniform(2, 4)
                page.wait_for_timeout(int(delay * 1000))
                
            except Exception as e:
                logger.error(f"处理第 {index} 个职位时发生错误：{str(e)}")
                continue
        
        # 保存职位信息
        if job_details:
            save_job_details(job_details)
        
    except Exception as e:
        logger.error(f"搜索职位时发生错误：{str(e)}")

def save_job_details(job_details):
    """保存职位信息到文件"""
    try:
        filename = f'liepin_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(job_details, f, ensure_ascii=False, indent=2)
        logger.info(f"职位信息已保存到文件: {filename}")
    except Exception as e:
        logger.error(f"保存职位信息时发生错误：{str(e)}")

def create_browser_context(playwright):
    """创建浏览器上下文"""
    browser = playwright.chromium.launch(
        headless=HEADLESS_MODE,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--start-maximized",
        ],
    )
    
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        java_script_enabled=True,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    
    # 注入反检测脚本
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context

def login_liepin():
    """登录猎聘网"""
    try:
        with sync_playwright() as p:
            browser, context = create_browser_context(p)
            page = context.new_page()
            
            try:
                # 访问首页
                page.goto("https://www.liepin.com/")
                page.wait_for_load_state("networkidle")
                
                # 点击登录按钮
                login_button = page.wait_for_selector("text=登录")
                login_button.click()
                
                logger.info("请扫描二维码登录...")
                
                # 等待登录成功
                page.wait_for_selector(".user-nav", timeout=120000)
                logger.info("登录成功！")
                
                # 开始搜索
                search_jobs(page)
                
                # 保存cookies
                cookies = page.context.cookies()
                save_cookies(cookies)
                
                return cookies
                
            except Exception as e:
                logger.error(f"登录过程中发生错误：{str(e)}")
                return None
            finally:
                browser.close()
    except Exception as e:
        logger.error(f"创建浏览器时发生错误：{str(e)}")
        return None

def reuse_login_session(cookies=None):
    """使用已保存的登录状态"""
    if cookies is None:
        cookies = load_cookies()
        if cookies is None:
            return False
            
    try:
        with sync_playwright() as p:
            browser, context = create_browser_context(p)
            context.add_cookies(cookies)
            page = context.new_page()
            
            page.goto("https://www.liepin.com/")
            page.wait_for_load_state("networkidle")
            
            try:
                page.wait_for_selector(".user-nav", timeout=10000)
                logger.info("使用已保存的登录状态成功！")
                
                search_jobs(page)
                return True
            except:
                logger.warning("登录状态已失效")
                return False
            finally:
                browser.close()
    except Exception as e:
        logger.error(f"使用登录状态时发生错误：{str(e)}")
        return False

if __name__ == "__main__":
    # 首先尝试使用保存的 cookies
    saved_cookies = load_cookies()
    if saved_cookies and reuse_login_session(saved_cookies):
        logger.info("使用已保存的登录状态成功")
    else:
        logger.info("需要重新登录...")
        cookies = login_liepin()
        if cookies:
            time.sleep(10)
            reuse_login_session(cookies)
