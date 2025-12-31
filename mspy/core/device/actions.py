"""
设备动作定义

从 packages/core/src/device/index.ts 迁移
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel, Field

from mspy.core.types import DeviceAction
from mspy.shared.types import LocateResultElement, Rect


# ========== 动作参数模型 ==========

class TapParam(BaseModel):
    """点击参数"""
    locate: LocateResultElement = Field(description="要点击的元素")


class RightClickParam(BaseModel):
    """右键点击参数"""
    locate: LocateResultElement = Field(description="要右键点击的元素")


class DoubleClickParam(BaseModel):
    """双击参数"""
    locate: LocateResultElement = Field(description="要双击的元素")


class HoverParam(BaseModel):
    """悬停参数"""
    locate: LocateResultElement = Field(description="要悬停的元素")


class InputParam(BaseModel):
    """输入参数"""
    value: str = Field(description="要输入的文本")
    locate: Optional[LocateResultElement] = Field(
        default=None,
        description="输入框位置"
    )
    mode: str = Field(
        default="replace",
        description="输入模式: replace(替换), append(追加), clear(清空)"
    )


class KeyboardPressParam(BaseModel):
    """键盘按键参数"""
    key_name: str = Field(
        description="要按的键，使用+连接组合键，如Control+A, Shift+Enter"
    )
    locate: Optional[LocateResultElement] = Field(
        default=None,
        description="按键前点击的元素"
    )


class ScrollParam(BaseModel):
    """滚动参数"""
    scroll_type: str = Field(
        default="singleAction",
        description="滚动类型: singleAction, scrollToBottom, scrollToTop, scrollToRight, scrollToLeft"
    )
    direction: str = Field(
        default="down",
        description="滚动方向: down, up, right, left"
    )
    distance: Optional[int] = Field(
        default=None,
        description="滚动距离（像素）"
    )
    locate: Optional[LocateResultElement] = Field(
        default=None,
        description="要滚动的目标区域"
    )


class AssertParam(BaseModel):
    """断言参数"""
    condition: str = Field(description="断言条件")
    thought: str = Field(description="断言的思考过程")
    result: bool = Field(description="断言结果")


class DragAndDropParam(BaseModel):
    """拖放参数"""
    from_element: LocateResultElement = Field(
        alias="from",
        description="拖动起始位置"
    )
    to_element: LocateResultElement = Field(
        alias="to",
        description="放置目标位置"
    )


# ========== 动作定义辅助函数 ==========

T = TypeVar("T")


def define_action(
    name: str,
    description: str,
    call: Callable[[Any], Any],
    interface_alias: Optional[str] = None,
    delay_after_runner: Optional[int] = None,
) -> DeviceAction:
    """
    定义设备动作
    
    Args:
        name: 动作名称
        description: 动作描述
        call: 执行函数
        interface_alias: 接口别名
        delay_after_runner: 执行后延迟（毫秒）
    
    Returns:
        DeviceAction实例
    """
    return DeviceAction(
        name=name,
        description=description,
        call=call,
        interface_alias=interface_alias,
        delay_after_runner=delay_after_runner,
    )


def define_action_tap(
    call: Callable[[TapParam], Any]
) -> DeviceAction:
    """定义点击动作"""
    return define_action(
        name="Tap",
        description="点击元素",
        interface_alias="ai_tap",
        call=call,
    )


def define_action_right_click(
    call: Callable[[RightClickParam], Any]
) -> DeviceAction:
    """定义右键点击动作"""
    return define_action(
        name="RightClick",
        description="右键点击元素",
        interface_alias="ai_right_click",
        call=call,
    )


def define_action_double_click(
    call: Callable[[DoubleClickParam], Any]
) -> DeviceAction:
    """定义双击动作"""
    return define_action(
        name="DoubleClick",
        description="双击元素",
        interface_alias="ai_double_click",
        call=call,
    )


def define_action_hover(
    call: Callable[[HoverParam], Any]
) -> DeviceAction:
    """定义悬停动作"""
    return define_action(
        name="Hover",
        description="鼠标悬停在元素上",
        interface_alias="ai_hover",
        call=call,
    )


def define_action_input(
    call: Callable[[InputParam], Any]
) -> DeviceAction:
    """定义输入动作"""
    return define_action(
        name="Input",
        description="在元素中输入文本",
        interface_alias="ai_input",
        call=call,
    )


def define_action_keyboard_press(
    call: Callable[[KeyboardPressParam], Any]
) -> DeviceAction:
    """定义键盘按键动作"""
    return define_action(
        name="KeyboardPress",
        description="按下键盘按键或组合键，如Enter, Tab, Control+A",
        interface_alias="ai_keyboard_press",
        call=call,
    )


def define_action_scroll(
    call: Callable[[ScrollParam], Any]
) -> DeviceAction:
    """定义滚动动作"""
    return define_action(
        name="Scroll",
        description="滚动页面或元素",
        interface_alias="ai_scroll",
        call=call,
    )


def define_action_assert() -> DeviceAction:
    """定义断言动作"""
    from mspy.shared.logger import get_debug
    
    _debug = get_debug("device:common-action")
    
    async def call(param: AssertParam) -> None:
        if not isinstance(param.result, bool):
            raise ValueError(
                f"断言结果必须是布尔值，但得到: {type(param.result)}. "
                f"{param.thought or '(no thought)'}"
            )
        
        _debug(
            f"Assert: {param.condition}, "
            f"Thought: {param.thought}, "
            f"Result: {param.result}"
        )
        
        if not param.result:
            raise AssertionError(
                f"断言失败: {param.thought or '(no thought)'} "
                f"(Assertion = {param.condition})"
            )
    
    return define_action(
        name="Print_Assert_Result",
        description="打印断言结果",
        call=call,
    )
