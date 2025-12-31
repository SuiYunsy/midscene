# -*- coding: utf-8 -*-
"""
Midscene Device Module
设备抽象接口模块
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from ..shared import Size, Rect, UIContext


class AbstractInterface(ABC):
    """抽象设备接口"""
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """设备接口类型"""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """获取截图的base64编码"""
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """获取页面/屏幕尺寸"""
        pass
    
    @abstractmethod
    def action_space(self) -> List[Dict[str, Any]]:
        """获取可用动作空间"""
        pass
    
    async def destroy(self) -> None:
        """销毁/清理资源"""
        pass
    
    async def describe(self) -> str:
        """描述当前状态"""
        return ""
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """调用动作前的钩子"""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """调用动作后的钩子"""
        pass
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        screenshot = await self.screenshot_base64()
        page_size = await self.size()
        return UIContext(
            screenshot_base64=screenshot,
            size=page_size,
        )


def define_action(
    name: str,
    description: str,
    param_schema: Optional[Dict[str, Any]] = None,
    interface_alias: Optional[str] = None,
    delay_after_runner: int = 300,
) -> Dict[str, Any]:
    """
    定义一个动作
    
    Args:
        name: 动作名称
        description: 动作描述
        param_schema: 参数模式
        interface_alias: 接口别名
        delay_after_runner: 执行后延迟
    
    Returns:
        动作定义字典
    """
    return {
        "name": name,
        "description": description,
        "param_schema": param_schema or {},
        "interface_alias": interface_alias,
        "delay_after_runner": delay_after_runner,
    }


# 预定义的动作模式
def get_locate_param_schema() -> Dict[str, Any]:
    """获取locate参数模式"""
    return {
        "locate": {
            "type": "MidsceneLocation",
            "description": "The element to locate",
            "is_locator": True,
            "optional": False,
        }
    }


def define_action_tap(call: callable) -> Dict[str, Any]:
    """定义Tap动作"""
    return {
        "name": "Tap",
        "description": "Tap the element",
        "interface_alias": "aiTap",
        "param_schema": {
            "locate": {
                "type": "MidsceneLocation",
                "description": "The element to be tapped",
                "is_locator": True,
                "optional": False,
            }
        },
        "call": call,
    }


def define_action_right_click(call: callable) -> Dict[str, Any]:
    """定义RightClick动作"""
    return {
        "name": "RightClick",
        "description": "Right click the element",
        "interface_alias": "aiRightClick",
        "param_schema": {
            "locate": {
                "type": "MidsceneLocation",
                "description": "The element to be right clicked",
                "is_locator": True,
                "optional": False,
            }
        },
        "call": call,
    }


def define_action_double_click(call: callable) -> Dict[str, Any]:
    """定义DoubleClick动作"""
    return {
        "name": "DoubleClick",
        "description": "Double click the element",
        "interface_alias": "aiDoubleClick",
        "param_schema": {
            "locate": {
                "type": "MidsceneLocation",
                "description": "The element to be double clicked",
                "is_locator": True,
                "optional": False,
            }
        },
        "call": call,
    }


def define_action_hover(call: callable) -> Dict[str, Any]:
    """定义Hover动作"""
    return {
        "name": "Hover",
        "description": "Move the mouse to the element",
        "interface_alias": "aiHover",
        "param_schema": {
            "locate": {
                "type": "MidsceneLocation",
                "description": "The element to be hovered",
                "is_locator": True,
                "optional": False,
            }
        },
        "call": call,
    }


def define_action_input(call: callable) -> Dict[str, Any]:
    """定义Input动作"""
    return {
        "name": "Input",
        "description": "Input the value into the element",
        "interface_alias": "aiInput",
        "param_schema": {
            "value": {
                "type": "string",
                "description": "The text to input. Provide the final content for replace/append modes, or an empty string when using clear mode to remove existing text.",
                "optional": False,
            },
            "locate": {
                "type": "MidsceneLocation",
                "description": "the position of the placeholder or text content in the target input field",
                "is_locator": True,
                "optional": True,
            },
            "mode": {
                "type": "enum",
                "values": ["replace", "clear", "append"],
                "description": 'Input mode: "replace" (default) - clear the field and input the value; "append" - append the value to existing content; "clear" - clear the field without inputting new text.',
                "optional": True,
            },
        },
        "call": call,
    }


def define_action_keyboard_press(call: callable) -> Dict[str, Any]:
    """定义KeyboardPress动作"""
    return {
        "name": "KeyboardPress",
        "description": 'Press a key or key combination, like "Enter", "Tab", "Escape", or "Control+A", "Shift+Enter". Do not use this to type text.',
        "interface_alias": "aiKeyboardPress",
        "param_schema": {
            "locate": {
                "type": "MidsceneLocation",
                "description": "The element to be clicked before pressing the key",
                "is_locator": True,
                "optional": True,
            },
            "keyName": {
                "type": "string",
                "description": "The key to be pressed. Use '+' for key combinations, e.g., 'Control+A', 'Shift+Enter'",
                "optional": False,
            },
        },
        "call": call,
    }


def define_action_scroll(call: callable) -> Dict[str, Any]:
    """定义Scroll动作"""
    return {
        "name": "Scroll",
        "description": "Scroll the page or an element. The direction to scroll, the scroll type, and the distance to scroll. The distance is the number of pixels to scroll. If not specified, use `down` direction, `once` scroll type, and `null` distance.",
        "interface_alias": "aiScroll",
        "param_schema": {
            "scrollType": {
                "type": "enum",
                "values": ["singleAction", "scrollToBottom", "scrollToTop", "scrollToRight", "scrollToLeft"],
                "description": 'The scroll behavior: "singleAction" for a single scroll action, "scrollToBottom" for scrolling to the bottom, etc.',
                "optional": True,
            },
            "direction": {
                "type": "enum",
                "values": ["down", "up", "right", "left"],
                "description": 'The direction to scroll. Only effective when scrollType is "singleAction".',
                "optional": True,
            },
            "distance": {
                "type": "number",
                "description": "The distance in pixels to scroll",
                "optional": True,
            },
            "locate": {
                "type": "MidsceneLocation",
                "description": 'The target element to be scrolled on, like "the table" or "the list"',
                "is_locator": True,
                "optional": True,
            },
        },
        "call": call,
    }


def define_action_assert() -> Dict[str, Any]:
    """定义Assert动作"""
    async def assert_call(param: Dict[str, Any], context: Any = None) -> None:
        result = param.get("result")
        thought = param.get("thought", "(no thought)")
        condition = param.get("condition", "")
        
        if not isinstance(result, bool):
            raise AssertionError(
                f"The result of the assertion must be a boolean, but got: {type(result)}. {thought}"
            )
        
        if not result:
            raise AssertionError(f"Assertion failed: {thought} (Assertion = {condition})")
    
    return {
        "name": "Print_Assert_Result",
        "description": "Print the result of the assertion",
        "param_schema": {
            "condition": {
                "type": "string",
                "description": "The condition of the assertion",
                "optional": False,
            },
            "thought": {
                "type": "string",
                "description": 'The thought of the assertion, like "I can see there are A, B, C elements on the page, which means ... , so the assertion is true"',
                "optional": False,
            },
            "result": {
                "type": "boolean",
                "description": "The result of the assertion, true or false",
                "optional": False,
            },
        },
        "call": assert_call,
    }
