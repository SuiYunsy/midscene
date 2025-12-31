"""
共享模块 - 基础工具、类型和常量
"""

from mspy.shared.constants import NodeType
from mspy.shared.types import Point, Size, Rect, BaseElement, ElementTreeNode, LocateResultElement
from mspy.shared.utils import uuid, generate_hash_id, assert_condition
from mspy.shared.logger import get_logger

__all__ = [
    "NodeType",
    "Point",
    "Size",
    "Rect",
    "BaseElement",
    "ElementTreeNode",
    "LocateResultElement",
    "uuid",
    "generate_hash_id",
    "assert_condition",
    "get_logger",
]
