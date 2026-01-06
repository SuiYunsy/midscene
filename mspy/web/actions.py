"""
Web动作定义

从 packages/web-integration/src/web-page.ts 的 commonWebActionsForWebPage 迁移
"""

import asyncio
from typing import Any, List

from mspy.core.device.actions import (
    TapParam,
    RightClickParam,
    DoubleClickParam,
    HoverParam,
    InputParam,
    KeyboardPressParam,
    ScrollParam,
    define_action,
)
from mspy.core.types import DeviceAction
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition
from mspy.web.web_page import AbstractWebPage, get_key_commands


_debug = get_debug("web:actions")


def create_web_actions(page: AbstractWebPage) -> List[DeviceAction]:
    """
    创建Web页面的动作列表
    
    Args:
        page: Web页面实例
    
    Returns:
        DeviceAction列表
    """
    actions: List[DeviceAction] = []
    
    # Tap动作
    async def tap_action(param: TapParam) -> None:
        element = param.locate
        assert_condition(element is not None, "Element not found, cannot tap")
        await page.mouse.click(element.center[0], element.center[1])
    
    actions.append(DeviceAction(
        name="Tap",
        description="点击元素",
        call=tap_action,
    ))
    
    # RightClick动作
    async def right_click_action(param: RightClickParam) -> None:
        element = param.locate
        assert_condition(element is not None, "Element not found, cannot right click")
        await page.mouse.click(element.center[0], element.center[1], button="right")
    
    actions.append(DeviceAction(
        name="RightClick",
        description="右键点击元素",
        call=right_click_action,
    ))
    
    # DoubleClick动作
    async def double_click_action(param: DoubleClickParam) -> None:
        element = param.locate
        assert_condition(element is not None, "Element not found, cannot double click")
        await page.mouse.click(element.center[0], element.center[1], count=2)
    
    actions.append(DeviceAction(
        name="DoubleClick",
        description="双击元素",
        call=double_click_action,
    ))
    
    # Hover动作
    async def hover_action(param: HoverParam) -> None:
        element = param.locate
        assert_condition(element is not None, "Element not found, cannot hover")
        await page.mouse.move(element.center[0], element.center[1])
    
    actions.append(DeviceAction(
        name="Hover",
        description="悬停在元素上",
        call=hover_action,
    ))
    
    # Input动作
    async def input_action(param: InputParam) -> None:
        element = param.locate
        
        if element and param.mode != "append":
            await page.clear_input(element)
        
        if param.mode == "clear":
            return
        
        if not param.value:
            return
        
        await page.keyboard.type_text(param.value)
    
    actions.append(DeviceAction(
        name="Input",
        description="在元素中输入文本",
        call=input_action,
    ))
    
    # KeyboardPress动作
    async def keyboard_press_action(param: KeyboardPressParam) -> None:
        element = param.locate
        if element:
            await page.mouse.click(element.center[0], element.center[1])
        
        keys = get_key_commands(param.key_name)
        await page.keyboard.press(keys)
    
    actions.append(DeviceAction(
        name="KeyboardPress",
        description="按下键盘按键",
        call=keyboard_press_action,
    ))
    
    # Scroll动作
    async def scroll_action(param: ScrollParam) -> None:
        element = param.locate
        starting_point = None
        if element:
            from mspy.shared.types import Point
            starting_point = Point(left=element.center[0], top=element.center[1])
        
        scroll_type = param.scroll_type
        
        if scroll_type == "scrollToTop":
            await page.scroll_until_top(starting_point)
        elif scroll_type == "scrollToBottom":
            await page.scroll_until_bottom(starting_point)
        elif scroll_type == "scrollToRight":
            await page.scroll_until_right(starting_point)
        elif scroll_type == "scrollToLeft":
            await page.scroll_until_left(starting_point)
        elif scroll_type == "singleAction" or not scroll_type:
            direction = param.direction or "down"
            distance = param.distance
            
            if direction == "down":
                await page.scroll_down(distance, starting_point)
            elif direction == "up":
                await page.scroll_up(distance, starting_point)
            elif direction == "left":
                await page.scroll_left(distance, starting_point)
            elif direction == "right":
                await page.scroll_right(distance, starting_point)
            else:
                raise ValueError(f"Unknown scroll direction: {direction}")
            
            # 等待滚动完成
            await asyncio.sleep(0.5)
        else:
            raise ValueError(f"Unknown scroll event type: {scroll_type}")
    
    actions.append(DeviceAction(
        name="Scroll",
        description="滚动页面或元素",
        call=scroll_action,
    ))
    
    # Navigate动作
    async def navigate_action(param: dict) -> None:
        url = param.get("url", "")
        if not hasattr(page, "navigate") or not page.navigate:
            raise NotImplementedError("Navigate operation is not supported on this page type")
        await page.navigate(url)
    
    actions.append(DeviceAction(
        name="Navigate",
        description="导航到指定URL",
        call=navigate_action,
    ))
    
    # Reload动作
    async def reload_action(param: Any = None) -> None:
        if not hasattr(page, "reload") or not page.reload:
            raise NotImplementedError("Reload operation is not supported on this page type")
        await page.reload()
    
    actions.append(DeviceAction(
        name="Reload",
        description="重新加载页面",
        call=reload_action,
    ))
    
    # GoBack动作
    async def go_back_action(param: Any = None) -> None:
        if not hasattr(page, "go_back") or not page.go_back:
            raise NotImplementedError("GoBack operation is not supported on this page type")
        await page.go_back()
    
    actions.append(DeviceAction(
        name="GoBack",
        description="返回上一页",
        call=go_back_action,
    ))
    
    return actions
