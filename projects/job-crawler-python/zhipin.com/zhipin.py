from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import json
import os
import logging
from datetime import datetime
import random

# 全局配置
HEADLESS_MODE = True  # 设置为 True 使用无界面模式，False 显示浏览器界面
SEARCH_KEYWORD = "海淀区 数据挖掘 数据分析 数据仓库 数据治理"  # 搜索关键词
COOKIES_FILE = "zhipin_cookies.json"


# 配置日志
def setup_logger():
    # 创建logs目录（如果不存在）
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 设置日志文件名（包含时间戳）
    log_filename = f'logs/zhipin_{datetime.now().strftime("%Y%m%d")}.log'

    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),  # 同时输出到控制台
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
        # 设置更长的超时时间
        page.set_default_timeout(60000)  # 设置60秒全局超时

        # 访问职位详情页
        page.goto(job_link, timeout=60000)

        # 等待页面加载完成，增加超时时间
        page.wait_for_load_state("networkidle", timeout=60000)

        # 添加随机延迟，避免触发反爬
        delay = random.uniform(3, 5)
        page.wait_for_timeout(int(delay * 1000))

        # 等待详情内容加载
        page.wait_for_selector(".job-detail", timeout=60000)

        # 仅提取职位描述
        job_desc = page.query_selector(".job-sec-text")
        job_description = job_desc.inner_text() if job_desc else ""

        # 返回搜索结果页
        page.goto(search_url, timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)

        return {"job_description": job_description}
    except Exception as e:
        logger.error(f"获取职位详情时发生错误：{str(e)}")
        import traceback

        logger.error(f"错误详情：{traceback.format_exc()}")
        # 确保返回搜索结果页
        try:
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("networkidle")
        except:
            logger.error("返回搜索页面失败")
        return None


def search_jobs(page, keyword=SEARCH_KEYWORD):
    """搜索职位并提取信息"""
    try:
        # 点击顶部的"搜索"按钮进入搜索页面
        search_page_button = page.wait_for_selector('a[ka="header-job"]')
        logger.info("点击顶部搜索按钮")
        search_page_button.click()

        # 等待并定位搜索输入框
        search_input = page.wait_for_selector(
            'input[type="text"][placeholder="搜索职位、公司"]'
        )
        logger.info(f"开始搜索关键词: {keyword}")
        search_input.fill(keyword)

        # 点击搜索按钮
        search_button = page.wait_for_selector('a[ka="job_search_btn_click"]')
        search_button.click()

        # 等待搜索结果加载
        page.wait_for_load_state("networkidle")
        logger.info("搜索结果加载完成")

        # 保存搜索结果页面的URL
        search_url = page.url
        logger.info(f"搜索结果页面URL: {search_url}")

        # 等待职位列表出现
        page.wait_for_selector(".job-list-box")

        # 存储所有职位信息
        job_details = []

        # 先获取所有职位的基本信息
        job_items = page.query_selector_all(".job-card-wrapper")[:10]
        total_jobs = len(job_items)
        logger.info(f"找到 {total_jobs} 个职位")

        for index in range(1, total_jobs + 1):
            try:
                # 确保在搜索结果页面
                if page.url != search_url:
                    logger.info("重新回到搜索结果页面")
                    page.goto(search_url)
                    page.wait_for_load_state("networkidle")

                # 重新获取当前职位元素
                current_item = page.query_selector(
                    f".job-card-wrapper:nth-child({index})"
                )
                if not current_item:
                    logger.error(f"无法找到第 {index} 个职位元素")
                    continue

                # 提取职位链接
                job_link_element = current_item.query_selector(".job-card-left")
                if not job_link_element:
                    logger.error(f"第 {index} 个职位未找到链接元素")
                    continue

                job_link = job_link_element.get_attribute("href")
                if not job_link:
                    logger.error(f"第 {index} 个职位未找到链接地址")
                    continue

                job_link = (
                    f"https://www.zhipin.com{job_link}"
                    if job_link.startswith("/")
                    else job_link
                )

                # 创建职位信息字典
                job_info = {"index": index, "job_link": job_link}

                # 使用安全的提取方法
                def safe_extract(selector, attribute="inner_text"):
                    try:
                        element = current_item.query_selector(selector)
                        if element:
                            return getattr(element, attribute)()
                        return "N/A"
                    except Exception as e:
                        logger.error(f"提取 {selector} 时发生错误: {str(e)}")
                        return "N/A"

                # 提取基本信息
                job_info.update(
                    {
                        "job_name": safe_extract(".job-name"),
                        "job_area": safe_extract(".job-area"),
                        "salary": safe_extract(".salary"),
                        "company_name": safe_extract(".company-name"),
                    }
                )

                # 提取经验和学历要求
                requirements = current_item.query_selector_all(".job-info .tag-list li")
                for req in requirements:
                    try:
                        text = req.inner_text()
                        if "年" in text:
                            job_info["experience"] = text
                        elif "科" in text or "历" in text:
                            job_info["education"] = text
                    except Exception as e:
                        logger.error(f"提取要求信息时发生错误: {str(e)}")

                # 提取标签信息
                def safe_extract_tags(selector):
                    try:
                        elements = current_item.query_selector_all(selector)
                        return [
                            tag.inner_text() for tag in elements if tag.inner_text()
                        ]
                    except Exception as e:
                        logger.error(f"提取标签 {selector} 时发生错误: {str(e)}")
                        return []

                job_info.update(
                    {
                        "company_tags": safe_extract_tags(".company-tag-list li"),
                        "job_tags": safe_extract_tags(".job-card-footer .tag-list li"),
                    }
                )

                # 提取福利信息
                job_info["welfare"] = safe_extract(".info-desc")

                # 获取职位描述（从详情页）
                logger.info(f"\n正在获取第 {index} 个职位的详细描述...")
                detail_info = get_job_detail(page, job_link, search_url)

                if detail_info:
                    job_info.update(detail_info)

                job_details.append(job_info)

                # 打印提取到的信息
                logger.info(f"\n{index}. 职位详情:")
                for key, value in job_info.items():
                    if key != "job_description":
                        if isinstance(value, list):
                            logger.info(f'{key}: {", ".join(value)}')
                        else:
                            logger.info(f"{key}: {value}")
                if "job_description" in job_info:
                    logger.info("\n职位描述:")
                    logger.info(job_info["job_description"])
                logger.info("------------------------")

                # 添加随机延迟，避免频繁请求
                delay = random.uniform(2, 4)
                page.wait_for_timeout(int(delay * 1000))

            except Exception as e:
                logger.error(f"处理第 {index} 个职位时发生错误：{str(e)}")
                import traceback

                logger.error(f"错误详情：\n{traceback.format_exc()}")
                # 确保返回搜索结果页
                try:
                    page.goto(search_url)
                    page.wait_for_load_state("networkidle")
                except:
                    logger.error("返回搜索页面失败")
                continue

        logger.info("===== 职位信息获取完成 =====")

        # 将所有职位信息保存到文件
        if job_details:
            save_job_details(job_details)
        else:
            logger.warning("没有成功提取到任何职位信息")

    except Exception as e:
        logger.error(f"搜索职位时发生错误：{str(e)}")
        import traceback

        logger.error(f"错误详情：{traceback.format_exc()}")


def save_job_details(job_details):
    """保存职位详细信息到文件"""
    try:
        filename = f'job_details_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(job_details, f, ensure_ascii=False, indent=2)
        logger.info(f"职位详细信息已保存到文件: {filename}")
    except Exception as e:
        logger.error(f"保存职位详情时发生错误：{str(e)}")


def create_browser_context(playwright):
    """创建一个更真实的浏览器上下文"""
    browser = playwright.chromium.launch(
        headless=HEADLESS_MODE,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--start-maximized",
        ],
    )

    # 创建上下文并设置更真实的参数
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        java_script_enabled=True,
        has_touch=True,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        geolocation={"latitude": 39.9042, "longitude": 116.4074},  # 北京坐标
        permissions=["geolocation"],
    )

    # 注入脚本以修改 webdriver 属性
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """
    )

    return browser, context


def login_zhipin():
    try:
        with sync_playwright() as p:
            # 使用新的浏览器创建函数
            browser, context = create_browser_context(p)
            page = context.new_page()

            try:
                # 添加随机延迟和鼠标移动
                page.goto("https://www.zhipin.com/", timeout=30000)
                page.wait_for_load_state("networkidle")

                # 模拟真实的鼠标移动
                page.mouse.move(random.randint(0, 800), random.randint(0, 600))
                page.wait_for_timeout(random.randint(500, 1500))

                # 等待并点击登录按钮
                login_button = page.wait_for_selector("text=登录/注册", timeout=5000)
                if login_button:
                    logger.info("找到登录按钮")
                    login_button.click()
                    logger.info("已点击登录按钮")

                # 等待登录框加载并点击微信登录
                wechat_login = page.wait_for_selector("a.wx-login-btn", timeout=5000)
                if wechat_login:
                    logger.info("找到微信登录按钮")
                    wechat_login.click()
                    logger.info("已点击微信登录按钮")
                else:
                    logger.warning("未找到微信登录按钮")
                    # 尝试使用更具体的选择器
                    wechat_login = page.wait_for_selector(
                        '[ka="wx_signin"]', timeout=5000
                    )
                    if wechat_login:
                        logger.info("使用备用选择器找到微信登录按钮")
                        wechat_login.click()
                        logger.info("已点击微信登录按钮")
                    else:
                        logger.error("所有尝试都未找到微信登录按钮")

                logger.info("请使用微信扫描二维码登录...")

                # 等待用户扫码并登录成功
                page.wait_for_selector(".user-nav", timeout=120000)  # 2分钟超时
                logger.info("登录成功！")

                # 登录成功后，执行搜索
                logger.info("开始搜索职位...")
                search_jobs(page)

                # 保持页面打开一段时间
                page.wait_for_timeout(10000)

                # 保存登录状态（cookies）
                cookies = page.context.cookies()

                # 保存到文件
                if save_cookies(cookies):
                    logger.info("登录状态已保存到文件")

                return cookies

            except PlaywrightTimeoutError:
                logger.error("等待超时，请重试")
                return None
            except Exception as e:
                logger.error(f"登录过程中发生错误：{str(e)}")
                return None
            finally:
                browser.close()
    except Exception as e:
        logger.error(f"发生错误：{str(e)}")
        return None


def reuse_login_session(cookies=None):
    """使用已保存的登录状态重新登录"""
    if cookies is None:
        cookies = load_cookies()
        if cookies is None:
            logger.warning("没有找到已保存的登录状态")
            return False

    try:
        with sync_playwright() as p:
            # 使用新的浏览器创建函数
            browser, context = create_browser_context(p)

            # 设置保存的 cookies
            context.add_cookies(cookies)

            page = context.new_page()

            # 添加随机延迟和行为
            page.goto("https://www.zhipin.com/")
            page.wait_for_load_state("networkidle")

            # 模拟真实的滚动行为
            for _ in range(3):
                page.mouse.wheel(0, random.randint(100, 300))
                page.wait_for_timeout(random.randint(500, 1500))

            # 验证是否登录成功
            try:
                page.wait_for_selector(".user-nav", timeout=10000)
                logger.info("使用已保存的登录状态成功！")

                # 登录成功后执行搜索
                search_jobs(page)

                # 保持页面打开一段时间
                page.wait_for_timeout(10000)

                return True
            except:
                logger.warning("登录状态已失效，需要重新登录")
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
        # 重新登录并获取新的 cookies
        cookies = login_zhipin()

        if cookies:
            # 等待一段时间后验证登录状态
            logger.info("等待 10 秒后验证登录状态...")
            time.sleep(10)
            reuse_login_session(cookies)
