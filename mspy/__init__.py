"""
Midscene Python
将 Midscene 的核心功能从 TypeScript 迁移到 Python

主要模块:
- shared: 共享工具、类型定义、配置管理
- core: AI 规划、断言、服务调用
- web: Playwright 集成
"""

__version__ = "0.1.0"

from mspy.shared import (
    # Types
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
    # Logger
    get_debug,
    setup_logger,
    # Utils
    uuid,
    assert_condition,
    # Config
    GlobalConfigManager,
    ModelConfigManager,
    IModelConfig,
)

from mspy.core import (
    Agent,
    AgentOpt,
    AiActOptions,
    create_agent,
    Service,
    plan,
    call_ai,
    call_ai_with_object_response,
    system_prompt_to_task_planning,
    ASSERT_SCHEMA,
)

from mspy.web import (
    PlaywrightWebPage,
    PlaywrightAgent,
)

__all__ = [
    # Version
    "__version__",
    # Shared Types
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
    # Shared Logger
    "get_debug",
    "setup_logger",
    # Shared Utils
    "uuid",
    "assert_condition",
    # Shared Config
    "GlobalConfigManager",
    "ModelConfigManager",
    "IModelConfig",
    # Core
    "Agent",
    "AgentOpt",
    "AiActOptions",
    "create_agent",
    "Service",
    "plan",
    "call_ai",
    "call_ai_with_object_response",
    "system_prompt_to_task_planning",
    "ASSERT_SCHEMA",
    # Web
    "PlaywrightWebPage",
    "PlaywrightAgent",
]
