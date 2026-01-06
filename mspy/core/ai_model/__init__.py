"""
AI模型调用模块

从 packages/core/src/ai-model/ 迁移
"""

from mspy.core.ai_model.caller import (
    call_ai,
    call_ai_with_object_response,
    call_ai_with_string_response,
)

__all__ = [
    "call_ai",
    "call_ai_with_object_response",
    "call_ai_with_string_response",
]
