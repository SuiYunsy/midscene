# -*- coding: utf-8 -*-
"""
Playwright 页面封装
提供对 Playwright Page 对象的封装。
"""

import asyncio
import base64
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from playwright.async_api import Page as PlaywrightPageType

from mspy.shared.types import Rect, Size, LocateResultElement
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

from mspy.core.types import DeviceAction, UIContext

debug = get_debug("web:page")


# 键盘按键映射
KEY_ALIASES = {
    "enter": "Enter",
    "tab": "Tab",
    "escape": "Escape",
    "space": " ",
    "backspace": "Backspace",
    "delete": "Delete",
    "arrowup": "ArrowUp",
    "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "arrowright": "ArrowRight",
    "control": "Control",
    "shift": "Shift",
    "alt": "Alt",
    "meta": "Meta",
}


def normalize_key(key: str) -> str:
    """标准化按键名称"""
    return KEY_ALIASES.get(key.lower(), key)


def get_key_commands(value: str) -> List[Dict[str, Any]]:
    """
    解析键盘命令
    
    Args:
        value: 按键字符串，支持 '+' 组合键
        
    Returns:
        按键命令列表
    """
    # 处理组合键
    if "+" in value:
        keys = [normalize_key(k.strip()) for k in value.split("+")]
    else:
        keys = [normalize_key(value.strip())]
    
    result = []
    has_modifier = any(k in ("Meta", "Control", "Alt", "Shift") for k in keys)
    
    for k in keys:
        command = None
        if has_modifier:
            if k.lower() == "a":
                command = "SelectAll"
            elif k.lower() == "c":
                command = "Copy"
            elif k.lower() == "v":
                command = "Paste"
        
        result.append({"key": k, "command": command} if command else {"key": k})
    
    return result


class SimpleUIContext(UIContext):
    """简单的 UI 上下文实现"""
    
    def __init__(self, screenshot: str, page_size: Size):
        self._screenshot = screenshot
        self._size = page_size
        self._is_frozen = False
    
    @property
    def screenshot_base64(self) -> str:
        return self._screenshot
    
    @property
    def size(self) -> Size:
        return self._size
    
    @property
    def is_frozen(self) -> bool:
        return self._is_frozen


class PlaywrightPage:
    """
    Playwright 页面封装类
    提供对 Playwright Page 对象的高级封装
    """
    
    interface_type = "playwright"
    
    def __init__(self, page: PlaywrightPageType, headless: bool = True):
        """
        初始化 Playwright 页面
        
        Args:
            page: Playwright Page 对象
            headless: 是否为无头模式
        """
        self._page = page
        self._headless = headless
    
    @property
    def page(self) -> PlaywrightPageType:
        """获取原始 Playwright Page 对象"""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """
        获取页面截图的 base64 编码
        
        Returns:
            base64 编码的截图
        """
        screenshot_bytes = await self._page.screenshot(type="png", full_page=False)
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
        
        # 如果没有 viewport，获取页面实际尺寸
        size = await self._page.evaluate("""
            () => ({
                width: window.innerWidth,
                height: window.innerHeight,
                dpr: window.devicePixelRatio
            })
        """)
        return Size(
            width=size["width"],
            height=size["height"],
            dpr=size.get("dpr")
        )
    
    async def get_context(self) -> UIContext:
        """
        获取 UI 上下文
        
        Returns:
            UI 上下文
        """
        screenshot = await self.screenshot_base64()
        page_size = await self.size()
        return SimpleUIContext(screenshot, page_size)
    
    def url(self) -> str:
        """获取当前页面 URL"""
        return self._page.url
    
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
    
    async def go_forward(self) -> None:
        """前进到下一页"""
        await self._page.go_forward()
    
    async def click(self, x: int, y: int, button: str = "left", count: int = 1) -> None:
        """
        点击指定坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
            button: 鼠标按钮 ('left', 'right', 'middle')
            count: 点击次数
        """
        await self._page.mouse.click(x, y, button=button, click_count=count)
    
    async def double_click(self, x: int, y: int) -> None:
        """
        双击指定坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
        """
        await self._page.mouse.dblclick(x, y)
    
    async def move(self, x: int, y: int) -> None:
        """
        移动鼠标到指定坐标
        
        Args:
            x: X 坐标
            y: Y 坐标
        """
        await self._page.mouse.move(x, y)
    
    async def wheel(self, delta_x: int, delta_y: int) -> None:
        """
        滚动鼠标滚轮
        
        Args:
            delta_x: X 方向滚动量
            delta_y: Y 方向滚动量
        """
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def drag(
        self,
        from_pos: Dict[str, int],
        to_pos: Dict[str, int]
    ) -> None:
        """
        拖拽操作
        
        Args:
            from_pos: 起始位置 {'x': int, 'y': int}
            to_pos: 目标位置 {'x': int, 'y': int}
        """
        await self._page.mouse.move(from_pos["x"], from_pos["y"])
        await self._page.mouse.down()
        await self._page.mouse.move(to_pos["x"], to_pos["y"])
        await self._page.mouse.up()
    
    async def type_text(self, text: str) -> None:
        """
        输入文本
        
        Args:
            text: 要输入的文本
        """
        await self._page.keyboard.type(text)
    
    async def press_key(self, key: str) -> None:
        """
        按下键盘按键
        
        Args:
            key: 按键名称
        """
        normalized = normalize_key(key)
        await self._page.keyboard.press(normalized)
    
    async def press_keys(self, keys: List[Dict[str, Any]]) -> None:
        """
        按下多个键（支持组合键）
        
        Args:
            keys: 按键列表
        """
        # 按下所有修饰键
        modifiers = []
        regular_keys = []
        
        for k in keys:
            key = k["key"]
            if key in ("Control", "Shift", "Alt", "Meta"):
                modifiers.append(key)
            else:
                regular_keys.append(k)
        
        # 按下修饰键
        for mod in modifiers:
            await self._page.keyboard.down(mod)
        
        # 按下普通键
        for k in regular_keys:
            await self._page.keyboard.press(k["key"])
        
        # 释放修饰键
        for mod in reversed(modifiers):
            await self._page.keyboard.up(mod)
    
    async def clear_input(self, element: LocateResultElement) -> None:
        """
        清空输入框
        
        Args:
            element: 目标元素
        """
        # 点击元素
        await self.click(element.center[0], element.center[1])
        
        # 全选并删除
        await self._page.keyboard.press("Control+a")
        await self._page.keyboard.press("Backspace")
    
    async def scroll_up(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """
        向上滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始位置
        """
        d = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point["left"], starting_point["top"])
        await self._page.mouse.wheel(0, -d)
    
    async def scroll_down(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """
        向下滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始位置
        """
        d = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point["left"], starting_point["top"])
        await self._page.mouse.wheel(0, d)
    
    async def scroll_left(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """
        向左滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始位置
        """
        d = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point["left"], starting_point["top"])
        await self._page.mouse.wheel(-d, 0)
    
    async def scroll_right(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """
        向右滚动
        
        Args:
            distance: 滚动距离
            starting_point: 起始位置
        """
        d = distance or 300
        if starting_point:
            await self._page.mouse.move(starting_point["left"], starting_point["top"])
        await self._page.mouse.wheel(d, 0)
    
    async def scroll_until_top(
        self,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """滚动到顶部"""
        await self._page.evaluate("window.scrollTo(0, 0)")
    
    async def scroll_until_bottom(
        self,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """滚动到底部"""
        await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    async def scroll_until_left(
        self,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """滚动到最左边"""
        await self._page.evaluate("window.scrollTo(0, window.scrollY)")
    
    async def scroll_until_right(
        self,
        starting_point: Optional[Dict[str, int]] = None
    ) -> None:
        """滚动到最右边"""
        await self._page.evaluate("window.scrollTo(document.body.scrollWidth, window.scrollY)")
    
    async def long_press(self, x: int, y: int, duration: int = 500) -> None:
        """
        长按
        
        Args:
            x: X 坐标
            y: Y 坐标
            duration: 持续时间（毫秒）
        """
        await self._page.mouse.move(x, y)
        await self._page.mouse.down()
        await asyncio.sleep(duration / 1000)
        await self._page.mouse.up()
    
    async def swipe(
        self,
        from_pos: Dict[str, int],
        to_pos: Dict[str, int],
        duration: int = 300
    ) -> None:
        """
        滑动
        
        Args:
            from_pos: 起始位置 {'x': int, 'y': int}
            to_pos: 目标位置 {'x': int, 'y': int}
            duration: 持续时间（毫秒）
        """
        steps = max(1, duration // 16)  # 约 60fps
        
        await self._page.mouse.move(from_pos["x"], from_pos["y"])
        await self._page.mouse.down()
        
        for i in range(1, steps + 1):
            progress = i / steps
            current_x = from_pos["x"] + (to_pos["x"] - from_pos["x"]) * progress
            current_y = from_pos["y"] + (to_pos["y"] - from_pos["y"]) * progress
            await self._page.mouse.move(current_x, current_y)
            await asyncio.sleep(16 / 1000)
        
        await self._page.mouse.up()
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行 JavaScript
        
        Args:
            script: JavaScript 代码
            
        Returns:
            执行结果
        """
        return await self._page.evaluate(script)
    
    async def destroy(self) -> None:
        """销毁页面"""
        # Playwright 页面不需要手动销毁
        pass
    
    def action_space(self) -> List[DeviceAction]:
        """
        获取动作空间
        
        Returns:
            动作列表
        """
        return [
            DeviceAction(
                name="Tap",
                description="Tap the element",
                interface_alias="aiTap",
                call=self._action_tap,
            ),
            DeviceAction(
                name="RightClick",
                description="Right click the element",
                interface_alias="aiRightClick",
                call=self._action_right_click,
            ),
            DeviceAction(
                name="DoubleClick",
                description="Double click the element",
                interface_alias="aiDoubleClick",
                call=self._action_double_click,
            ),
            DeviceAction(
                name="Hover",
                description="Move the mouse to the element",
                interface_alias="aiHover",
                call=self._action_hover,
            ),
            DeviceAction(
                name="Input",
                description="Input the value into the element",
                interface_alias="aiInput",
                call=self._action_input,
            ),
            DeviceAction(
                name="KeyboardPress",
                description="Press a key or key combination",
                interface_alias="aiKeyboardPress",
                call=self._action_keyboard_press,
            ),
            DeviceAction(
                name="Scroll",
                description="Scroll the page or an element",
                interface_alias="aiScroll",
                call=self._action_scroll,
            ),
            DeviceAction(
                name="Navigate",
                description="Navigate the browser to a specified URL",
                call=self._action_navigate,
            ),
            DeviceAction(
                name="Reload",
                description="Reload the current page",
                call=self._action_reload,
            ),
            DeviceAction(
                name="GoBack",
                description="Navigate back in browser history",
                call=self._action_go_back,
            ),
        ]
    
    async def _action_tap(self, param: Dict[str, Any]) -> None:
        """点击动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot tap")
        await self.click(element.center[0], element.center[1])
    
    async def _action_right_click(self, param: Dict[str, Any]) -> None:
        """右键点击动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot right click")
        await self.click(element.center[0], element.center[1], button="right")
    
    async def _action_double_click(self, param: Dict[str, Any]) -> None:
        """双击动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot double click")
        await self.double_click(element.center[0], element.center[1])
    
    async def _action_hover(self, param: Dict[str, Any]) -> None:
        """悬停动作"""
        element = param.get("locate")
        assert_condition(element, "Element not found, cannot hover")
        await self.move(element.center[0], element.center[1])
    
    async def _action_input(self, param: Dict[str, Any]) -> None:
        """输入动作"""
        element = param.get("locate")
        value = param.get("value", "")
        mode = param.get("mode", "replace")
        
        if element and mode != "append":
            await self.clear_input(element)
        
        if mode == "clear":
            return
        
        if value:
            await self.type_text(str(value))
    
    async def _action_keyboard_press(self, param: Dict[str, Any]) -> None:
        """键盘按键动作"""
        element = param.get("locate")
        key_name = param.get("key_name", param.get("keyName", ""))
        
        if element:
            await self.click(element.center[0], element.center[1])
        
        keys = get_key_commands(key_name)
        await self.press_keys(keys)
    
    async def _action_scroll(self, param: Dict[str, Any]) -> None:
        """滚动动作"""
        element = param.get("locate")
        starting_point = None
        if element:
            starting_point = {
                "left": element.center[0],
                "top": element.center[1],
            }
        
        scroll_type = param.get("scroll_type", param.get("scrollType", "singleAction"))
        direction = param.get("direction", "down")
        distance = param.get("distance")
        
        if scroll_type == "scrollToTop":
            await self.scroll_until_top(starting_point)
        elif scroll_type == "scrollToBottom":
            await self.scroll_until_bottom(starting_point)
        elif scroll_type == "scrollToLeft":
            await self.scroll_until_left(starting_point)
        elif scroll_type == "scrollToRight":
            await self.scroll_until_right(starting_point)
        else:
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
        """导航动作"""
        url = param.get("url")
        assert_condition(url, "URL is required for Navigate action")
        await self.navigate(url)
    
    async def _action_reload(self, param: Dict[str, Any]) -> None:
        """刷新动作"""
        await self.reload()
    
    async def _action_go_back(self, param: Dict[str, Any]) -> None:
        """返回动作"""
        await self.go_back()
