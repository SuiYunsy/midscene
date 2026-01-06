"""
Playwright页面封装

对应TypeScript源码: packages/web-integration/src/playwright/page.ts
"""

import asyncio
import base64
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from mspy.shared.types import Rect, Size, Point
from mspy.shared.logger import get_debug
from mspy.core.types import UIContext, DeviceAction
from mspy.core.device import AbstractInterface
from mspy.web.web_page import AbstractWebPage, KeyInput

debug = get_debug('web:playwright:page')


@dataclass
class WebPageOpt:
    """Web页面选项"""
    wait_for_navigation_timeout: int = 30000
    wait_for_network_idle_timeout: int = 10000
    force_same_tab_navigation: bool = True
    enable_touch_events_in_action_space: bool = False
    force_chrome_select_rendering: bool = False
    before_invoke_action: Optional[Callable] = None
    after_invoke_action: Optional[Callable] = None
    custom_actions: Optional[List[DeviceAction]] = None


class SimpleUIContext(UIContext):
    """简单的UI上下文实现"""
    
    def __init__(self, screenshot_base64: str, size: Size):
        self._screenshot_base64 = screenshot_base64
        self._size = size
        self._is_frozen = False
    
    @property
    def screenshot_base64(self) -> str:
        return self._screenshot_base64
    
    @property
    def size(self) -> Size:
        return self._size


class WebPage(AbstractWebPage):
    """Playwright页面封装类
    
    封装Playwright Page对象，提供Midscene所需的接口
    """
    
    def __init__(self, page: Any, opts: Optional[WebPageOpt] = None):
        """初始化WebPage
        
        Args:
            page: Playwright Page对象
            opts: 页面选项
        """
        self._page = page
        self._opts = opts or WebPageOpt()
        self._interface_type = "playwright"
    
    @property
    def interface_type(self) -> str:
        return self._interface_type
    
    @property
    def page(self) -> Any:
        """获取原始Playwright Page对象"""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """获取页面截图的Base64编码"""
        screenshot_bytes = await self._page.screenshot(
            type='png',
            full_page=False
        )
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def size(self) -> Size:
        """获取页面尺寸"""
        viewport = self._page.viewport_size
        if viewport:
            return Size(width=viewport['width'], height=viewport['height'])
        
        # 如果没有viewport，获取document尺寸
        size = await self._page.evaluate('''
            () => ({
                width: document.documentElement.clientWidth,
                height: document.documentElement.clientHeight
            })
        ''')
        return Size(width=size['width'], height=size['height'])
    
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作空间"""
        from mspy.web.web_page import get_common_web_actions
        actions = get_common_web_actions(self)
        
        # 添加自定义动作
        if self._opts.custom_actions:
            actions.extend(self._opts.custom_actions)
        
        return actions
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        screenshot = await self.screenshot_base64()
        size = await self.size()
        return SimpleUIContext(screenshot, size)
    
    async def url(self) -> str:
        """获取当前URL"""
        return self._page.url
    
    async def navigate(self, url: str) -> None:
        """导航到URL
        
        Args:
            url: 目标URL
        """
        await self._page.goto(url, wait_until='domcontentloaded')
    
    async def reload(self) -> None:
        """重新加载页面"""
        await self._page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        await self._page.go_back()
    
    async def evaluate_javascript(self, script: str) -> Any:
        """执行JavaScript
        
        Args:
            script: JavaScript代码
            
        Returns:
            执行结果
        """
        return await self._page.evaluate(script)
    
    async def destroy(self) -> None:
        """销毁页面"""
        try:
            await self._page.close()
        except Exception:
            pass
    
    # ============ 鼠标操作 ============
    
    async def mouse_click(
        self,
        x: float,
        y: float,
        button: str = 'left',
        count: int = 1
    ) -> None:
        """鼠标点击
        
        Args:
            x: X坐标
            y: Y坐标
            button: 按钮类型 (left/right/middle)
            count: 点击次数
        """
        await self._page.mouse.click(x, y, button=button, click_count=count)
    
    async def mouse_move(self, x: float, y: float) -> None:
        """鼠标移动"""
        await self._page.mouse.move(x, y)
    
    async def mouse_wheel(self, delta_x: float, delta_y: float) -> None:
        """鼠标滚轮"""
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def mouse_drag(
        self,
        from_point: Dict[str, float],
        to_point: Dict[str, float]
    ) -> None:
        """鼠标拖拽"""
        await self._page.mouse.move(from_point['x'], from_point['y'])
        await self._page.mouse.down()
        await self._page.mouse.move(to_point['x'], to_point['y'])
        await self._page.mouse.up()
    
    # ============ 键盘操作 ============
    
    async def keyboard_type(self, text: str) -> None:
        """输入文本"""
        await self._page.keyboard.type(text)
    
    async def keyboard_press(self, key: str) -> None:
        """按下按键"""
        await self._page.keyboard.press(key)
    
    async def keyboard_press_multiple(self, keys: List[Dict[str, str]]) -> None:
        """按下多个按键（组合键）"""
        for key_info in keys:
            key = key_info.get('key', '')
            if key:
                await self._page.keyboard.press(key)
    
    # ============ 滚动操作 ============
    
    async def scroll_up(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向上滚动"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(0, -distance)
    
    async def scroll_down(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向下滚动"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(0, distance)
    
    async def scroll_left(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向左滚动"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(-distance, 0)
    
    async def scroll_right(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向右滚动"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(distance, 0)
    
    async def scroll_until_top(self, starting_point: Optional[Point] = None) -> None:
        """滚动到顶部"""
        await self._page.evaluate('window.scrollTo(0, 0)')
    
    async def scroll_until_bottom(self, starting_point: Optional[Point] = None) -> None:
        """滚动到底部"""
        await self._page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    
    async def scroll_until_left(self, starting_point: Optional[Point] = None) -> None:
        """滚动到最左边"""
        await self._page.evaluate('window.scrollTo(0, window.scrollY)')
    
    async def scroll_until_right(self, starting_point: Optional[Point] = None) -> None:
        """滚动到最右边"""
        await self._page.evaluate('window.scrollTo(document.body.scrollWidth, window.scrollY)')
    
    # ============ 触摸操作 ============
    
    async def long_press(self, x: float, y: float, duration: int = 500) -> None:
        """长按操作"""
        await self._page.mouse.move(x, y)
        await self._page.mouse.down()
        await asyncio.sleep(duration / 1000)
        await self._page.mouse.up()
    
    async def swipe(
        self,
        from_point: Dict[str, float],
        to_point: Dict[str, float],
        duration: int = 300
    ) -> None:
        """滑动操作"""
        steps = max(1, duration // 50)
        dx = (to_point['x'] - from_point['x']) / steps
        dy = (to_point['y'] - from_point['y']) / steps
        
        await self._page.mouse.move(from_point['x'], from_point['y'])
        await self._page.mouse.down()
        
        for i in range(steps):
            await self._page.mouse.move(
                from_point['x'] + dx * (i + 1),
                from_point['y'] + dy * (i + 1)
            )
            await asyncio.sleep(0.05)
        
        await self._page.mouse.up()
    
    # ============ 输入操作 ============
    
    async def clear_input(self, element: Any) -> None:
        """清除输入框内容"""
        if element and hasattr(element, 'center'):
            x, y = element.center
            await self._page.mouse.click(x, y, click_count=3)  # 三击选中全部
            await self._page.keyboard.press('Backspace')
