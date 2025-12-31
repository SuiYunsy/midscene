"""
核心模块
Core module for midscene
"""
from .device import (
    AbstractInterface,
    DeviceAction,
    define_action_tap,
    define_action_input,
    define_action_scroll,
    define_action_keyboard_press,
    define_action_hover,
    define_action_right_click,
    define_action_double_click,
    define_action_assert,
)

from .service import Service, create_service_dump

from .task_runner import TaskRunner, TaskExecutionError

from .conversation_history import ConversationHistory

from .llm_planning import plan

from .service_caller import (
    call_ai,
    call_ai_with_object_response,
    safe_parse_json,
    extract_json_from_code_block,
)

from .prompt import (
    bbox_description,
    ASSERT_SCHEMA,
    system_prompt_to_task_planning,
    description_for_action,
)

from .agent import Agent

__all__ = [
    # device
    "AbstractInterface",
    "DeviceAction",
    "define_action_tap",
    "define_action_input",
    "define_action_scroll",
    "define_action_keyboard_press",
    "define_action_hover",
    "define_action_right_click",
    "define_action_double_click",
    "define_action_assert",
    # service
    "Service",
    "create_service_dump",
    # task_runner
    "TaskRunner",
    "TaskExecutionError",
    # conversation_history
    "ConversationHistory",
    # llm_planning
    "plan",
    # service_caller
    "call_ai",
    "call_ai_with_object_response",
    "safe_parse_json",
    "extract_json_from_code_block",
    # prompt
    "bbox_description",
    "ASSERT_SCHEMA",
    "system_prompt_to_task_planning",
    "description_for_action",
    # agent
    "Agent",
]
