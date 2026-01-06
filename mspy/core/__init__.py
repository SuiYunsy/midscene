"""
Midscene Python SDK - Core Module
核心模块，包含Agent、Service、Device等核心功能
"""

from .device import (
    AbstractInterface,
    DeviceAction,
    define_action,
    define_action_tap,
    define_action_right_click,
    define_action_double_click,
    define_action_hover,
    define_action_input,
    define_action_keyboard_press,
    define_action_scroll,
    define_action_assert,
)

from .service import (
    Service,
    create_service_dump,
)

from .service_caller import (
    call_ai,
    call_ai_with_object_response,
    safe_parse_json,
    extract_json_from_code_block,
    AIResponse,
)

from .conversation_history import (
    ConversationHistory,
)

from .llm_planning import (
    plan,
    AIActionType,
    fill_bbox_param,
)

from .prompt_planning import (
    system_prompt_to_task_planning,
    bbox_description,
    get_vl_locate_param,
    description_for_action,
)

from .task_executor import (
    TaskExecutor,
    TaskExecutionError,
    ExecutionResult,
)

from .agent import (
    Agent,
    AgentOpt,
    create_agent,
)

__all__ = [
    # Device
    "AbstractInterface",
    "DeviceAction",
    "define_action",
    "define_action_tap",
    "define_action_right_click",
    "define_action_double_click",
    "define_action_hover",
    "define_action_input",
    "define_action_keyboard_press",
    "define_action_scroll",
    "define_action_assert",
    # Service
    "Service",
    "create_service_dump",
    # Service Caller
    "call_ai",
    "call_ai_with_object_response",
    "safe_parse_json",
    "extract_json_from_code_block",
    "AIResponse",
    # Conversation History
    "ConversationHistory",
    # LLM Planning
    "plan",
    "AIActionType",
    "fill_bbox_param",
    # Prompt Planning
    "system_prompt_to_task_planning",
    "bbox_description",
    "get_vl_locate_param",
    "description_for_action",
    # Task Executor
    "TaskExecutor",
    "TaskExecutionError",
    "ExecutionResult",
    # Agent
    "Agent",
    "AgentOpt",
    "create_agent",
]
