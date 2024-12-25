import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime, timedelta
import os
import random
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logger import setup_logger

config_path = os.path.join(os.path.dirname(__file__), "../../conf/liepin.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

logger = setup_logger(name=config["log_name"], level=config["log_level"])
logger.debug(f"加载配置文件: {config}")


class LiepinSelectors:
    """猎聘网登录相关的选择器"""

    LOGIN_BUTTON = ".login-btn"  # 登录按钮
    SCAN_LOGIN_TAB = ".scan-login-tab"  # 扫码登录标签
    QR_CODE = ".qr-code img"  # 二维码图片
    USER_NAV = ".user-nav"  # 用户导航栏，用于判断登录状态
    USER_MENU = ".user-menu"  # 用户菜单


class LiepinLogin:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.cookies_file = config.get("cookies_file", "liepin_cookies.json")
        self.login_url = config["login_url"]
        self.home_url = config["home_url"]

    async def init_browser(self):
        """初始化浏览器"""
        logger.info("初始化浏览器")
        self.playwright = await async_playwright().start()
        browser_args =[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--ignore-certificate-errors",
            f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36",
        ]

        self.browser = await self.playwright.chromium.launch(
            headless=config["headless"], args=browser_args
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        await self.page.goto(self.login_url)
        logger.info("浏览器初始化完成")

    async def login(self) -> bool:
        """执行登录流程"""
        logger.info("开始登录流程")

        # 尝试使用cookies登录
        if await self._try_cookie_login():
            logger.info("Cookie登录成功")
            return True

        logger.debug("Cookie登录失败，执行扫码登录")

        # Cookie登录失败，执行扫码登录
        return await self.login_by_qrcode()

    async def login_by_qrcode(self) -> bool:
        """通过扫码方式登录"""
        try:
            # 跳转到登录页面
            await self.page.goto(self.login_url)
            logger.debug("已跳转到登录页面")
            # 等待扫码登录标签出现并点击
            await self.page.click(".switch-type-mask-img-box img")
            logger.debug("切换到扫码登录")

            # 等待二维码出现
            await self.page.wait_for_selector(".qr-code-img")
            logger.info("二维码已加载，请使用猎聘APP扫码登录")

            # 获取二维码图片的src属性
            qr_code_element = await self.page.wait_for_selector(".qr-code-img")
            qr_code_src = await qr_code_element.get_attribute("src")
            logger.debug(f"获取到二维码链接: {qr_code_src}")

            # 尝试打印二维码到控制台
            await self._print_qrcode_to_console(qr_code_src)

            # 等待登录成功
            if await self._wait_for_login_success():
                logger.info("扫码登录成功")
                # 保存cookies
                await self._save_cookies()
                return True

            logger.warning("扫码登录超时,已达到最大尝试次数")
            return False

        except Exception as e:
            logger.error(f"扫码登录过程出现错误: {e}", exc_info=True)
            # 截图保存到log目录
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                log_dir, f"liepin_login_failed_{timestamp}.png"
            )
            await self.page.screenshot(path=screenshot_path)
            logger.debug(f"已保存登录失败截图: {screenshot_path}")
            return False

    async def _print_qrcode_to_console(self, qr_code_src: str):
        """将二维码打印到控制台"""
        try:
            import qrcode
            import io
            from PIL import Image
            import requests

            # 下载二维码图片
            response = requests.get(qr_code_src)
            img = Image.open(io.BytesIO(response.content))

            # 创建一个新的二维码对象
            qr = qrcode.QRCode()
            qr.add_data(qr_code_src)
            qr.make()

            # 打印二维码到控制台
            qr.print_ascii(invert=False)
            logger.info("二维码已打印到控制台，请使用微信扫描登录")

        except Exception as e:
            logger.error(f"打印二维码到控制台时出错: {e}")
            logger.info(f"请直接使用微信扫描页面上的二维码进行登录")

    async def _wait_for_login_success(
        self, max_attempts: int = 5, interval: int = 2
    ) -> bool:
        """等待登录成功

        Args:
            max_attempts: 最大尝试次数
            interval: 每次检查的间隔时间(秒)

        Returns:
            bool: 是否登录成功
        """
        attempts = 0
        while attempts < max_attempts:
            if await self.check_login_status():
                return True

            attempts += 1
            logger.debug(f"等待登录中,第{attempts}次尝试")
            await asyncio.sleep(interval)

        return False

    async def _try_cookie_login(self) -> bool:
        """尝试使用cookies登录"""
        try:
            if not os.path.exists(self.cookies_file):
                logger.debug(f"Cookie文件不存在: {self.cookies_file}")
                return False

            logger.debug(f"使用Cookie登录[{self.cookies_file}]")
            # 读取cookies
            with open(self.cookies_file, "r") as f:
                cookies = json.load(f)

            # 检查cookies是否过期
            if self._is_cookies_expired(cookies):
                logger.debug("Cookies已过期")
                return False

            # 设置cookies
            await self.context.add_cookies(cookies)

            # 先访问主页
            await self.page.goto(self.home_url)

            # 重新加载页面以应用cookies
            # await self.page.reload()
            await asyncio.sleep(2)  # 等待页面加载完成

            # 验证登录状态
            is_logged_in = await self.check_login_status()
            if not is_logged_in:
                logger.debug("Cookie登录失败，cookie可能已失效")
                # 删除失效的cookie文件
                # os.remove(self.cookies_file)
                # 截图保存到log目录
                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(
                    log_dir, f"liepin_login_failed_{timestamp}.png"
                )
                await self.page.screenshot(path=screenshot_path)
                logger.debug(f"已保存登录失败截图: {screenshot_path}")
                return False

            logger.info("Cookie登录成功")
            return True

        except Exception as e:
            logger.error(f"Cookie登录失败: {e}")
            return False

    def _is_cookies_expired(self, cookies: list) -> bool:
        """检查cookies是否过期"""
        try:
            current_time = time.time()
            for cookie in cookies:
                # 只检查关键cookie的过期时间
                if cookie.get("name") in [
                    "__login_token",
                    "access_token",
                    "user_token",
                ]:
                    if "expires" in cookie:
                        expires = cookie["expires"]
                        if expires < current_time:
                            return True
            return False
        except Exception as e:
            logger.error(f"检查Cookie过期状态失败: {e}")
            return True

    async def _save_cookies(self):
        """保存cookies到文件，并延长有效期"""
        try:
            cookies = await self.context.cookies()
            # 设置Cookie有效期为30天
            thirty_days = int((datetime.now() + timedelta(days=30)).timestamp())

            # 更新每个cookie的过期时间
            for cookie in cookies:
                # 设置domain和path
                if "domain" not in cookie:
                    cookie["domain"] = ".liepin.com"
                if "path" not in cookie:
                    cookie["path"] = "/"
                # 更新过期时间
                cookie["expires"] = thirty_days

            with open(self.cookies_file, "w") as f:
                json.dump(cookies, f)
            logger.debug(f"Cookies保存成功[{self.cookies_file}]，有效期30天")
        except Exception as e:
            logger.error(f"保存Cookies失败[{self.cookies_file}]: {e}")

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        logger.debug("检查登录状态")
        try:
            await self.page.wait_for_selector(
                "#header-quick-menu-user-info", timeout=5000
            )
            await self.page.wait_for_selector(
                ".header-quick-menu-username", timeout=5000
            )
            logger.debug("用户已登录")
            return True
        except Exception as e:
            logger.debug(f"用户未登录: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        logger.debug("关闭浏览器")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.debug("浏览器已关闭")


async def main():
    login = LiepinLogin()
    await login.init_browser()

    if await login.login():
        print("登录成功!")
    else:
        print("登录失败!")

    await login.close()


if __name__ == "__main__":
    asyncio.run(main())
