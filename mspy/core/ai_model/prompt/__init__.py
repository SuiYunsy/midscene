"""
提示词模块

从 packages/core/src/ai-model/prompt/ 迁移
"""

from mspy.core.ai_model.prompt.common import (
    SYSTEM_ROLE_PROMPT,
    get_user_instruction_base,
)
from mspy.core.ai_model.prompt.locator import (
    system_prompt_to_locate_element,
)
from mspy.core.ai_model.prompt.extraction import (
    system_prompt_to_extract_data,
)
from mspy.core.ai_model.prompt.assertion import (
    system_prompt_to_assert,
)
from mspy.core.ai_model.prompt.describe import (
    element_describer_instruction,
)

__all__ = [
    "SYSTEM_ROLE_PROMPT",
    "get_user_instruction_base",
    "system_prompt_to_locate_element",
    "system_prompt_to_extract_data",
    "system_prompt_to_assert",
    "element_describer_instruction",
]
