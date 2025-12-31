"""
Playwright页面封装

从 packages/web-integration/src/puppeteer/base-page.ts 迁移
只保留Playwright部分
"""

import asyncio
import platform
from typing import Any, Optional, Tuple, TYPE_CHECKING

from mspy.core.types import DeviceAction, UIContext
from mspy.shared.constants import (
    DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
    DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
)
from mspy.shared.img import create_img_base64_by_format
from mspy.shared.logger import get_debug
from mspy.shared.types import Point, Rect, Size
from mspy.web.web_page import AbstractWebPage, KeyCommand, get_key_commands

if TYPE_CHECKING:
    from playwright.async_api import Page as PlaywrightPageType


_debug = get_debug("web:playwright:page")


class PlaywrightPage(AbstractWebPage):
    """
    Playwright页面封装
    
    封装Playwright的Page对象，提供统一的接口
    """
    
    def __init__(
        self,
        page: "PlaywrightPageType",
        wait_for_navigation_timeout: int = DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
        wait_for_network_idle_timeout: int = DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
    ):
        self._page = page
        self._wait_for_navigation_timeout = wait_for_navigation_timeout
        self._wait_for_network_idle_timeout = wait_for_network_idle_timeout
        self._viewport_size: Optional[Size] = None
        self._ever_moved = False
    
    @property
    def interface_type(self) -> str:
        return "playwright"
    
    @property
    def underlying_page(self) -> "PlaywrightPageType":
        """获取底层Playwright页面对象"""
        return self._page
    
    def action_space(self) -> list[DeviceAction]:
        """获取支持的动作空间"""
        from mspy.web.actions import create_web_actions
        return create_web_actions(self)
    
    # ========== 基础方法 ==========
    
    async def evaluate_javascript(self, script: str) -> Any:
        """执行JavaScript"""
        return await self._page.evaluate(script)
    
    async def wait_for_navigation(self) -> None:
        """等待导航完成"""
        if self._wait_for_navigation_timeout == 0:
            _debug("waitForNavigation timeout is 0, skip waiting")
            return
        
        _debug("waitForNavigation begin")
        try:
            await self._page.wait_for_selector(
                "html",
                timeout=self._wait_for_navigation_timeout
            )
        except Exception as e:
            print(
                "[midscene:warning] Waiting for navigation has timed out, "
                "but Midscene will continue execution."
            )
        _debug("waitForNavigation end")
    
    async def wait_for_network_idle(self, timeout: Optional[int] = None) -> None:
        """等待网络空闲"""
        timeout = timeout or self._wait_for_network_idle_timeout
        if timeout == 0:
            _debug("waitForNetworkIdle timeout is 0, skip waiting")
            return
        
        try:
            await self._page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            print(
                "[midscene:warning] Waiting for network idle has timed out, "
                "but Midscene will continue execution."
            )
    
    # ========== 截图和尺寸 ==========
    
    async def screenshot_base64(self) -> str:
        """获取页面截图的Base64编码"""
        await self.wait_for_navigation()
        _debug("screenshot_base64 begin")
        
        buffer = await self._page.screenshot(
            type="jpeg",
            quality=90,
            timeout=10000
        )
        
        import base64
        base64_str = base64.b64encode(buffer).decode("utf-8")
        
        _debug("screenshot_base64 end")
        return create_img_base64_by_format(buffer, "jpeg")
    
    async def size(self) -> Size:
        """获取页面尺寸"""
        if self._viewport_size:
            return self._viewport_size
        
        size_info = await self._page.evaluate("""() => ({
            width: document.documentElement.clientWidth,
            height: document.documentElement.clientHeight,
            dpr: window.devicePixelRatio
        })""")
        
        self._viewport_size = Size(
            width=size_info["width"],
            height=size_info["height"],
            dpr=size_info.get("dpr")
        )
        return self._viewport_size
    
    async def url(self) -> str:
        """获取当前URL"""
        return self._page.url
    
    def describe(self) -> str:
        """获取页面描述"""
        return self._page.url or ""
    
    # ========== 鼠标操作 ==========
    
    @property
    def mouse(self):
        """鼠标动作"""
        page = self._page
        parent = self
        
        class PlaywrightMouse:
            async def click(
                self,
                x: int,
                y: int,
                button: str = "left",
                count: int = 1
            ) -> None:
                await self.move(x, y)
                _debug(f"mouse click {x}, {y}, {button}, {count}")
                
                if count == 2:
                    await page.mouse.dblclick(x, y, button=button)
                else:
                    await page.mouse.click(x, y, button=button, click_count=count)
            
            async def wheel(self, delta_x: int, delta_y: int) -> None:
                _debug(f"mouse wheel {delta_x}, {delta_y}")
                await page.mouse.wheel(delta_x, delta_y)
            
            async def move(self, x: int, y: int) -> None:
                parent._ever_moved = True
                _debug(f"mouse move to {x}, {y}")
                await page.mouse.move(x, y)
            
            async def drag(
                self,
                from_pos: Tuple[int, int],
                to_pos: Tuple[int, int]
            ) -> None:
                _debug(f"begin mouse drag from {from_pos} to {to_pos}")
                await page.mouse.move(from_pos[0], from_pos[1])
                await asyncio.sleep(0.2)
                await page.mouse.down()
                await asyncio.sleep(0.3)
                await page.mouse.move(to_pos[0], to_pos[1], steps=20)
                await asyncio.sleep(0.5)
                await page.mouse.up()
                await asyncio.sleep(0.2)
                _debug(f"end mouse drag from {from_pos} to {to_pos}")
        
        return PlaywrightMouse()
    
    @property
    def keyboard(self):
        """键盘动作"""
        page = self._page
        
        class PlaywrightKeyboard:
            async def type_text(self, text: str) -> None:
                _debug(f"keyboard type {text}")
                await page.keyboard.type(text, delay=80)
            
            async def press(self, action) -> None:
                keys = action if isinstance(action, list) else [action]
                _debug(f"keyboard press {keys}")
                
                for k in keys:
                    key = k.key if hasattr(k, 'key') else k.get('key', k)
                    await page.keyboard.down(key)
                
                for k in reversed(keys):
                    key = k.key if hasattr(k, 'key') else k.get('key', k)
                    await page.keyboard.up(key)
            
            async def down(self, key: str) -> None:
                _debug(f"keyboard down {key}")
                await page.keyboard.down(key)
            
            async def up(self, key: str) -> None:
                _debug(f"keyboard up {key}")
                await page.keyboard.up(key)
        
        return PlaywrightKeyboard()
    
    async def clear_input(self, element: Any) -> None:
        """清除输入框"""
        if not element:
            print("Warning: No element to clear input")
            return
        
        center = element.get("center", [0, 0])
        is_mac = platform.system() == "Darwin"
        
        _debug("clearInput begin")
        await self.mouse.click(center[0], center[1])
        
        if is_mac:
            await self._page.keyboard.down("Meta")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Meta")
        else:
            await self._page.keyboard.down("Control")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Control")
        
        await asyncio.sleep(0.1)
        await self._page.keyboard.press("Backspace")
        _debug("clearInput end")
    
    # ========== 滚动操作 ==========
    
    async def _move_to_point_before_scroll(self, point: Optional[Point] = None) -> None:
        """滚动前移动鼠标到指定点"""
        if point:
            await self.mouse.move(point.left, point.top)
        elif not self._ever_moved:
            size = await self.size()
            target_x = size.width // 2
            target_y = size.height // 2
            await self.mouse.move(target_x, target_y)
    
    async def scroll_until_top(self, starting_point: Optional[Point] = None) -> None:
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(0, -9999999)
    
    async def scroll_until_bottom(self, starting_point: Optional[Point] = None) -> None:
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(0, 9999999)
    
    async def scroll_until_left(self, starting_point: Optional[Point] = None) -> None:
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(-9999999, 0)
    
    async def scroll_until_right(self, starting_point: Optional[Point] = None) -> None:
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(9999999, 0)
    
    async def scroll_up(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(0, -scroll_distance)
    
    async def scroll_down(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(0, scroll_distance)
    
    async def scroll_left(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(-scroll_distance, 0)
    
    async def scroll_right(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse.wheel(scroll_distance, 0)
    
    # ========== 触摸操作 ==========
    
    async def long_press(
        self,
        x: int,
        y: int,
        duration: Optional[int] = None
    ) -> None:
        duration = duration or 500
        duration = max(300, min(duration, 600))  # 限制范围
        
        _debug(f"mouse longPress at {x}, {y} for {duration}ms")
        await self._page.mouse.move(x, y)
        await self._page.mouse.down(button="left")
        await asyncio.sleep(duration / 1000)
        await self._page.mouse.up(button="left")
    
    async def swipe(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        duration: Optional[int] = None
    ) -> None:
        duration = duration or 100
        duration = max(150, min(duration, 500))  # 限制范围
        
        _debug(f"mouse swipe from {from_pos} to {to_pos} with duration {duration}ms")
        
        await self._page.mouse.move(from_pos[0], from_pos[1])
        await self._page.mouse.down()
        
        steps = 30
        delay = duration / steps / 1000
        
        for i in range(1, steps + 1):
            x = from_pos[0] + (to_pos[0] - from_pos[0]) * (i / steps)
            y = from_pos[1] + (to_pos[1] - from_pos[1]) * (i / steps)
            await self._page.mouse.move(x, y)
            await asyncio.sleep(delay)
        
        await self._page.mouse.up(button="left")
    
    # ========== 导航操作 ==========
    
    async def navigate(self, url: str) -> None:
        _debug(f"navigate to {url}")
        await self._page.goto(url)
    
    async def reload(self) -> None:
        _debug("reload page")
        await self._page.reload()
    
    async def go_back(self) -> None:
        _debug("go back")
        await self._page.go_back()
    
    # ========== UI上下文 ==========
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        screenshot = await self.screenshot_base64()
        size = await self.size()
        
        return UIContext(
            screenshot_base64=screenshot,
            size=size,
        )
    
    async def destroy(self) -> None:
        """销毁页面"""
        pass
