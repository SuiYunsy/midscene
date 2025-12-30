# -*- coding: utf-8 -*-
"""
AI 模型模块
导出所有 AI 模型相关的功能。
"""

from .service_caller import (
    call_ai,
    call_ai_with_object_response,
    call_ai_with_string_response,
    AIActionType,
    AICallResult,
    safe_parse_json,
    extract_json_from_code_block,
)
from .prompt import (
    system_prompt_to_locate_element,
    find_element_prompt,
    system_prompt_to_extract,
    extract_data_query_prompt,
    system_prompt_to_task_planning,
    element_describer_instruction,
    bbox_description,
)

__all__ = [
    # 服务调用
    "call_ai",
    "call_ai_with_object_response",
    "call_ai_with_string_response",
    "AIActionType",
    "AICallResult",
    "safe_parse_json",
    "extract_json_from_code_block",
    # 提示词
    "system_prompt_to_locate_element",
    "find_element_prompt",
    "system_prompt_to_extract",
    "extract_data_query_prompt",
    "system_prompt_to_task_planning",
    "element_describer_instruction",
    "bbox_description",
]
