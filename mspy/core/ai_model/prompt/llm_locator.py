# -*- coding: utf-8 -*-
"""
元素定位提示词
用于定位页面元素的提示词模板。
"""

from typing import Optional
from .common import bbox_description


def system_prompt_to_locate_element(vl_mode: Optional[str]) -> str:
    """
    生成元素定位的系统提示词
    
    Args:
        vl_mode: VL 模式类型
        
    Returns:
        系统提示词
    """
    bbox_comment = bbox_description(vl_mode)
    
    return f"""
## Role:
You are an AI assistant that helps identify UI elements.

## Objective:
- Identify elements in screenshots that match the user's description.
- Provide the coordinates of the element that matches the user's description.

## Output Format:
```json
{{
  "bbox": [number, number, number, number],  // {bbox_comment}
  "errors"?: string[]
}}
```

Fields:
* `bbox` is the bounding box of the element that matches the user's description
* `errors` is an optional array of error messages (if any)

For example, when an element is found:
```json
{{
  "bbox": [100, 100, 200, 200],
  "errors": []
}}
```

When no element is found:
```json
{{
  "bbox": [],
  "errors": ["I can see ..., but {{some element}} is not found"]
}}
```
"""


def find_element_prompt(target_element_description: str) -> str:
    """
    生成查找元素的用户提示词
    
    Args:
        target_element_description: 目标元素描述
        
    Returns:
        用户提示词
    """
    return f"Find: {target_element_description}"
