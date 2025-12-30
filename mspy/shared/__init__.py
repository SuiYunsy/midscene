"""
共享模块 - 提供类型定义、工具函数、环境配置等通用功能
"""

from mspy.shared.types import (
    Point,
    Size,
    Rect,
    BaseElement,
    ElementTreeNode,
    LocateResultElement,
)
from mspy.shared.logger import get_debug, get_logger
from mspy.shared.utils import assert_condition, sleep_ms
from mspy.shared.common import get_midscene_run_sub_dir

__all__ = [
    # 类型
    "Point",
    "Size", 
    "Rect",
    "BaseElement",
    "ElementTreeNode",
    "LocateResultElement",
    # 日志
    "get_debug",
    "get_logger",
    # 工具
    "assert_condition",
    "sleep_ms",
    "get_midscene_run_sub_dir",
]
