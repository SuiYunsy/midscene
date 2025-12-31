"""
Playwright页面封装

提供Playwright页面的抽象接口实现。
"""

import asyncio
import base64
import logging
from typing import Optional, Any, Dict, List, Callable, Awaitable

from playwright.async_api import Page as PlaywrightPageType

from mspy.core.device import AbstractInterface, DeviceAction
from mspy.core.types import UIContext, WebUIContext, ExecutionTask
from mspy.shared.types import Size, Rect, Point
from mspy.shared.constants import (
    DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
    DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
)
from mspy.shared.logger import get_debug

logger = logging.getLogger("midscene.web")
debug_page = get_debug("web:page")


class PlaywrightPage(AbstractInterface):
    """
    Playwright页面封装
    
    实现AbstractInterface接口，提供Playwright页面的自动化能力。
    """
    
    def __init__(
        self,
        page: PlaywrightPageType,
        opts: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Playwright页面
        
        Args:
            page: Playwright页面实例
            opts: 选项配置
        """
        self.underlying_page = page
        self.opts = opts or {}
        
        self.wait_for_navigation_timeout = self.opts.get(
            "wait_for_navigation_timeout",
            DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
        )
        self.wait_for_network_idle_timeout = self.opts.get(
            "wait_for_network_idle_timeout",
            DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
        )
        
        self._viewport_size: Optional[Size] = None
        self._custom_actions: List[DeviceAction] = self.opts.get("custom_actions", [])
        
        # 生命周期钩子
        self.before_invoke_action = self.opts.get("before_invoke_action")
        self.after_invoke_action = self.opts.get("after_invoke_action")
    
    @property
    def interface_type(self) -> str:
        return "playwright"
    
    def action_space(self) -> List[DeviceAction]:
        """获取设备支持的操作列表"""
        from mspy.web.playwright.actions import create_playwright_actions
        
        default_actions = create_playwright_actions(self)
        return default_actions + self._custom_actions
    
    async def screenshot_base64(self) -> str:
        """获取屏幕截图"""
        debug_page("Taking screenshot")
        
        screenshot_bytes = await self.underlying_page.screenshot(type="png")
        base64_str = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        return f"data:image/png;base64,{base64_str}"
    
    async def size(self) -> Dict[str, Any]:
        """获取屏幕尺寸"""
        viewport = self.underlying_page.viewport_size
        
        if viewport:
            return {
                "width": viewport["width"],
                "height": viewport["height"],
            }
        
        # 如果没有viewport，尝试从页面获取
        size = await self.underlying_page.evaluate(
            "() => ({ width: window.innerWidth, height: window.innerHeight })"
        )
        
        return size
    
    async def get_context(self) -> Optional[UIContext]:
        """获取UI上下文"""
        screenshot = await self.screenshot_base64()
        size_dict = await self.size()
        size = Size(width=size_dict["width"], height=size_dict["height"])
        
        return WebUIContext(screenshot_base64=screenshot, size=size)
    
    async def evaluate_javascript(self, script: str) -> Any:
        """执行JavaScript代码"""
        debug_page("Evaluating JavaScript")
        return await self.underlying_page.evaluate(script)
    
    async def wait_for_navigation(self) -> None:
        """等待页面导航完成"""
        if self.wait_for_navigation_timeout == 0:
            debug_page("waitForNavigation timeout is 0, skip waiting")
            return
        
        try:
            debug_page(f"Waiting for navigation (timeout: {self.wait_for_navigation_timeout}ms)")
            # 使用wait_for_load_state等待页面加载完成
            await self.underlying_page.wait_for_load_state(
                "load",
                timeout=self.wait_for_navigation_timeout,
            )
        except Exception as e:
            logger.warning(
                "[midscene:warning] Waiting for navigation timed out, but continuing execution. "
                "See https://midscenejs.com/faq.html#customize-the-network-timeout"
            )
    
    async def destroy(self) -> None:
        """销毁页面"""
        # 页面生命周期由外部管理
        pass
    
    # 便捷方法
    
    async def click(self, x: float, y: float) -> None:
        """点击指定位置"""
        await self.underlying_page.mouse.click(x, y)
    
    async def double_click(self, x: float, y: float) -> None:
        """双击指定位置"""
        await self.underlying_page.mouse.dblclick(x, y)
    
    async def right_click(self, x: float, y: float) -> None:
        """右键点击指定位置"""
        await self.underlying_page.mouse.click(x, y, button="right")
    
    async def hover(self, x: float, y: float) -> None:
        """悬停到指定位置"""
        await self.underlying_page.mouse.move(x, y)
    
    async def type_text(self, text: str) -> None:
        """输入文本"""
        await self.underlying_page.keyboard.type(text)
    
    async def press_key(self, key: str) -> None:
        """按下按键"""
        await self.underlying_page.keyboard.press(key)
    
    async def scroll(
        self,
        x: float,
        y: float,
        delta_x: float = 0,
        delta_y: float = 0,
    ) -> None:
        """滚动"""
        await self.underlying_page.mouse.move(x, y)
        await self.underlying_page.mouse.wheel(delta_x, delta_y)
    
    async def clear_input(self, x: float, y: float) -> None:
        """清空输入框"""
        await self.underlying_page.mouse.click(x, y)
        await self.underlying_page.keyboard.press("Control+a")
        await self.underlying_page.keyboard.press("Backspace")
