"""
Web页面抽象类

对应TypeScript源码: packages/web-integration/src/web-page.ts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from mspy.shared.types import Point, Rect, Size
from mspy.core.types import DeviceAction
from mspy.core.device import (
    AbstractInterface,
    define_action,
    define_action_tap,
    define_action_right_click,
    define_action_double_click,
    define_action_hover,
    define_action_input,
    define_action_keyboard_press,
    define_action_scroll,
    define_action_drag_and_drop,
    define_action_long_press,
    define_action_swipe,
    define_action_clear_input,
    ActionTapParam,
    ActionRightClickParam,
    ActionDoubleClickParam,
    ActionHoverParam,
    ActionInputParam,
    ActionKeyboardPressParam,
    ActionScrollParam,
    ActionDragAndDropParam,
    ActionLongPressParam,
    ActionSwipeParam,
    ActionClearInputParam,
)
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

debug = get_debug('web:page')

# 键盘输入类型
KeyInput = str  # 简化处理，实际上应该是详细的类型定义


class MouseButton:
    """鼠标按钮类型"""
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


class AbstractWebPage(AbstractInterface, ABC):
    """抽象Web页面类
    
    定义了Web页面必须实现的方法
    """
    
    # 可选的导航方法
    async def navigate(self, url: str) -> None:
        """导航到URL"""
        raise NotImplementedError("此页面类型不支持导航操作")
    
    async def reload(self) -> None:
        """重新加载页面"""
        raise NotImplementedError("此页面类型不支持重新加载")
    
    async def go_back(self) -> None:
        """返回上一页"""
        raise NotImplementedError("此页面类型不支持返回操作")
    
    # 鼠标操作
    async def mouse_click(
        self,
        x: float,
        y: float,
        button: str = 'left',
        count: int = 1
    ) -> None:
        """鼠标点击"""
        pass
    
    async def mouse_move(self, x: float, y: float) -> None:
        """鼠标移动"""
        pass
    
    async def mouse_wheel(self, delta_x: float, delta_y: float) -> None:
        """鼠标滚轮"""
        pass
    
    async def mouse_drag(
        self,
        from_point: Dict[str, float],
        to_point: Dict[str, float]
    ) -> None:
        """鼠标拖拽"""
        pass
    
    # 键盘操作
    async def keyboard_type(self, text: str) -> None:
        """输入文本"""
        pass
    
    async def keyboard_press(self, key: str) -> None:
        """按下按键"""
        pass
    
    async def keyboard_press_multiple(self, keys: List[Dict[str, str]]) -> None:
        """按下多个按键"""
        pass
    
    # 输入操作
    async def clear_input(self, element: Any) -> None:
        """清除输入框内容"""
        pass
    
    # 滚动操作
    @abstractmethod
    async def scroll_until_top(self, starting_point: Optional[Point] = None) -> None:
        """滚动到顶部"""
        pass
    
    @abstractmethod
    async def scroll_until_bottom(self, starting_point: Optional[Point] = None) -> None:
        """滚动到底部"""
        pass
    
    @abstractmethod
    async def scroll_until_left(self, starting_point: Optional[Point] = None) -> None:
        """滚动到最左边"""
        pass
    
    @abstractmethod
    async def scroll_until_right(self, starting_point: Optional[Point] = None) -> None:
        """滚动到最右边"""
        pass
    
    @abstractmethod
    async def scroll_up(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向上滚动"""
        pass
    
    @abstractmethod
    async def scroll_down(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向下滚动"""
        pass
    
    @abstractmethod
    async def scroll_left(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向左滚动"""
        pass
    
    @abstractmethod
    async def scroll_right(self, distance: int = 500, starting_point: Optional[Point] = None) -> None:
        """向右滚动"""
        pass
    
    # 触摸操作
    @abstractmethod
    async def long_press(self, x: float, y: float, duration: int = 500) -> None:
        """长按操作"""
        pass
    
    @abstractmethod
    async def swipe(
        self,
        from_point: Dict[str, float],
        to_point: Dict[str, float],
        duration: int = 300
    ) -> None:
        """滑动操作"""
        pass


def get_common_web_actions(page: AbstractWebPage, include_touch_events: bool = False) -> List[DeviceAction]:
    """获取通用Web动作列表
    
    Args:
        page: Web页面实例
        include_touch_events: 是否包含触摸事件
        
    Returns:
        动作列表
    """
    actions = []
    
    # Tap
    async def tap_handler(param: ActionTapParam):
        element = param.locate
        assert_condition(element, "Element not found, cannot tap")
        await page.mouse_click(element.center[0], element.center[1])
    
    actions.append(define_action_tap(tap_handler))
    
    # RightClick
    async def right_click_handler(param: ActionRightClickParam):
        element = param.locate
        assert_condition(element, "Element not found, cannot right click")
        await page.mouse_click(element.center[0], element.center[1], button='right')
    
    actions.append(define_action_right_click(right_click_handler))
    
    # DoubleClick
    async def double_click_handler(param: ActionDoubleClickParam):
        element = param.locate
        assert_condition(element, "Element not found, cannot double click")
        await page.mouse_click(element.center[0], element.center[1], count=2)
    
    actions.append(define_action_double_click(double_click_handler))
    
    # Hover
    async def hover_handler(param: ActionHoverParam):
        element = param.locate
        assert_condition(element, "Element not found, cannot hover")
        await page.mouse_move(element.center[0], element.center[1])
    
    actions.append(define_action_hover(hover_handler))
    
    # Input
    async def input_handler(param: ActionInputParam):
        element = param.locate
        if element and param.mode != 'append':
            await page.clear_input(element)
        
        if param.mode == 'clear':
            return
        
        if param.value:
            await page.keyboard_type(param.value)
    
    actions.append(define_action_input(input_handler))
    
    # KeyboardPress
    async def keyboard_press_handler(param: ActionKeyboardPressParam):
        element = param.locate
        if element:
            await page.mouse_click(element.center[0], element.center[1])
        
        await page.keyboard_press(param.key_name)
    
    actions.append(define_action_keyboard_press(keyboard_press_handler))
    
    # Scroll
    async def scroll_handler(param: ActionScrollParam):
        element = param.locate
        starting_point = None
        if element:
            starting_point = Point(left=element.center[0], top=element.center[1])
        
        scroll_type = param.scroll_type
        if scroll_type == 'scrollToTop':
            await page.scroll_until_top(starting_point)
        elif scroll_type == 'scrollToBottom':
            await page.scroll_until_bottom(starting_point)
        elif scroll_type == 'scrollToRight':
            await page.scroll_until_right(starting_point)
        elif scroll_type == 'scrollToLeft':
            await page.scroll_until_left(starting_point)
        else:
            direction = param.direction or 'down'
            distance = param.distance or 500
            
            if direction == 'down':
                await page.scroll_down(distance, starting_point)
            elif direction == 'up':
                await page.scroll_up(distance, starting_point)
            elif direction == 'left':
                await page.scroll_left(distance, starting_point)
            elif direction == 'right':
                await page.scroll_right(distance, starting_point)
    
    actions.append(define_action_scroll(scroll_handler))
    
    # DragAndDrop
    async def drag_handler(param: ActionDragAndDropParam):
        from_elem = param.from_element
        to_elem = param.to_element
        assert_condition(from_elem, "missing 'from' param for drag and drop")
        assert_condition(to_elem, "missing 'to' param for drag and drop")
        
        await page.mouse_drag(
            {'x': from_elem.center[0], 'y': from_elem.center[1]},
            {'x': to_elem.center[0], 'y': to_elem.center[1]}
        )
    
    actions.append(define_action_drag_and_drop(drag_handler))
    
    # LongPress
    async def long_press_handler(param: ActionLongPressParam):
        element = param.locate
        assert_condition(element, "Element not found, cannot long press")
        await page.long_press(element.center[0], element.center[1], param.duration)
    
    actions.append(define_action_long_press(long_press_handler))
    
    # ClearInput
    async def clear_input_handler(param: ActionClearInputParam):
        element = param.locate
        assert_condition(element, "Element not found, cannot clear input")
        await page.clear_input(element)
    
    actions.append(define_action_clear_input(clear_input_handler))
    
    # Navigate
    actions.append(define_action(
        name="Navigate",
        description="导航到指定URL",
        call=lambda param: page.navigate(param.get('url', '')),
    ))
    
    # Reload
    actions.append(define_action(
        name="Reload",
        description="重新加载页面",
        call=lambda _: page.reload(),
    ))
    
    # GoBack
    actions.append(define_action(
        name="GoBack",
        description="返回上一页",
        call=lambda _: page.go_back(),
    ))
    
    # Swipe (if touch events enabled)
    if include_touch_events:
        async def swipe_handler(param: ActionSwipeParam):
            size = await page.size()
            
            if param.start:
                start_point = {'x': param.start.center[0], 'y': param.start.center[1]}
            else:
                start_point = {'x': size.width / 2, 'y': size.height / 2}
            
            if param.end:
                end_point = {'x': param.end.center[0], 'y': param.end.center[1]}
            elif param.distance:
                direction = param.direction or 'down'
                dx = param.distance if direction == 'right' else (-param.distance if direction == 'left' else 0)
                dy = param.distance if direction == 'down' else (-param.distance if direction == 'up' else 0)
                end_point = {
                    'x': max(0, min(start_point['x'] + dx, size.width)),
                    'y': max(0, min(start_point['y'] + dy, size.height))
                }
            else:
                raise ValueError("Either end or distance must be specified for swipe gesture")
            
            repeat = param.repeat or 1
            for _ in range(repeat):
                await page.swipe(start_point, end_point, param.duration)
        
        actions.append(define_action_swipe(swipe_handler))
    
    return actions
