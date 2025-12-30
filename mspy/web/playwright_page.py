"""
Playwright Web Page - Playwright 网页封装
提供 Playwright 页面的基础操作
"""

import asyncio
import base64
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from playwright.async_api import Page as PlaywrightPage

from mspy.shared.types import DeviceAction, LocateResultElement, Rect, Size, Point
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition
from mspy.core.agent import AbstractInterface


debug = get_debug("web:page")


# 鼠标按钮类型
MouseButton = str  # 'left' | 'right' | 'middle'


class PlaywrightWebPage(AbstractInterface):
    """
    Playwright 网页封装
    提供基于 Playwright 的页面操作
    """
    
    def __init__(
        self,
        page: PlaywrightPage,
        opts: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化 Playwright 页面
        
        Args:
            page: Playwright 页面对象
            opts: 可选配置
        """
        self._page = page
        self._opts = opts or {}
    
    @property
    def interface_type(self) -> str:
        """接口类型"""
        return "playwright"
    
    @property
    def underlying_page(self) -> PlaywrightPage:
        """获取底层 Playwright 页面"""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """
        获取页面截图的 base64 编码
        
        Returns:
            base64 编码的截图
        """
        screenshot_bytes = await self._page.screenshot(type="png")
        base64_str = base64.b64encode(screenshot_bytes).decode("utf-8")
        return f"data:image/png;base64,{base64_str}"
    
    async def size(self) -> Size:
        """
        获取页面尺寸
        
        Returns:
            页面尺寸
        """
        viewport = self._page.viewport_size
        if viewport:
            return Size(width=viewport["width"], height=viewport["height"])
        
        # 如果没有 viewport，获取实际页面尺寸
        dimensions = await self._page.evaluate("""
            () => ({
                width: window.innerWidth,
                height: window.innerHeight
            })
        """)
        return Size(width=dimensions["width"], height=dimensions["height"])
    
    async def navigate(self, url: str) -> None:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
        """
        await self._page.goto(url)
    
    async def reload(self) -> None:
        """重新加载页面"""
        await self._page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        await self._page.go_back()
    
    async def url(self) -> str:
        """获取当前 URL"""
        return self._page.url
    
    async def mouse_click(
        self,
        x: float,
        y: float,
        button: MouseButton = "left",
        count: int = 1,
    ) -> None:
        """
        鼠标点击
        
        Args:
            x: X 坐标
            y: Y 坐标
            button: 鼠标按钮
            count: 点击次数
        """
        await self._page.mouse.click(x, y, button=button, click_count=count)
    
    async def mouse_move(self, x: float, y: float) -> None:
        """
        移动鼠标
        
        Args:
            x: X 坐标
            y: Y 坐标
        """
        await self._page.mouse.move(x, y)
    
    async def mouse_wheel(self, delta_x: float, delta_y: float) -> None:
        """
        滚动鼠标滚轮
        
        Args:
            delta_x: X 方向滚动量
            delta_y: Y 方向滚动量
        """
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def mouse_drag(
        self,
        from_point: Dict[str, float],
        to_point: Dict[str, float],
    ) -> None:
        """
        拖拽操作
        
        Args:
            from_point: 起始点 {x, y}
            to_point: 结束点 {x, y}
        """
        await self._page.mouse.move(from_point["x"], from_point["y"])
        await self._page.mouse.down()
        await self._page.mouse.move(to_point["x"], to_point["y"])
        await self._page.mouse.up()
    
    async def keyboard_type(self, text: str) -> None:
        """
        键盘输入文本
        
        Args:
            text: 输入文本
        """
        await self._page.keyboard.type(text)
    
    async def keyboard_press(self, key: str) -> None:
        """
        按下键盘按键
        
        Args:
            key: 按键名称
        """
        await self._page.keyboard.press(key)
    
    async def clear_input(self, element: Optional[LocateResultElement] = None) -> None:
        """
        清除输入框内容
        
        Args:
            element: 目标元素（可选）
        """
        if element:
            await self.mouse_click(element.center[0], element.center[1])
        
        # 全选并删除
        await self._page.keyboard.press("Control+A")
        await self._page.keyboard.press("Backspace")
    
    async def scroll_up(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None,
    ) -> None:
        """
        向上滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始点
        """
        scroll_distance = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(0, -scroll_distance)
    
    async def scroll_down(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None,
    ) -> None:
        """
        向下滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始点
        """
        scroll_distance = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(0, scroll_distance)
    
    async def scroll_left(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None,
    ) -> None:
        """
        向左滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始点
        """
        scroll_distance = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(-scroll_distance, 0)
    
    async def scroll_right(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None,
    ) -> None:
        """
        向右滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始点
        """
        scroll_distance = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.mouse.wheel(scroll_distance, 0)
    
    async def scroll_until_top(self, starting_point: Optional[Point] = None) -> None:
        """滚动到顶部"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.keyboard.press("Home")
    
    async def scroll_until_bottom(self, starting_point: Optional[Point] = None) -> None:
        """滚动到底部"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.keyboard.press("End")
    
    async def scroll_until_left(self, starting_point: Optional[Point] = None) -> None:
        """滚动到最左边"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.evaluate("window.scrollTo(0, window.scrollY)")
    
    async def scroll_until_right(self, starting_point: Optional[Point] = None) -> None:
        """滚动到最右边"""
        if starting_point:
            await self._page.mouse.move(starting_point.left, starting_point.top)
        await self._page.evaluate("window.scrollTo(document.body.scrollWidth, window.scrollY)")
    
    async def long_press(
        self,
        x: float,
        y: float,
        duration: Optional[int] = None,
    ) -> None:
        """
        长按
        
        Args:
            x: X 坐标
            y: Y 坐标
            duration: 持续时间（毫秒）
        """
        press_duration = duration or 500
        await self._page.mouse.move(x, y)
        await self._page.mouse.down()
        await asyncio.sleep(press_duration / 1000)
        await self._page.mouse.up()
    
    async def swipe(
        self,
        from_point: Dict[str, float],
        to_point: Dict[str, float],
        duration: Optional[int] = None,
    ) -> None:
        """
        滑动手势
        
        Args:
            from_point: 起始点 {x, y}
            to_point: 结束点 {x, y}
            duration: 持续时间（毫秒）
        """
        swipe_duration = duration or 300
        steps = max(10, swipe_duration // 16)  # 约 60fps
        
        dx = (to_point["x"] - from_point["x"]) / steps
        dy = (to_point["y"] - from_point["y"]) / steps
        
        await self._page.mouse.move(from_point["x"], from_point["y"])
        await self._page.mouse.down()
        
        for i in range(1, steps + 1):
            await self._page.mouse.move(
                from_point["x"] + dx * i,
                from_point["y"] + dy * i,
            )
            await asyncio.sleep(swipe_duration / steps / 1000)
        
        await self._page.mouse.up()
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行 JavaScript 代码
        
        Args:
            script: JavaScript 代码
            
        Returns:
            执行结果
        """
        return await self._page.evaluate(script)
    
    async def destroy(self) -> None:
        """销毁页面"""
        # Playwright 页面通常由外部管理，这里不主动关闭
        pass
    
    def action_space(self) -> List[DeviceAction]:
        """
        获取动作空间
        
        Returns:
            支持的动作列表
        """
        page = self
        
        return [
            # Tap 动作
            DeviceAction(
                name="Tap",
                description="Tap the element",
                interface_alias="aiTap",
                param_schema={
                    "locate": {
                        "type": "object",
                        "description": "The element to be tapped",
                    },
                },
                call=lambda param: page._action_tap(param),
            ),
            # RightClick 动作
            DeviceAction(
                name="RightClick",
                description="Right click the element",
                interface_alias="aiRightClick",
                param_schema={
                    "locate": {
                        "type": "object",
                        "description": "The element to be right clicked",
                    },
                },
                call=lambda param: page._action_right_click(param),
            ),
            # DoubleClick 动作
            DeviceAction(
                name="DoubleClick",
                description="Double click the element",
                interface_alias="aiDoubleClick",
                param_schema={
                    "locate": {
                        "type": "object",
                        "description": "The element to be double clicked",
                    },
                },
                call=lambda param: page._action_double_click(param),
            ),
            # Hover 动作
            DeviceAction(
                name="Hover",
                description="Move the mouse to the element",
                interface_alias="aiHover",
                param_schema={
                    "locate": {
                        "type": "object",
                        "description": "The element to be hovered",
                    },
                },
                call=lambda param: page._action_hover(param),
            ),
            # Input 动作
            DeviceAction(
                name="Input",
                description="Input the value into the element",
                interface_alias="aiInput",
                param_schema={
                    "value": {
                        "type": "string",
                        "description": "The text to input",
                    },
                    "locate": {
                        "type": "object",
                        "description": "The input field",
                        "optional": True,
                    },
                    "mode": {
                        "type": "string",
                        "description": "Input mode: replace, clear, or append",
                        "optional": True,
                    },
                },
                call=lambda param: page._action_input(param),
            ),
            # KeyboardPress 动作
            DeviceAction(
                name="KeyboardPress",
                description="Press a key or key combination",
                interface_alias="aiKeyboardPress",
                param_schema={
                    "keyName": {
                        "type": "string",
                        "description": "The key to press",
                    },
                    "locate": {
                        "type": "object",
                        "description": "The element to click before pressing",
                        "optional": True,
                    },
                },
                call=lambda param: page._action_keyboard_press(param),
            ),
            # Scroll 动作
            DeviceAction(
                name="Scroll",
                description="Scroll the page or an element",
                interface_alias="aiScroll",
                param_schema={
                    "scrollType": {
                        "type": "string",
                        "description": "Scroll type: singleAction, scrollToBottom, scrollToTop, etc.",
                        "optional": True,
                    },
                    "direction": {
                        "type": "string",
                        "description": "Scroll direction: down, up, left, right",
                        "optional": True,
                    },
                    "distance": {
                        "type": "number",
                        "description": "Scroll distance in pixels",
                        "optional": True,
                    },
                    "locate": {
                        "type": "object",
                        "description": "The element to scroll",
                        "optional": True,
                    },
                },
                call=lambda param: page._action_scroll(param),
            ),
            # Navigate 动作
            DeviceAction(
                name="Navigate",
                description="Navigate the browser to a specified URL",
                param_schema={
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to",
                    },
                },
                call=lambda param: page._action_navigate(param),
            ),
            # Reload 动作
            DeviceAction(
                name="Reload",
                description="Reload the current page",
                call=lambda param: page.reload(),
            ),
            # GoBack 动作
            DeviceAction(
                name="GoBack",
                description="Navigate back in browser history",
                call=lambda param: page.go_back(),
            ),
        ]
    
    # 动作实现方法
    async def _action_tap(self, param: Dict[str, Any]) -> None:
        """执行点击动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot tap")
        await self.mouse_click(element.center[0], element.center[1])
    
    async def _action_right_click(self, param: Dict[str, Any]) -> None:
        """执行右键点击动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot right click")
        await self.mouse_click(element.center[0], element.center[1], button="right")
    
    async def _action_double_click(self, param: Dict[str, Any]) -> None:
        """执行双击动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot double click")
        await self.mouse_click(element.center[0], element.center[1], count=2)
    
    async def _action_hover(self, param: Dict[str, Any]) -> None:
        """执行悬停动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot hover")
        await self.mouse_move(element.center[0], element.center[1])
    
    async def _action_input(self, param: Dict[str, Any]) -> None:
        """执行输入动作"""
        element = param.get("locate")
        value = param.get("value", "")
        mode = param.get("mode", "replace")
        
        if element and mode != "append":
            await self.clear_input(element)
        
        if mode == "clear":
            return
        
        if value:
            await self.keyboard_type(value)
    
    async def _action_keyboard_press(self, param: Dict[str, Any]) -> None:
        """执行按键动作"""
        element = param.get("locate")
        key_name = param.get("keyName", "")
        
        if element:
            await self.mouse_click(element.center[0], element.center[1])
        
        if key_name:
            # 处理组合键 - Playwright 支持 "Control+A" 格式
            # 使用 Playwright 原生的组合键支持
            await self._page.keyboard.press(key_name)
    
    async def _action_scroll(self, param: Dict[str, Any]) -> None:
        """执行滚动动作"""
        element = param.get("locate")
        scroll_type = param.get("scrollType", "singleAction")
        direction = param.get("direction", "down")
        distance = param.get("distance")
        
        starting_point = None
        if element:
            starting_point = Point(left=element.center[0], top=element.center[1])
        
        if scroll_type == "scrollToTop":
            await self.scroll_until_top(starting_point)
        elif scroll_type == "scrollToBottom":
            await self.scroll_until_bottom(starting_point)
        elif scroll_type == "scrollToLeft":
            await self.scroll_until_left(starting_point)
        elif scroll_type == "scrollToRight":
            await self.scroll_until_right(starting_point)
        else:
            # singleAction
            if direction == "up":
                await self.scroll_up(distance, starting_point)
            elif direction == "down":
                await self.scroll_down(distance, starting_point)
            elif direction == "left":
                await self.scroll_left(distance, starting_point)
            elif direction == "right":
                await self.scroll_right(distance, starting_point)
        
        # 等待滚动完成
        await asyncio.sleep(0.5)
    
    async def _action_navigate(self, param: Dict[str, Any]) -> None:
        """执行导航动作"""
        url = param.get("url")
        assert_condition(url, "URL is required for navigation")
        await self.navigate(url)
