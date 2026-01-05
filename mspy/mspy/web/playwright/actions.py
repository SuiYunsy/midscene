"""
Playwright操作定义

定义Playwright页面可执行的操作。
"""

from typing import Any, Dict, List, Optional

from mspy.core.device import DeviceAction
from mspy.core.types import ExecutionTask
from mspy.shared.logger import get_debug

debug = get_debug("web:actions")


def create_playwright_actions(page: Any) -> List[DeviceAction]:
    """
    创建Playwright操作列表
    
    Args:
        page: PlaywrightPage实例
        
    Returns:
        操作列表
    """
    
    async def tap_action(param: Dict[str, Any], context: Any) -> None:
        """点击操作"""
        element = param.get("_element")
        
        if element:
            x, y = element.center
            debug(f"Tapping at ({x}, {y})")
            await page.click(x, y)
        else:
            debug("No element found for tap")
    
    async def double_click_action(param: Dict[str, Any], context: Any) -> None:
        """双击操作"""
        element = param.get("_element")
        
        if element:
            x, y = element.center
            debug(f"Double clicking at ({x}, {y})")
            await page.double_click(x, y)
    
    async def right_click_action(param: Dict[str, Any], context: Any) -> None:
        """右键点击操作"""
        element = param.get("_element")
        
        if element:
            x, y = element.center
            debug(f"Right clicking at ({x}, {y})")
            await page.right_click(x, y)
    
    async def hover_action(param: Dict[str, Any], context: Any) -> None:
        """悬停操作"""
        element = param.get("_element")
        
        if element:
            x, y = element.center
            debug(f"Hovering at ({x}, {y})")
            await page.hover(x, y)
    
    async def input_action(param: Dict[str, Any], context: Any) -> None:
        """输入操作"""
        element = param.get("_element")
        value = param.get("value", "")
        mode = param.get("mode", "replace")
        
        if element:
            x, y = element.center
            debug(f"Input '{value}' at ({x}, {y}), mode={mode}")
            
            # 点击输入框
            await page.click(x, y)
            
            # 根据模式处理
            if mode == "replace":
                await page.clear_input(x, y)
            elif mode == "clear":
                await page.clear_input(x, y)
                return
            
            # 输入文本
            if value:
                await page.type_text(value)
    
    async def keyboard_press_action(param: Dict[str, Any], context: Any) -> None:
        """按键操作"""
        key_name = param.get("keyName", param.get("key_name", ""))
        element = param.get("_element")
        
        if element:
            x, y = element.center
            await page.click(x, y)
        
        if key_name:
            debug(f"Pressing key: {key_name}")
            await page.press_key(key_name)
    
    async def scroll_action(param: Dict[str, Any], context: Any) -> None:
        """滚动操作"""
        element = param.get("_element")
        direction = param.get("direction", "down")
        distance = param.get("distance", 300)
        
        # 确定滚动位置
        if element:
            x, y = element.center
        else:
            # 默认在页面中心滚动
            size = await page.size()
            x = size["width"] / 2
            y = size["height"] / 2
        
        # 计算滚动偏移
        delta_x = 0
        delta_y = 0
        
        if direction == "down":
            delta_y = distance
        elif direction == "up":
            delta_y = -distance
        elif direction == "right":
            delta_x = distance
        elif direction == "left":
            delta_x = -distance
        
        debug(f"Scrolling at ({x}, {y}), delta=({delta_x}, {delta_y})")
        await page.scroll(x, y, delta_x, delta_y)
    
    async def assert_action(param: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """断言操作（由Agent处理）"""
        # 这个操作主要用于记录，实际断言由Agent处理
        return {"pass": True}
    
    return [
        DeviceAction(
            name="Tap",
            interface_alias="aiTap",
            description="Click/tap on an element",
            call=tap_action,
        ),
        DeviceAction(
            name="DoubleClick",
            interface_alias="aiDoubleClick",
            description="Double click on an element",
            call=double_click_action,
        ),
        DeviceAction(
            name="RightClick",
            interface_alias="aiRightClick",
            description="Right click on an element",
            call=right_click_action,
        ),
        DeviceAction(
            name="Hover",
            interface_alias="aiHover",
            description="Hover over an element",
            call=hover_action,
        ),
        DeviceAction(
            name="Input",
            interface_alias="aiInput",
            description="Input text into an element",
            call=input_action,
        ),
        DeviceAction(
            name="KeyboardPress",
            interface_alias="aiKeyboardPress",
            description="Press a keyboard key",
            call=keyboard_press_action,
        ),
        DeviceAction(
            name="Scroll",
            interface_alias="aiScroll",
            description="Scroll the page or an element",
            call=scroll_action,
        ),
        DeviceAction(
            name="Assert",
            interface_alias="aiAssert",
            description="Assert a condition",
            call=assert_action,
        ),
    ]
