"""
AI Prompt Templates

This module contains English prompts for AI model interactions.
Corresponding to TypeScript source: packages/core/src/ai-model/prompt/
"""

from mspy.core.ai_model.prompt.common import bbox_description
from mspy.core.ai_model.prompt.llm_locator import (
    system_prompt_to_locate_element,
    find_element_prompt,
)
from mspy.core.ai_model.prompt.llm_planning import (
    system_prompt_to_task_planning,
    description_for_action,
)
from mspy.core.ai_model.prompt.extraction import (
    system_prompt_to_extract,
    extract_data_query_prompt,
)
from mspy.core.ai_model.prompt.describe import element_describer_instruction
from mspy.core.ai_model.prompt.assertion import assert_schema
from mspy.core.ai_model.prompt.util import describe_size, describe_user_page

__all__ = [
    # Common
    "bbox_description",
    # Locator
    "system_prompt_to_locate_element",
    "find_element_prompt",
    # Planning
    "system_prompt_to_task_planning",
    "description_for_action",
    # Extraction
    "system_prompt_to_extract",
    "extract_data_query_prompt",
    # Describe
    "element_describer_instruction",
    # Assertion
    "assert_schema",
    # Util
    "describe_size",
    "describe_user_page",
]
