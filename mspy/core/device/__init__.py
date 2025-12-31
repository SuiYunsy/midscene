"""
设备模块

从 packages/core/src/device/ 迁移
"""

from mspy.core.device.interface import AbstractInterface
from mspy.core.device.actions import (
    define_action,
    define_action_tap,
    define_action_input,
    define_action_scroll,
    define_action_keyboard_press,
    define_action_hover,
    define_action_double_click,
    define_action_right_click,
    define_action_assert,
)

__all__ = [
    "AbstractInterface",
    "define_action",
    "define_action_tap",
    "define_action_input",
    "define_action_scroll",
    "define_action_keyboard_press",
    "define_action_hover",
    "define_action_double_click",
    "define_action_right_click",
    "define_action_assert",
]
