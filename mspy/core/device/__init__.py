"""
设备抽象层

对应TypeScript源码: packages/core/src/device/index.ts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

from mspy.shared.types import Rect, Size, LocateResultElement
from mspy.core.types import UIContext, DeviceAction


class AbstractInterface(ABC):
    """抽象接口类
    
    定义了所有设备接口必须实现的方法
    """
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """接口类型"""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """获取页面截图的Base64编码"""
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """获取页面尺寸"""
        pass
    
    @abstractmethod
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作空间"""
        pass
    
    async def cache_feature_for_rect(
        self,
        rect: Rect,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """为矩形区域获取缓存特征"""
        return {}
    
    async def rect_matches_cache_feature(
        self,
        feature: Dict[str, Any]
    ) -> Optional[Rect]:
        """检查缓存特征是否匹配某个矩形"""
        return None
    
    async def destroy(self) -> None:
        """销毁接口"""
        pass
    
    def describe(self) -> str:
        """描述接口"""
        return f"{self.interface_type} interface"
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """动作执行前的钩子"""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """动作执行后的钩子"""
        pass
    
    async def get_context(self) -> Optional[UIContext]:
        """获取UI上下文"""
        return None
    
    async def url(self) -> Optional[str]:
        """获取当前URL"""
        return None
    
    async def evaluate_javascript(self, script: str) -> Any:
        """执行JavaScript"""
        raise NotImplementedError("此接口不支持执行JavaScript")


# ============ 动作定义工具函数 ============

def define_action(
    name: str,
    description: str,
    call: Callable,
    param_schema: Any = None,
    interface_alias: Optional[str] = None,
    delay_after_runner: Optional[int] = None,
) -> DeviceAction:
    """定义一个动作
    
    Args:
        name: 动作名称
        description: 动作描述
        call: 执行函数
        param_schema: 参数模式
        interface_alias: 接口别名
        delay_after_runner: 执行后延迟
        
    Returns:
        DeviceAction对象
    """
    return DeviceAction(
        name=name,
        description=description,
        call=call,
        param_schema=param_schema,
        interface_alias=interface_alias,
        delay_after_runner=delay_after_runner,
    )


# ============ 预定义动作参数类型 ============

@dataclass
class ActionTapParam:
    """点击动作参数"""
    locate: LocateResultElement


@dataclass
class ActionRightClickParam:
    """右键点击动作参数"""
    locate: LocateResultElement


@dataclass
class ActionDoubleClickParam:
    """双击动作参数"""
    locate: LocateResultElement


@dataclass
class ActionHoverParam:
    """悬停动作参数"""
    locate: LocateResultElement


@dataclass
class ActionInputParam:
    """输入动作参数"""
    value: str
    locate: Optional[LocateResultElement] = None
    mode: str = "replace"  # replace, clear, append


@dataclass
class ActionKeyboardPressParam:
    """键盘按键动作参数"""
    key_name: str
    locate: Optional[LocateResultElement] = None


@dataclass
class ActionScrollParam:
    """滚动动作参数"""
    scroll_type: str = "singleAction"  # singleAction, scrollToBottom, scrollToTop, scrollToRight, scrollToLeft
    direction: str = "down"  # down, up, right, left
    distance: Optional[int] = None
    locate: Optional[LocateResultElement] = None


@dataclass
class ActionDragAndDropParam:
    """拖拽动作参数"""
    from_element: LocateResultElement
    to_element: LocateResultElement


@dataclass
class ActionLongPressParam:
    """长按动作参数"""
    locate: LocateResultElement
    duration: int = 500


@dataclass
class ActionSwipeParam:
    """滑动动作参数"""
    start: Optional[LocateResultElement] = None
    end: Optional[LocateResultElement] = None
    direction: Optional[str] = None  # up, down, left, right
    distance: Optional[int] = None
    duration: int = 300
    repeat: int = 1


@dataclass
class ActionClearInputParam:
    """清除输入动作参数"""
    locate: LocateResultElement


@dataclass
class ActionAssertParam:
    """断言动作参数"""
    condition: str
    thought: str
    result: bool


# ============ 动作定义辅助函数 ============

def define_action_tap(call: Callable[[ActionTapParam], None]) -> DeviceAction:
    """定义点击动作"""
    return define_action(
        name="Tap",
        description="点击元素",
        call=call,
        interface_alias="aiTap",
    )


def define_action_right_click(call: Callable[[ActionRightClickParam], None]) -> DeviceAction:
    """定义右键点击动作"""
    return define_action(
        name="RightClick",
        description="右键点击元素",
        call=call,
        interface_alias="aiRightClick",
    )


def define_action_double_click(call: Callable[[ActionDoubleClickParam], None]) -> DeviceAction:
    """定义双击动作"""
    return define_action(
        name="DoubleClick",
        description="双击元素",
        call=call,
        interface_alias="aiDoubleClick",
    )


def define_action_hover(call: Callable[[ActionHoverParam], None]) -> DeviceAction:
    """定义悬停动作"""
    return define_action(
        name="Hover",
        description="鼠标悬停在元素上",
        call=call,
        interface_alias="aiHover",
    )


def define_action_input(call: Callable[[ActionInputParam], None]) -> DeviceAction:
    """定义输入动作"""
    return define_action(
        name="Input",
        description="在元素中输入文本",
        call=call,
        interface_alias="aiInput",
    )


def define_action_keyboard_press(call: Callable[[ActionKeyboardPressParam], None]) -> DeviceAction:
    """定义键盘按键动作"""
    return define_action(
        name="KeyboardPress",
        description="按下键盘按键",
        call=call,
        interface_alias="aiKeyboardPress",
    )


def define_action_scroll(call: Callable[[ActionScrollParam], None]) -> DeviceAction:
    """定义滚动动作"""
    return define_action(
        name="Scroll",
        description="滚动页面或元素",
        call=call,
        interface_alias="aiScroll",
    )


def define_action_drag_and_drop(call: Callable[[ActionDragAndDropParam], None]) -> DeviceAction:
    """定义拖拽动作"""
    return define_action(
        name="DragAndDrop",
        description="拖拽元素",
        call=call,
        interface_alias="aiDragAndDrop",
    )


def define_action_long_press(call: Callable[[ActionLongPressParam], None]) -> DeviceAction:
    """定义长按动作"""
    return define_action(
        name="LongPress",
        description="长按元素",
        call=call,
    )


def define_action_swipe(call: Callable[[ActionSwipeParam], None]) -> DeviceAction:
    """定义滑动动作"""
    return define_action(
        name="Swipe",
        description="滑动手势",
        call=call,
    )


def define_action_clear_input(call: Callable[[ActionClearInputParam], None]) -> DeviceAction:
    """定义清除输入动作"""
    return define_action(
        name="ClearInput",
        description="清除输入框内容",
        call=call,
        interface_alias="aiClearInput",
    )


def define_action_assert() -> DeviceAction:
    """定义断言动作"""
    from mspy.shared.logger import get_debug
    debug = get_debug('device:common-action')
    
    async def call(param: ActionAssertParam):
        if not isinstance(param.result, bool):
            raise ValueError(
                f"断言结果必须是布尔值，但得到: {type(param.result)}. {param.thought or '(无说明)'}"
            )
        
        debug(f"断言: {param.condition}, 说明: {param.thought}, 结果: {param.result}")
        
        if not param.result:
            raise AssertionError(
                f"断言失败: {param.thought or '(无说明)'} (断言 = {param.condition})"
            )
    
    return define_action(
        name="Print_Assert_Result",
        description="打印断言结果",
        call=call,
    )
