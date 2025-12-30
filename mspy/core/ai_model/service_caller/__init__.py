"""
AI服务调用模块

对应TypeScript源码: packages/core/src/ai-model/service-caller/
"""

from mspy.core.ai_model.service_caller.caller import (
    call_ai,
    call_ai_with_string_response,
    call_ai_with_object_response,
)

__all__ = [
    "call_ai",
    "call_ai_with_string_response",
    "call_ai_with_object_response",
]
