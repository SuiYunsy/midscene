"""
Midscene Python 版本
Midscene Python version

这是 Midscene 的 Python 实现，提供 AI 驱动的 UI 自动化功能。
This is the Python implementation of Midscene, providing AI-driven UI automation.
"""

from .shared import (
    # types
    Point,
    Size,
    Rect,
    LocateResultElement,
    UIContext,
    PlanningAction,
    PlanningAIResponse,
    AIUsageInfo,
    ServiceError,
    DetailedLocateParam,
    # env
    ModelConfig,
    ModelConfigManager,
    get_env_value,
    get_env_bool,
    get_env_int,
    # utils
    uuid,
    assert_condition,
    sleep_ms,
    # logger
    get_debug,
)

from .core import (
    # device
    AbstractInterface,
    DeviceAction,
    # service
    Service,
    # agent
    Agent,
    # task_runner
    TaskRunner,
    TaskExecutionError,
)

from .web import (
    PlaywrightWebPage,
)

__version__ = "0.1.0"

__all__ = [
    # types
    "Point",
    "Size",
    "Rect",
    "LocateResultElement",
    "UIContext",
    "PlanningAction",
    "PlanningAIResponse",
    "AIUsageInfo",
    "ServiceError",
    "DetailedLocateParam",
    # env
    "ModelConfig",
    "ModelConfigManager",
    "get_env_value",
    "get_env_bool",
    "get_env_int",
    # utils
    "uuid",
    "assert_condition",
    "sleep_ms",
    # logger
    "get_debug",
    # device
    "AbstractInterface",
    "DeviceAction",
    # service
    "Service",
    # agent
    "Agent",
    # task_runner
    "TaskRunner",
    "TaskExecutionError",
    # web
    "PlaywrightWebPage",
]
