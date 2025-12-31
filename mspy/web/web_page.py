"""
Web页面抽象层

从 packages/web-integration/src/web-page.ts 迁移
"""

import asyncio
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Protocol, Tuple, Union

from mspy.core.device import AbstractInterface
from mspy.core.types import DeviceAction
from mspy.shared.keyboard import parse_key_combination
from mspy.shared.logger import get_debug
from mspy.shared.types import Point


_debug = get_debug("web:page")


# ========== 键盘输入类型定义 ==========

# 常用键名列表
KEY_INPUT_VALUES = [
    "Escape", "Tab", "Enter", "Backspace", "Delete", "Insert",
    "Home", "End", "PageUp", "PageDown",
    "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
    "Shift", "ShiftLeft", "ShiftRight",
    "Control", "ControlLeft", "ControlRight",
    "Alt", "AltLeft", "AltRight",
    "Meta", "MetaLeft", "MetaRight",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
    "Space", " ",
    # 字母键
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    # 数字键
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
]

MouseButton = str  # "left" | "right" | "middle"


@dataclass
class KeyCommand:
    """键命令"""
    key: str
    command: Optional[str] = None


# ========== 动作接口定义 ==========

class MouseAction(Protocol):
    """鼠标动作接口"""
    
    async def click(
        self,
        x: int,
        y: int,
        button: MouseButton = "left",
        count: int = 1
    ) -> None:
        """点击"""
        ...
    
    async def wheel(self, delta_x: int, delta_y: int) -> None:
        """滚轮"""
        ...
    
    async def move(self, x: int, y: int) -> None:
        """移动"""
        ...
    
    async def drag(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int]
    ) -> None:
        """拖拽"""
        ...


class KeyboardAction(Protocol):
    """键盘动作接口"""
    
    async def type_text(self, text: str) -> None:
        """输入文本"""
        ...
    
    async def press(
        self,
        action: Union[KeyCommand, List[KeyCommand]]
    ) -> None:
        """按键"""
        ...


# ========== 工具函数 ==========

def normalize_key_inputs(value: Union[str, List[str]]) -> List[str]:
    """规范化键输入"""
    inputs = value if isinstance(value, list) else [value]
    result: List[str] = []
    
    for input_str in inputs:
        if not isinstance(input_str, str):
            result.append(str(input_str))
            continue
        
        trimmed = input_str.strip()
        if not trimmed:
            result.append(input_str)
            continue
        
        normalized = trimmed
        if len(normalized) > 1 and "+" in normalized:
            # 替换 + 为空格（组合键）
            normalized = normalized.replace("+", " ").strip()
        
        # 处理空格
        if " " in normalized:
            parts = normalized.split()
            result.extend(parts)
        else:
            result.append(normalized)
    
    return result


def get_key_commands(value: Union[str, List[str]]) -> List[KeyCommand]:
    """
    获取键命令列表
    
    Args:
        value: 键输入值，可以是单个键或键列表
    
    Returns:
        KeyCommand列表
    """
    keys = normalize_key_inputs(value)
    result: List[KeyCommand] = []
    
    has_meta = "Meta" in keys or "Control" in keys
    
    for key in keys:
        command = None
        
        if has_meta:
            if key.lower() == "a":
                command = "SelectAll"
            elif key.lower() == "c":
                command = "Copy"
            elif key.lower() == "v":
                command = "Paste"
        
        result.append(KeyCommand(key=key, command=command))
    
    return result


# ========== 抽象Web页面类 ==========

class AbstractWebPage(AbstractInterface):
    """
    抽象Web页面类
    
    定义了Web页面的基础接口，包括鼠标、键盘操作和滚动等
    """
    
    @property
    def interface_type(self) -> str:
        """接口类型"""
        return "web"
    
    # 导航方法
    async def navigate(self, url: str) -> None:
        """导航到URL"""
        raise NotImplementedError("navigate not implemented")
    
    async def reload(self) -> None:
        """重新加载页面"""
        raise NotImplementedError("reload not implemented")
    
    async def go_back(self) -> None:
        """后退"""
        raise NotImplementedError("go_back not implemented")
    
    # 鼠标操作
    @property
    def mouse(self) -> MouseAction:
        """获取鼠标动作接口"""
        # 默认空实现
        class DefaultMouse:
            async def click(self, x: int, y: int, button: str = "left", count: int = 1) -> None:
                pass
            async def wheel(self, delta_x: int, delta_y: int) -> None:
                pass
            async def move(self, x: int, y: int) -> None:
                pass
            async def drag(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> None:
                pass
        return DefaultMouse()
    
    @property
    def keyboard(self) -> KeyboardAction:
        """获取键盘动作接口"""
        class DefaultKeyboard:
            async def type_text(self, text: str) -> None:
                pass
            async def press(self, action) -> None:
                pass
        return DefaultKeyboard()
    
    async def clear_input(self, element: Any) -> None:
        """清除输入框内容"""
        pass
    
    # 抽象滚动方法
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
    async def scroll_up(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        """向上滚动"""
        pass
    
    @abstractmethod
    async def scroll_down(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        """向下滚动"""
        pass
    
    @abstractmethod
    async def scroll_left(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        """向左滚动"""
        pass
    
    @abstractmethod
    async def scroll_right(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Point] = None
    ) -> None:
        """向右滚动"""
        pass
    
    @abstractmethod
    async def long_press(
        self,
        x: int,
        y: int,
        duration: Optional[int] = None
    ) -> None:
        """长按"""
        pass
    
    @abstractmethod
    async def swipe(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int],
        duration: Optional[int] = None
    ) -> None:
        """滑动"""
        pass
