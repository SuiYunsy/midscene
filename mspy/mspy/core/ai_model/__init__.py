"""
AI模型调用模块
"""

from mspy.core.ai_model.service_caller import (
    call_ai,
    call_ai_with_object_response,
    call_ai_with_string_response,
    extract_json_from_code_block,
    safe_parse_json,
)

__all__ = [
    "call_ai",
    "call_ai_with_object_response",
    "call_ai_with_string_response",
    "extract_json_from_code_block",
    "safe_parse_json",
]
