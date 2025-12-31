"""
设备抽象接口模块
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from ..shared import (
    Size,
    Rect,
    UIContext,
    DeviceAction,
    LocateResultElement,
)


class AbstractInterface(ABC):
    """设备抽象接口"""
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """接口类型"""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """获取屏幕截图的base64编码"""
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """获取屏幕尺寸"""
        pass
    
    @abstractmethod
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作空间"""
        pass
    
    async def destroy(self) -> None:
        """销毁接口"""
        pass
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """在调用动作之前的钩子"""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """在调用动作之后的钩子"""
        pass
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        screenshot = await self.screenshot_base64()
        size = await self.size()
        return UIContext(
            screenshot_base64=screenshot,
            size=size,
        )


def define_action(
    name: str,
    description: str,
    call: Callable,
    param_schema: Optional[Any] = None,
    interface_alias: Optional[str] = None,
    delay_after_runner: int = 300,
) -> DeviceAction:
    """
    定义设备动作
    
    Args:
        name: 动作名称
        description: 动作描述
        call: 调用函数
        param_schema: 参数schema
        interface_alias: 接口别名
        delay_after_runner: 执行后延迟时间(ms)
    
    Returns:
        DeviceAction实例
    """
    return DeviceAction(
        name=name,
        description=description,
        call=call,
        param_schema=param_schema,
        interface_alias=interface_alias,
        delay_after_runner=delay_after_runner,
    )


def define_action_tap(call: Callable) -> DeviceAction:
    """定义点击动作"""
    return define_action(
        name='Tap',
        description='Tap the element',
        call=call,
        param_schema={'locate': 'MidsceneLocation'},
        interface_alias='aiTap',
    )


def define_action_hover(call: Callable) -> DeviceAction:
    """定义悬停动作"""
    return define_action(
        name='Hover',
        description='Move the mouse to the element',
        call=call,
        param_schema={'locate': 'MidsceneLocation'},
        interface_alias='aiHover',
    )


def define_action_input(call: Callable) -> DeviceAction:
    """定义输入动作"""
    return define_action(
        name='Input',
        description='Input the value into the element',
        call=call,
        param_schema={
            'value': 'string',
            'locate': 'MidsceneLocation (optional)',
            'mode': 'replace | clear | append (optional)',
        },
        interface_alias='aiInput',
    )


def define_action_keyboard_press(call: Callable) -> DeviceAction:
    """定义键盘按键动作"""
    return define_action(
        name='KeyboardPress',
        description='Press a key or key combination',
        call=call,
        param_schema={
            'keyName': 'string',
            'locate': 'MidsceneLocation (optional)',
        },
        interface_alias='aiKeyboardPress',
    )


def define_action_scroll(call: Callable) -> DeviceAction:
    """定义滚动动作"""
    return define_action(
        name='Scroll',
        description='Scroll the page or an element',
        call=call,
        param_schema={
            'scrollType': 'singleAction | scrollToBottom | scrollToTop',
            'direction': 'down | up | right | left',
            'distance': 'number (optional)',
            'locate': 'MidsceneLocation (optional)',
        },
        interface_alias='aiScroll',
    )


def define_action_assert() -> DeviceAction:
    """定义断言动作"""
    from ..shared import get_debug
    
    debug = get_debug('device:common-action')
    
    async def assert_call(param: Dict[str, Any], context: Any = None) -> None:
        result = param.get('result')
        thought = param.get('thought', '')
        condition = param.get('condition', '')
        
        if not isinstance(result, bool):
            raise ValueError(
                f"The result of the assertion must be a boolean, but got: {type(result).__name__}. "
                f"{thought or '(no thought)'}"
            )
        
        debug(f"Assert: {condition}, Thought: {thought}, Result: {result}")
        
        if not result:
            raise AssertionError(
                f"Assertion failed: {thought or '(no thought)'} (Assertion = {condition})"
            )
    
    return define_action(
        name='Print_Assert_Result',
        description='Print the result of the assertion',
        call=assert_call,
        param_schema={
            'condition': 'string',
            'thought': 'string',
            'result': 'boolean',
        },
    )
