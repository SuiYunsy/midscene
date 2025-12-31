"""
设备抽象接口模块
Device abstract interface module
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Awaitable

from ..shared import (
    Size,
    Rect,
    UIContext,
    LocateResultElement,
    ModelConfig,
    get_debug,
)

debug = get_debug("device")


class DeviceAction:
    """
    Device action definition.
    设备动作定义
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        param_fields: Optional[List[Dict[str, Any]]] = None,
        call: Optional[Callable[..., Awaitable[Any]]] = None,
        interface_alias: Optional[str] = None,
        delay_after_runner: int = 300,
    ):
        self.name = name
        self.description = description
        self.param_fields = param_fields or []
        self._call = call
        self.interface_alias = interface_alias
        self.delay_after_runner = delay_after_runner
    
    async def call(self, param: Any, context: Any = None) -> Any:
        """Execute the action."""
        if self._call:
            return await self._call(param, context)
        raise NotImplementedError(f"Action {self.name} call not implemented")


class AbstractInterface(ABC):
    """
    Abstract interface for device interaction.
    设备交互的抽象接口
    """
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """Get the interface type name."""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """Take a screenshot and return as base64."""
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """Get the viewport size."""
        pass
    
    @abstractmethod
    def action_space(self) -> List[DeviceAction]:
        """Get available actions for this interface."""
        pass
    
    async def destroy(self) -> None:
        """Destroy the interface and cleanup resources."""
        pass
    
    def describe(self) -> str:
        """Get a description of the current state."""
        return ""
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """Hook called before invoking an action."""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """Hook called after invoking an action."""
        pass
    
    async def get_context(self) -> UIContext:
        """Get UI context with screenshot and size."""
        screenshot = await self.screenshot_base64()
        size = await self.size()
        return UIContext(
            screenshot_base64=screenshot,
            size=size,
            is_frozen=False,
        )


def define_action_tap(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define a tap action."""
    return DeviceAction(
        name="Tap",
        description="Tap the element",
        interface_alias="aiTap",
        param_fields=[
            {
                "name": "locate",
                "type": "object",
                "is_locator": True,
                "description": "The element to be tapped",
            }
        ],
        call=call,
    )


def define_action_input(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define an input action."""
    return DeviceAction(
        name="Input",
        description="Input the value into the element",
        interface_alias="aiInput",
        param_fields=[
            {
                "name": "value",
                "type": "string",
                "description": "The text to input",
            },
            {
                "name": "locate",
                "type": "object",
                "optional": True,
                "is_locator": True,
                "description": "The input field to input text",
            },
            {
                "name": "mode",
                "type": "string",
                "optional": True,
                "description": 'Input mode: "replace", "clear", or "append"',
            },
        ],
        call=call,
    )


def define_action_scroll(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define a scroll action."""
    return DeviceAction(
        name="Scroll",
        description="Scroll the page or an element",
        interface_alias="aiScroll",
        param_fields=[
            {
                "name": "scrollType",
                "type": "string",
                "optional": True,
                "description": 'Scroll type: "singleAction", "scrollToBottom", etc.',
            },
            {
                "name": "direction",
                "type": "string",
                "optional": True,
                "description": 'Direction: "up", "down", "left", "right"',
            },
            {
                "name": "distance",
                "type": "number",
                "optional": True,
                "description": "Distance in pixels to scroll",
            },
            {
                "name": "locate",
                "type": "object",
                "optional": True,
                "is_locator": True,
                "description": "The element to scroll on",
            },
        ],
        call=call,
    )


def define_action_keyboard_press(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define a keyboard press action."""
    return DeviceAction(
        name="KeyboardPress",
        description="Press a key or key combination",
        interface_alias="aiKeyboardPress",
        param_fields=[
            {
                "name": "keyName",
                "type": "string",
                "description": "The key to press, e.g. 'Enter', 'Control+A'",
            },
            {
                "name": "locate",
                "type": "object",
                "optional": True,
                "is_locator": True,
                "description": "Element to click before pressing key",
            },
        ],
        call=call,
    )


def define_action_hover(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define a hover action."""
    return DeviceAction(
        name="Hover",
        description="Move the mouse to the element",
        interface_alias="aiHover",
        param_fields=[
            {
                "name": "locate",
                "type": "object",
                "is_locator": True,
                "description": "The element to hover",
            }
        ],
        call=call,
    )


def define_action_right_click(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define a right click action."""
    return DeviceAction(
        name="RightClick",
        description="Right click the element",
        interface_alias="aiRightClick",
        param_fields=[
            {
                "name": "locate",
                "type": "object",
                "is_locator": True,
                "description": "The element to right click",
            }
        ],
        call=call,
    )


def define_action_double_click(call: Callable[..., Awaitable[None]]) -> DeviceAction:
    """Define a double click action."""
    return DeviceAction(
        name="DoubleClick",
        description="Double click the element",
        interface_alias="aiDoubleClick",
        param_fields=[
            {
                "name": "locate",
                "type": "object",
                "is_locator": True,
                "description": "The element to double click",
            }
        ],
        call=call,
    )


def define_action_assert() -> DeviceAction:
    """Define an assert action for AI planning."""
    async def assert_call(param: Dict[str, Any], context: Any = None) -> None:
        result = param.get("result")
        thought = param.get("thought", "(no thought)")
        condition = param.get("condition", "")
        
        if not isinstance(result, bool):
            raise ValueError(
                f"The result of the assertion must be a boolean, got: {type(result)}. {thought}"
            )
        
        debug.info(f"Assert: {condition}, Thought: {thought}, Result: {result}")
        
        if not result:
            raise AssertionError(f"Assertion failed: {thought} (Assertion = {condition})")
    
    return DeviceAction(
        name="Print_Assert_Result",
        description="Print the result of the assertion",
        param_fields=[
            {
                "name": "condition",
                "type": "string",
                "description": "The condition of the assertion",
            },
            {
                "name": "thought",
                "type": "string",
                "description": "The thought process behind the assertion",
            },
            {
                "name": "result",
                "type": "boolean",
                "description": "The result of the assertion, true or false",
            },
        ],
        call=assert_call,
    )
