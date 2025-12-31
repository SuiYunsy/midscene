"""
Prompt模块

包含各种AI操作的Prompt模板。
"""

from mspy.core.ai_model.prompt.common import bbox_description
from mspy.core.ai_model.prompt.llm_locator import build_locate_prompt
from mspy.core.ai_model.prompt.assertion import build_assertion_prompt
from mspy.core.ai_model.prompt.extraction import build_extraction_prompt
from mspy.core.ai_model.prompt.describe import build_describe_prompt

__all__ = [
    "bbox_description",
    "build_locate_prompt",
    "build_assertion_prompt",
    "build_extraction_prompt",
    "build_describe_prompt",
]
