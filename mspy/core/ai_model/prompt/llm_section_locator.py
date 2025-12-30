# -*- coding: utf-8 -*-
"""
区域定位提示词
用于定位页面区域的提示词模板。
"""

from typing import Optional
from .common import bbox_description


def system_prompt_to_locate_section(vl_mode: Optional[str]) -> str:
    """
    生成区域定位的系统提示词
    
    Args:
        vl_mode: VL 模式类型
        
    Returns:
        系统提示词
    """
    bbox_comment = bbox_description(vl_mode)
    
    return f"""
## Role:
You are an AI assistant that helps identify sections/regions in UI screenshots.

## Objective:
- Identify the section/region in the screenshot that matches the user's description.
- Provide the bounding box coordinates for the matched section.

## Output Format:
```json
{{
  "bbox": [number, number, number, number],  // {bbox_comment}
  "references_bbox"?: [[number, number, number, number]],  // Additional reference bounding boxes if any
  "error"?: string
}}
```
"""


def section_locator_instruction(section_description: str) -> str:
    """
    生成区域定位指令
    
    Args:
        section_description: 区域描述
        
    Returns:
        用户提示词
    """
    return f"Find the section: {section_description}"
