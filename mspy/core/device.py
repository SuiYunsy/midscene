"""
设备抽象接口模块
Device abstraction interface for Midscene Python SDK
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Awaitable, Tuple, TypeVar
from dataclasses import dataclass, field

from ..shared import (
    Size,
    Rect,
    UIContext,
    IModelConfig,
    get_debug,
)

debug = get_debug("device")


@dataclass
class DeviceAction:
    """
    设备动作定义
    """
    name: str
    description: str = ""
    interface_alias: Optional[str] = None
    param_schema: Optional[Dict[str, Any]] = None
    call: Optional[Callable] = None
    delay_after_runner: int = 300


class AbstractInterface(ABC):
    """
    抽象接口基类
    所有设备实现都需要继承此类
    """
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """获取接口类型"""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """获取截图的base64编码"""
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """获取屏幕/页面尺寸"""
        pass
    
    @abstractmethod
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作空间"""
        pass
    
    async def cache_feature_for_rect(
        self,
        rect: Rect,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        为矩形区域生成缓存特征
        
        Args:
            rect: 矩形区域
            options: 选项配置
            
        Returns:
            缓存特征字典
        """
        return {}
    
    async def rect_matches_cache_feature(
        self,
        feature: Dict[str, Any],
    ) -> Optional[Rect]:
        """
        根据缓存特征匹配矩形
        
        Args:
            feature: 缓存特征
            
        Returns:
            匹配的矩形，如果没有匹配则返回None
        """
        return None
    
    async def destroy(self):
        """销毁接口资源"""
        pass
    
    def describe(self) -> str:
        """获取接口描述"""
        return ""
    
    async def before_invoke_action(self, action_name: str, param: Any):
        """动作执行前的钩子"""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any):
        """动作执行后的钩子"""
        pass
    
    async def get_context(self) -> Optional[UIContext]:
        """获取UI上下文"""
        return None


def define_action(
    name: str,
    description: str = "",
    interface_alias: Optional[str] = None,
    param_schema: Optional[Dict[str, Any]] = None,
    call: Optional[Callable] = None,
    delay_after_runner: int = 300,
) -> DeviceAction:
    """
    定义一个设备动作
    
    Args:
        name: 动作名称
        description: 动作描述
        interface_alias: 接口别名
        param_schema: 参数schema
        call: 调用函数
        delay_after_runner: 执行后延迟(ms)
        
    Returns:
        DeviceAction对象
    """
    return DeviceAction(
        name=name,
        description=description,
        interface_alias=interface_alias,
        param_schema=param_schema,
        call=call,
        delay_after_runner=delay_after_runner,
    )


# 定义通用的参数schema

def get_locate_schema() -> Dict[str, Any]:
    """获取定位参数schema"""
    return {
        "type": "Locator",
        "description": "Target element locator",
        "optional": False,
    }


# 定义常用动作


def define_action_tap(call: Callable) -> DeviceAction:
    """定义点击动作"""
    return define_action(
        name="Tap",
        description="Tap the element",
        interface_alias="aiTap",
        param_schema={
            "locate": {
                "type": "Locator",
                "description": "The element to be tapped",
                "optional": False,
            }
        },
        call=call,
    )


def define_action_right_click(call: Callable) -> DeviceAction:
    """定义右键点击动作"""
    return define_action(
        name="RightClick",
        description="Right click the element",
        interface_alias="aiRightClick",
        param_schema={
            "locate": {
                "type": "Locator",
                "description": "The element to be right clicked",
                "optional": False,
            }
        },
        call=call,
    )


def define_action_double_click(call: Callable) -> DeviceAction:
    """定义双击动作"""
    return define_action(
        name="DoubleClick",
        description="Double click the element",
        interface_alias="aiDoubleClick",
        param_schema={
            "locate": {
                "type": "Locator",
                "description": "The element to be double clicked",
                "optional": False,
            }
        },
        call=call,
    )


def define_action_hover(call: Callable) -> DeviceAction:
    """定义悬停动作"""
    return define_action(
        name="Hover",
        description="Move the mouse to the element",
        interface_alias="aiHover",
        param_schema={
            "locate": {
                "type": "Locator",
                "description": "The element to be hovered",
                "optional": False,
            }
        },
        call=call,
    )


def define_action_input(call: Callable) -> DeviceAction:
    """定义输入动作"""
    return define_action(
        name="Input",
        description="Input the value into the element",
        interface_alias="aiInput",
        param_schema={
            "value": {
                "type": "string",
                "description": "The text to input",
                "optional": False,
            },
            "locate": {
                "type": "Locator",
                "description": "The input field",
                "optional": True,
            },
            "mode": {
                "type": "string",
                "description": "Input mode: replace, clear, or append",
                "optional": True,
            },
        },
        call=call,
    )


def define_action_keyboard_press(call: Callable) -> DeviceAction:
    """定义键盘按键动作"""
    return define_action(
        name="KeyboardPress",
        description="Press a key or key combination",
        interface_alias="aiKeyboardPress",
        param_schema={
            "locate": {
                "type": "Locator",
                "description": "The element to be clicked before pressing the key",
                "optional": True,
            },
            "keyName": {
                "type": "string",
                "description": "The key to be pressed",
                "optional": False,
            },
        },
        call=call,
    )


def define_action_scroll(call: Callable) -> DeviceAction:
    """定义滚动动作"""
    return define_action(
        name="Scroll",
        description="Scroll the page or an element",
        interface_alias="aiScroll",
        param_schema={
            "scrollType": {
                "type": "string",
                "description": "The scroll behavior",
                "optional": True,
            },
            "direction": {
                "type": "string",
                "description": "The direction to scroll",
                "optional": True,
            },
            "distance": {
                "type": "number",
                "description": "The distance in pixels to scroll",
                "optional": True,
            },
            "locate": {
                "type": "Locator",
                "description": "The target element to be scrolled on",
                "optional": True,
            },
        },
        call=call,
    )


def define_action_assert() -> DeviceAction:
    """定义断言动作"""
    async def assert_call(param: Dict[str, Any], context: Any = None):
        result = param.get("result")
        thought = param.get("thought", "(no thought)")
        condition = param.get("condition", "")
        
        if not isinstance(result, bool):
            raise ValueError(
                f"The result of the assertion must be a boolean, but got: {type(result).__name__}. {thought}"
            )
        
        debug(f"Assert: {condition}, Thought: {thought}, Result: {result}")
        
        if not result:
            raise AssertionError(f"Assertion failed: {thought} (Assertion = {condition})")
    
    return define_action(
        name="Print_Assert_Result",
        description="Print the result of the assertion",
        param_schema={
            "condition": {
                "type": "string",
                "description": "The condition of the assertion",
                "optional": False,
            },
            "thought": {
                "type": "string",
                "description": "The thought of the assertion",
                "optional": False,
            },
            "result": {
                "type": "boolean",
                "description": "The result of the assertion",
                "optional": False,
            },
        },
        call=assert_call,
    )
