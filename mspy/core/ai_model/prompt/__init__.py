# -*- coding: utf-8 -*-
"""
提示词模块
导出所有提示词相关的函数和模板。
"""

from .common import bbox_description
from .describe import element_describer_instruction
from .llm_locator import system_prompt_to_locate_element, find_element_prompt
from .extraction import system_prompt_to_extract, extract_data_query_prompt
from .assertion import system_prompt_to_assert, ASSERT_SCHEMA
from .llm_planning import (
    system_prompt_to_task_planning,
    description_for_action,
    vl_locate_param,
)
from .llm_section_locator import (
    system_prompt_to_locate_section,
    section_locator_instruction,
)

__all__ = [
    # 通用
    "bbox_description",
    # 描述
    "element_describer_instruction",
    # 定位
    "system_prompt_to_locate_element",
    "find_element_prompt",
    # 提取
    "system_prompt_to_extract",
    "extract_data_query_prompt",
    # 断言
    "system_prompt_to_assert",
    "ASSERT_SCHEMA",
    # 规划
    "system_prompt_to_task_planning",
    "description_for_action",
    "vl_locate_param",
    # 区域定位
    "system_prompt_to_locate_section",
    "section_locator_instruction",
]
