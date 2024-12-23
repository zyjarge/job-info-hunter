import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import os
import random
from utils.logger import setup_logger

# 初始化logger
logger = setup_logger()

class BossSelectors:
    """BOSS直聘网站元素选择器"""
    LOGIN_BUTTON = '.header-login-btn'  # 或 'text=登录/注册'
    WECHAT_LOGIN_BUTTON = '.wx-login-btn'

    # 二维码相关
    QR_CODE_CONTAINER = '.qrcode-box'
    QR_CODE_IMG = '.qrcode-box img'
    QR_CODE_TIPS = '.scan-title'  # 扫码提示文字
    

    # 小程序二维码相关
    MINI_APP_CONTAINER = '.mini-app-login'
    MINI_APP_QRCODE = '.mini-app-login img.mini-qrcode'
    
    # 登录状态相关
    USER_NAV = '.user-nav'  # 登录成功后的用户导航
    USER_MENU = '.nav-figure'  # 用户头像/菜单
    
    # 登录框相关
    LOGIN_MODAL = '.login-modal'  # 登录弹窗
    CLOSE_MODAL = '.close-modal'  # 关闭登录弹窗的按钮

class BossLogin:
    def __init__(self):
        self.cookie_file = "boss_cookies.json"
        self.login_url = "https://zhipin.com"
        logger.debug("初始化BossLogin实例")
        
    async def init_browser(self):
        """初始化浏览器"""
        logger.debug("开始初始化浏览器")
        self.playwright = await async_playwright().start()
        
        # 随机选择一个 User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        ]
        selected_ua = random.choice(user_agents)
        logger.debug(f"选择User-Agent: {selected_ua}")
        
        # 添加更多浏览器启动参数
        browser_args = [
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins',
            '--disable-site-isolation-trials',
            f'--window-size={random.randint(1200,1600)},{random.randint(800,1000)}',
        ]
        
        logger.debug("启动浏览器")
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=browser_args
        )
        
        logger.debug("创建浏览器上下文")
        window_width = random.randint(1200,1600)
        window_height = random.randint(800,1000)
        logger.debug(f"设置窗口大小: {window_width}x{window_height}")
        
        self.context = await self.browser.new_context(
            viewport={'width': window_width, 'height': window_height},
            user_agent=selected_ua,
            java_script_enabled=True,
            has_touch=True,
            is_mobile=False,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京坐标
            permissions=['geolocation'],
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
            },
            ignore_https_errors=True
        )
        
        logger.debug("注入反自动化检测脚本")
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        logger.debug("创建新页面")
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)
        logger.debug("浏览器初始化完成")
        
    async def random_delay(self, min_seconds=1, max_seconds=3):
        """随机延时"""
        delay_time = random.uniform(min_seconds, max_seconds)
        logger.debug(f"随机延时 {delay_time:.2f} 秒")
        await asyncio.sleep(delay_time)
        
    async def simulate_human_behavior(self):
        """模拟人类行为"""
        logger.debug("开始模拟人类行为")
        # 随机鼠标移动
        moves_count = random.randint(2, 5)
        logger.debug(f"执行{moves_count}次随机鼠标移动")
        for i in range(moves_count):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            logger.debug(f"鼠标移动到坐标: ({x}, {y})")
            await self.page.mouse.move(x, y)
            await self.random_delay(0.1, 0.3)
            
        logger.debug("执行随机页面滚动")
        await self.page.evaluate("""
            window.scrollTo({
                top: Math.floor(Math.random() * 100),
                behavior: 'smooth'
            });
        """)
        logger.debug("人类行为模拟完成")
        
    def load_cookies(self):
        """从文件加载cookies"""
        logger.debug(f"尝试从 {self.cookie_file} 加载cookies")
        if not os.path.exists(self.cookie_file):
            logger.debug("Cookie文件不存在")
            return None
            
        with open(self.cookie_file, 'r') as f:
            cookie_data = json.load(f)
            
        # 检查cookie是否过期
        expires = datetime.fromisoformat(cookie_data['expires'])
        if expires < datetime.now():
            logger.debug(f"Cookie已过期 (过期时间: {expires})")
            return None
            
        logger.debug("成功加载有效的cookies")
        return cookie_data['cookies']
        
    def save_cookies(self, cookies):
        """保存cookies到文件"""
        logger.debug("保存cookies到文件")
        expires = (datetime.now() + timedelta(days=30)).isoformat()
        cookie_data = {
            'cookies': cookies,
            'expires': expires
        }
        with open(self.cookie_file, 'w') as f:
            json.dump(cookie_data, f)
        logger.debug(f"Cookies已保存，过期时间: {expires}")
            
    async def login(self):
        """执行登录流程"""
        try:
            logger.debug("开始登录流程")
            cookies = self.load_cookies()
            if cookies:
                logger.debug("使用已保存的cookies尝试登录")
                await self.context.add_cookies(cookies)
                await self.page.goto(self.login_url, wait_until='networkidle')
                await self.random_delay()
                
                if await self.check_login_status():
                    logger.debug("使用cookies登录成功")
                    return True
                logger.debug("cookies登录失败，尝试重新登录")
                
            logger.debug(f"打开登录页面: {self.login_url}")
            await self.page.goto(self.login_url, wait_until='networkidle')
            await self.random_delay()
            
            await self.simulate_human_behavior()
            
            logger.debug("点击登录按钮")
            await self.page.hover(BossSelectors.LOGIN_BUTTON)
            await self.random_delay(0.5, 1)
            await self.page.click(BossSelectors.LOGIN_BUTTON)
            
            logger.debug("等待登录框出现")
            logger.debug("点击切换到扫码登录")
            # 点击微信登录按钮
            logger.debug("点击微信登录按钮")
            await self.page.wait_for_selector(BossSelectors.WECHAT_LOGIN_BUTTON)
            await self.page.hover(BossSelectors.WECHAT_LOGIN_BUTTON)
            await self.random_delay(0.5, 1)
            await self.page.click(BossSelectors.WECHAT_LOGIN_BUTTON)
            await self.random_delay()
            
            # 等待小程序二维码出现
            logger.debug("等待小程序二维码出现")
            await self.page.wait_for_selector(BossSelectors.MINI_APP_CONTAINER)
            await self.page.wait_for_selector(BossSelectors.MINI_APP_QRCODE)
            await self.random_delay(0.5, 1)
            
            logger.debug("等待用户扫码登录")
            # 等待用户扫码登录成功的标志 - 检查用户头像和下拉菜单是否出现
            logger.debug("等待用户头像和菜单出现")
            try:
                await self.page.wait_for_selector(BossSelectors.USER_MENU, timeout=300000)  # 5分钟超时
                await self.page.wait_for_selector(f"{BossSelectors.USER_MENU} .label-text", timeout=5000)
                await self.page.wait_for_selector(f"{BossSelectors.USER_MENU} img", timeout=5000)
                logger.debug("检测到用户头像和菜单元素,登录成功")
                
            except Exception as e:
                logger.error(f"等待登录超时或元素未找到: {e}")
                raise Exception("登录失败 - 未检测到用户登录标志")
            
            await self.page.wait_for_selector(BossSelectors.USER_NAV, timeout=300000)
            logger.debug("检测到登录成功")
            await self.random_delay()
            
            cookies = await self.context.cookies()
            self.save_cookies(cookies)
            logger.debug("登录流程完成")
            
            return True
            
        except Exception as e:
            logger.error(f"登录过程出现错误: {e}", exc_info=True)
            return False
            
    async def check_login_status(self):
        """检查登录状态"""
        logger.debug("检查登录状态")
        try:
            await self.page.wait_for_selector(BossSelectors.USER_NAV, timeout=5000)
            await self.page.wait_for_selector(BossSelectors.USER_MENU, timeout=5000)
            logger.debug("用户已登录")
            return True
        except Exception as e:
            logger.debug(f"用户未登录: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        logger.debug("关闭浏览器")
        await self.browser.close()
        await self.playwright.stop()
        logger.debug("浏览器已关闭")

async def main():
    boss = BossLogin()
    await boss.init_browser()
    
    if await boss.login():
        print("登录成功!")
    else:
        print("登录失败!")
        
    await boss.close()

if __name__ == "__main__":
    asyncio.run(main()) 