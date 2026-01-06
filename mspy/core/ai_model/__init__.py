"""
AI模型调用模块

对应TypeScript源码: packages/core/src/ai-model/
"""

from mspy.core.ai_model.service_caller import (
    call_ai,
    call_ai_with_string_response,
    call_ai_with_object_response,
    build_vision_message,
    extract_json_from_response,
)
from mspy.core.ai_model.types import AIActionType, AIArgs
from mspy.core.ai_model.prompt import (
    system_prompt_to_locate_element,
    find_element_prompt,
    system_prompt_to_task_planning,
    system_prompt_to_extract,
    extract_data_query_prompt,
    element_describer_instruction,
    assert_schema,
    describe_size,
    describe_user_page,
)

__all__ = [
    # Service caller
    "call_ai",
    "call_ai_with_string_response",
    "call_ai_with_object_response",
    "build_vision_message",
    "extract_json_from_response",
    # Types
    "AIActionType",
    "AIArgs",
    # Prompts
    "system_prompt_to_locate_element",
    "find_element_prompt",
    "system_prompt_to_task_planning",
    "system_prompt_to_extract",
    "extract_data_query_prompt",
    "element_describer_instruction",
    "assert_schema",
    "describe_size",
    "describe_user_page",
]
