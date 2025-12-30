"""
AI模型调用模块

对应TypeScript源码: packages/core/src/ai-model/
"""

from mspy.core.ai_model.service_caller import (
    call_ai,
    call_ai_with_string_response,
    call_ai_with_object_response,
)
from mspy.core.ai_model.types import AIActionType, AIArgs

__all__ = [
    "call_ai",
    "call_ai_with_string_response",
    "call_ai_with_object_response",
    "AIActionType",
    "AIArgs",
]
