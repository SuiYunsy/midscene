"""
Midscene Python - Shared Module
共享模块：提供类型定义、日志、工具函数和配置管理
"""

from .types import (
    Point,
    Size,
    Rect,
    BaseElement,
    ElementTreeNode,
    LocateResultElement,
    NodeType,
    AIUsageInfo,
    AIAssertionResponse,
    PlanningAction,
    PlanningAIResponse,
    UIContext,
    DeviceAction,
)

from .logger import get_debug, setup_logger
from .utils import (
    uuid,
    assert_condition,
    if_in_node,
)
from .config import (
    GlobalConfigManager,
    ModelConfigManager,
    IModelConfig,
    TIntent,
)

__all__ = [
    # Types
    "Point",
    "Size",
    "Rect",
    "BaseElement",
    "ElementTreeNode",
    "LocateResultElement",
    "NodeType",
    "AIUsageInfo",
    "AIAssertionResponse",
    "PlanningAction",
    "PlanningAIResponse",
    "UIContext",
    "DeviceAction",
    # Logger
    "get_debug",
    "setup_logger",
    # Utils
    "uuid",
    "assert_condition",
    "if_in_node",
    # Config
    "GlobalConfigManager",
    "ModelConfigManager",
    "IModelConfig",
    "TIntent",
]
