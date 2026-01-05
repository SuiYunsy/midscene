"""Playwright页面封装"""
import asyncio
import base64
from typing import Any, Dict, List, Optional, Tuple
from playwright.async_api import Page, Browser, BrowserContext, async_playwright, Playwright
from .interface import AbstractInterface
from .actions import get_web_action_space
from ..core.types import DeviceAction, Size
from ..shared.logger import get_logger
from ..shared.constants import (
    DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
    DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
    SCROLL_MAX_DISTANCE,
)

logger = get_logger("playwright")

class PlaywrightPage(AbstractInterface):
    """Playwright页面封装"""
    interface_type = "playwright"
    def __init__(
        self,
        page: Page,
        wait_for_navigation_timeout: int = DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
        wait_for_network_idle_timeout: int = DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
    ):
        self._page = page
        self._wait_nav_timeout = wait_for_navigation_timeout
        self._wait_idle_timeout = wait_for_network_idle_timeout
        self._size: Optional[Size] = None
        self._action_space: Optional[List[DeviceAction]] = None
    @property
    def page(self) -> Page:
        """获取底层Playwright页面"""
        return self._page
    async def screenshot_base64(self) -> str:
        """获取页面截图"""
        await self._wait_for_navigation()
        buffer = await self._page.screenshot(type="jpeg", quality=90)
        b64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    async def size(self) -> Size:
        """获取页面尺寸"""
        if self._size:
            return self._size
        viewport = self._page.viewport_size
        if viewport:
            self._size = Size(
                width=viewport["width"],
                height=viewport["height"],
                dpr=1.0,
            )
        else:
            # 从页面获取
            dimensions = await self._page.evaluate("""() => ({
                width: document.documentElement.clientWidth,
                height: document.documentElement.clientHeight,
                dpr: window.devicePixelRatio
            })""")
            self._size = Size(
                width=dimensions["width"],
                height=dimensions["height"],
                dpr=dimensions.get("dpr", 1.0),
            )
        return self._size
    def action_space(self) -> List[DeviceAction]:
        """获取动作空间"""
        if self._action_space is None:
            self._action_space = get_web_action_space(self)
        return self._action_space
    async def url(self) -> str:
        """获取当前URL"""
        return self._page.url
    async def destroy(self) -> None:
        """销毁页面"""
        try:
            await self._page.close()
        except Exception:
            pass
    async def _wait_for_navigation(self) -> None:
        """等待导航完成"""
        if self._wait_nav_timeout == 0:
            return
        try:
            await self._page.wait_for_selector("html", timeout=self._wait_nav_timeout)
        except Exception:
            logger.warning("等待导航超时，继续执行")
    async def _wait_for_network_idle(self) -> None:
        """等待网络空闲"""
        if self._wait_idle_timeout == 0:
            return
        try:
            await self._page.wait_for_load_state("networkidle", timeout=self._wait_idle_timeout)
        except Exception:
            logger.warning("等待网络空闲超时，继续执行")
    # 鼠标操作
    async def mouse_click(self, x: int, y: int, button: str = "left") -> None:
        """鼠标点击"""
        await self._page.mouse.click(x, y, button=button)
        await self._wait_for_network_idle()
    async def mouse_dblclick(self, x: int, y: int) -> None:
        """鼠标双击"""
        await self._page.mouse.dblclick(x, y)
        await self._wait_for_network_idle()
    async def mouse_move(self, x: int, y: int) -> None:
        """移动鼠标"""
        await self._page.mouse.move(x, y)
    async def drag(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> None:
        """拖动"""
        await self._page.mouse.move(from_pos[0], from_pos[1])
        await asyncio.sleep(0.2)
        await self._page.mouse.down()
        await asyncio.sleep(0.3)
        await self._page.mouse.move(to_pos[0], to_pos[1], steps=20)
        await asyncio.sleep(0.5)
        await self._page.mouse.up()
        await asyncio.sleep(0.2)
    # 键盘操作
    async def keyboard_type(self, text: str) -> None:
        """输入文本"""
        await self._page.keyboard.type(text, delay=80)
    async def keyboard_press(self, key: str) -> None:
        """按键"""
        # 处理组合键
        if "+" in key:
            keys = key.split("+")
            for k in keys:
                await self._page.keyboard.down(k.strip())
            for k in reversed(keys):
                await self._page.keyboard.up(k.strip())
        else:
            await self._page.keyboard.press(key)
    async def clear_input(self) -> None:
        """清空输入框"""
        # 全选然后删除
        await self._page.keyboard.press("Control+a")
        await self._page.keyboard.press("Backspace")
    # 滚动操作
    async def scroll(
        self,
        delta_x: int,
        delta_y: int,
        start_x: Optional[int] = None,
        start_y: Optional[int] = None,
    ) -> None:
        """滚动页面"""
        if start_x is not None and start_y is not None:
            await self._page.mouse.move(start_x, start_y)
        await self._page.mouse.wheel(delta_x, delta_y)
    async def scroll_to_top(
        self, start_x: Optional[int] = None, start_y: Optional[int] = None
    ) -> None:
        """滚动到顶部"""
        await self.scroll(0, -SCROLL_MAX_DISTANCE, start_x, start_y)
    async def scroll_to_bottom(
        self, start_x: Optional[int] = None, start_y: Optional[int] = None
    ) -> None:
        """滚动到底部"""
        await self.scroll(0, SCROLL_MAX_DISTANCE, start_x, start_y)
    async def scroll_to_left(
        self, start_x: Optional[int] = None, start_y: Optional[int] = None
    ) -> None:
        """滚动到最左"""
        await self.scroll(-SCROLL_MAX_DISTANCE, 0, start_x, start_y)
    async def scroll_to_right(
        self, start_x: Optional[int] = None, start_y: Optional[int] = None
    ) -> None:
        """滚动到最右"""
        await self.scroll(SCROLL_MAX_DISTANCE, 0, start_x, start_y)
    # 导航操作
    async def goto(self, url: str) -> None:
        """导航到URL"""
        await self._page.goto(url)
        await self._wait_for_navigation()
        await self._wait_for_network_idle()
    async def reload(self) -> None:
        """刷新页面"""
        await self._page.reload()
        await self._wait_for_navigation()
        await self._wait_for_network_idle()
    async def go_back(self) -> None:
        """后退"""
        await self._page.go_back()
        await self._wait_for_navigation()
        await self._wait_for_network_idle()

class PlaywrightLauncher:
    """Playwright启动器"""
    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        user_data_dir: Optional[str] = None,
        cookies: Optional[List[Dict[str, Any]]] = None,
        local_storage: Optional[Dict[str, str]] = None,
    ):
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.user_data_dir = user_data_dir
        self.cookies = cookies
        self.local_storage = local_storage
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    async def launch(self) -> PlaywrightPage:
        """启动浏览器并返回页面"""
        self._playwright = await async_playwright().start()
        # 启动浏览器
        if self.user_data_dir:
            self._context = await self._playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                viewport={"width": self.viewport_width, "height": self.viewport_height},
            )
            self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
        else:
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(
                viewport={"width": self.viewport_width, "height": self.viewport_height},
            )
            self._page = await self._context.new_page()
        # 设置cookies
        if self.cookies:
            await self._context.add_cookies(self.cookies)
        # 设置localStorage
        if self.local_storage:
            for key, value in self.local_storage.items():
                await self._page.evaluate(f"localStorage.setItem({key!r}, {value!r})")
        return PlaywrightPage(self._page)
    async def close(self) -> None:
        """关闭浏览器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
