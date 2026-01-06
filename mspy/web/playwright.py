"""
Playwright Web页面集成模块
"""

import asyncio
import base64
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from playwright.async_api import Page, Browser, BrowserContext, Playwright

from ..shared import (
    get_debug,
    Size,
    Rect,
    UIContext,
    DeviceAction,
    LocateResultElement,
)
from ..core import AbstractInterface, define_action

debug = get_debug('web:playwright')


class PlaywrightPage(AbstractInterface):
    """Playwright页面封装"""
    
    def __init__(
        self,
        page: Page,
        view_width: int = 1280,
        view_height: int = 720,
    ):
        """
        初始化Playwright页面
        
        Args:
            page: Playwright Page对象
            view_width: 视口宽度
            view_height: 视口高度
        """
        self._page = page
        self._view_width = view_width
        self._view_height = view_height
        debug(f"PlaywrightPage initialized with viewport {view_width}x{view_height}")
    
    @property
    def interface_type(self) -> str:
        return 'playwright'
    
    @property
    def page(self) -> Page:
        """获取底层Page对象"""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """获取屏幕截图的base64编码"""
        debug("Taking screenshot")
        screenshot_bytes = await self._page.screenshot(type='jpeg', quality=90)
        base64_str = base64.b64encode(screenshot_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_str}"
    
    async def size(self) -> Size:
        """获取屏幕尺寸"""
        viewport = self._page.viewport_size
        if viewport:
            return Size(width=viewport['width'], height=viewport['height'])
        return Size(width=self._view_width, height=self._view_height)
    
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作空间"""
        return [
            self._define_tap_action(),
            self._define_hover_action(),
            self._define_input_action(),
            self._define_keyboard_press_action(),
            self._define_scroll_action(),
        ]
    
    def _define_tap_action(self) -> DeviceAction:
        """定义点击动作"""
        async def tap(param: Dict[str, Any], context: Any = None) -> None:
            locate = param.get('locate')
            if not locate:
                raise ValueError("locate is required for Tap action")
            
            center = locate.center if hasattr(locate, 'center') else locate.get('center')
            if not center:
                raise ValueError("center is required for Tap action")
            
            x, y = center
            debug(f"Tapping at ({x}, {y})")
            await self._page.mouse.click(x, y)
        
        return define_action(
            name='Tap',
            description='Tap the element',
            call=tap,
            param_schema={'locate': 'MidsceneLocation'},
            interface_alias='aiTap',
        )
    
    def _define_hover_action(self) -> DeviceAction:
        """定义悬停动作"""
        async def hover(param: Dict[str, Any], context: Any = None) -> None:
            locate = param.get('locate')
            if not locate:
                raise ValueError("locate is required for Hover action")
            
            center = locate.center if hasattr(locate, 'center') else locate.get('center')
            if not center:
                raise ValueError("center is required for Hover action")
            
            x, y = center
            debug(f"Hovering at ({x}, {y})")
            await self._page.mouse.move(x, y)
        
        return define_action(
            name='Hover',
            description='Move the mouse to the element',
            call=hover,
            param_schema={'locate': 'MidsceneLocation'},
            interface_alias='aiHover',
        )
    
    def _define_input_action(self) -> DeviceAction:
        """定义输入动作"""
        async def input_action(param: Dict[str, Any], context: Any = None) -> None:
            value = param.get('value', '')
            locate = param.get('locate')
            mode = param.get('mode', 'replace')
            
            # 如果有定位，先点击
            if locate:
                center = locate.center if hasattr(locate, 'center') else locate.get('center')
                if center:
                    x, y = center
                    debug(f"Clicking at ({x}, {y}) before input")
                    await self._page.mouse.click(x, y)
                    await asyncio.sleep(0.1)
            
            if mode == 'clear':
                # 清除模式
                debug("Clearing input")
                await self._page.keyboard.press('Control+a')
                await self._page.keyboard.press('Backspace')
            elif mode == 'append':
                # 追加模式
                debug(f"Appending: {value}")
                await self._page.keyboard.type(str(value))
            else:
                # 替换模式（默认）
                debug(f"Replacing with: {value}")
                await self._page.keyboard.press('Control+a')
                await self._page.keyboard.type(str(value))
        
        return define_action(
            name='Input',
            description='Input the value into the element',
            call=input_action,
            param_schema={
                'value': 'string',
                'locate': 'MidsceneLocation (optional)',
                'mode': 'replace | clear | append (optional)',
            },
            interface_alias='aiInput',
        )
    
    def _define_keyboard_press_action(self) -> DeviceAction:
        """定义键盘按键动作"""
        async def keyboard_press(param: Dict[str, Any], context: Any = None) -> None:
            key_name = param.get('keyName', '')
            locate = param.get('locate')
            
            if not key_name:
                raise ValueError("keyName is required for KeyboardPress action")
            
            # 如果有定位，先点击
            if locate:
                center = locate.center if hasattr(locate, 'center') else locate.get('center')
                if center:
                    x, y = center
                    debug(f"Clicking at ({x}, {y}) before keyboard press")
                    await self._page.mouse.click(x, y)
                    await asyncio.sleep(0.1)
            
            debug(f"Pressing key: {key_name}")
            await self._page.keyboard.press(key_name)
        
        return define_action(
            name='KeyboardPress',
            description='Press a key or key combination',
            call=keyboard_press,
            param_schema={
                'keyName': 'string',
                'locate': 'MidsceneLocation (optional)',
            },
            interface_alias='aiKeyboardPress',
        )
    
    def _define_scroll_action(self) -> DeviceAction:
        """定义滚动动作"""
        async def scroll(param: Dict[str, Any], context: Any = None) -> None:
            scroll_type = param.get('scrollType', 'singleAction')
            direction = param.get('direction', 'down')
            distance = param.get('distance')
            locate = param.get('locate')
            
            # 确定滚动位置
            x, y = self._view_width // 2, self._view_height // 2
            if locate:
                center = locate.center if hasattr(locate, 'center') else locate.get('center')
                if center:
                    x, y = center
            
            # 计算滚动距离
            if distance is None:
                distance = 300
            
            # 根据方向确定滚动参数
            delta_x, delta_y = 0, 0
            if direction == 'down':
                delta_y = distance
            elif direction == 'up':
                delta_y = -distance
            elif direction == 'right':
                delta_x = distance
            elif direction == 'left':
                delta_x = -distance
            
            debug(f"Scrolling at ({x}, {y}) with delta ({delta_x}, {delta_y})")
            
            if scroll_type == 'singleAction':
                await self._page.mouse.wheel(delta_x, delta_y)
            elif scroll_type == 'scrollToBottom':
                for _ in range(20):
                    await self._page.mouse.wheel(0, 500)
                    await asyncio.sleep(0.1)
            elif scroll_type == 'scrollToTop':
                for _ in range(20):
                    await self._page.mouse.wheel(0, -500)
                    await asyncio.sleep(0.1)
        
        return define_action(
            name='Scroll',
            description='Scroll the page or an element',
            call=scroll,
            param_schema={
                'scrollType': 'singleAction | scrollToBottom | scrollToTop',
                'direction': 'down | up | right | left',
                'distance': 'number (optional)',
                'locate': 'MidsceneLocation (optional)',
            },
            interface_alias='aiScroll',
        )
    
    async def navigate(self, url: str, wait_for_network_idle: bool = True) -> None:
        """
        导航到URL
        
        Args:
            url: 目标URL
            wait_for_network_idle: 是否等待网络空闲
        """
        debug(f"Navigating to {url}")
        
        if wait_for_network_idle:
            await self._page.goto(url, wait_until='networkidle')
        else:
            await self._page.goto(url)
        
        debug(f"Navigation completed")
    
    async def wait_for_network_idle(self, timeout: int = 30000) -> None:
        """
        等待网络空闲
        
        Args:
            timeout: 超时时间（毫秒）
        """
        debug("Waiting for network idle")
        try:
            await self._page.wait_for_load_state('networkidle', timeout=timeout)
            debug("Network idle")
        except Exception as e:
            debug(f"Wait for network idle timeout: {e}")
    
    async def destroy(self) -> None:
        """销毁页面"""
        debug("Destroying PlaywrightPage")
        # 不关闭page，让调用者管理


class PlaywrightBrowser:
    """Playwright浏览器封装"""
    
    def __init__(
        self,
        headless: bool = True,
        view_width: int = 1280,
        view_height: int = 720,
        user_data_dir: Optional[str] = None,
    ):
        """
        初始化浏览器
        
        Args:
            headless: 是否无头模式
            view_width: 视口宽度
            view_height: 视口高度
            user_data_dir: 用户数据目录
        """
        self._headless = headless
        self._view_width = view_width
        self._view_height = view_height
        self._user_data_dir = user_data_dir
        
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        debug(f"PlaywrightBrowser initialized (headless={headless})")
    
    async def launch(self) -> 'PlaywrightBrowser':
        """启动浏览器"""
        from playwright.async_api import async_playwright
        
        debug("Launching browser")
        self._playwright = await async_playwright().start()
        
        if self._user_data_dir:
            # 使用持久化上下文
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=self._user_data_dir,
                headless=self._headless,
                viewport={'width': self._view_width, 'height': self._view_height},
            )
            pages = self._context.pages
            self._page = pages[0] if pages else await self._context.new_page()
        else:
            # 普通启动
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
            )
            self._context = await self._browser.new_context(
                viewport={'width': self._view_width, 'height': self._view_height},
            )
            self._page = await self._context.new_page()
        
        debug("Browser launched")
        return self
    
    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """
        设置cookies
        
        Args:
            cookies: cookie列表
        """
        if self._context:
            debug(f"Setting {len(cookies)} cookies")
            await self._context.add_cookies(cookies)
    
    async def set_local_storage(self, url: str, items: Dict[str, str]) -> None:
        """
        设置localStorage
        
        Args:
            url: 页面URL（用于设置origin）
            items: localStorage项
        """
        if self._page:
            debug(f"Setting {len(items)} localStorage items")
            # 先导航到目标URL，然后设置localStorage
            for key, value in items.items():
                await self._page.evaluate(
                    f'localStorage.setItem("{key}", {json.dumps(value)})'
                )
    
    def get_page(self) -> PlaywrightPage:
        """获取页面封装"""
        if not self._page:
            raise RuntimeError("Browser not launched")
        return PlaywrightPage(self._page, self._view_width, self._view_height)
    
    async def close(self) -> None:
        """关闭浏览器"""
        debug("Closing browser")
        
        if self._context:
            await self._context.close()
        
        if self._browser:
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        debug("Browser closed")


async def create_playwright_page(
    headless: bool = True,
    view_width: int = 1280,
    view_height: int = 720,
    user_data_dir: Optional[str] = None,
    cookies: Optional[List[Dict[str, Any]]] = None,
    local_storage: Optional[Dict[str, Dict[str, str]]] = None,
) -> Tuple[PlaywrightBrowser, PlaywrightPage]:
    """
    创建Playwright页面
    
    Args:
        headless: 是否无头模式
        view_width: 视口宽度
        view_height: 视口高度
        user_data_dir: 用户数据目录
        cookies: 要设置的cookies
        local_storage: 要设置的localStorage (url -> items)
    
    Returns:
        (browser, page) 元组
    """
    browser = PlaywrightBrowser(
        headless=headless,
        view_width=view_width,
        view_height=view_height,
        user_data_dir=user_data_dir,
    )
    await browser.launch()
    
    if cookies:
        await browser.set_cookies(cookies)
    
    page = browser.get_page()
    
    return browser, page
