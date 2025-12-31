"""
元素定位提示词

从 packages/core/src/ai-model/prompt/llm-locator.ts 迁移
"""

from mspy.core.ai_model.prompt.common import get_user_instruction_base


def system_prompt_to_locate_element() -> str:
    """生成元素定位的系统提示词"""
    base_instruction = get_user_instruction_base()
    
    return f"""{base_instruction}

You are an AI assistant specialized in locating UI elements on a page.

## Task
Given a screenshot of a page and a description of the target element, identify and locate the element.

## Response Format
Respond with a JSON object containing:
- "elements": Array of found elements, each with:
  - "bbox": [x, y, width, height] - The bounding box coordinates
  - "description": A brief description of the located element
  - "confidence": A number between 0 and 1 indicating confidence
- "errors": Array of error messages if any issues occurred

## Guidelines
1. Be precise with coordinates - they should exactly match the element's position
2. If multiple elements match, return all of them
3. If no element matches, return an empty elements array with an error message
4. Consider the visual context when identifying elements

## Example Response
```json
{{
  "elements": [
    {{
      "bbox": [100, 200, 80, 30],
      "description": "Blue submit button",
      "confidence": 0.95
    }}
  ],
  "errors": []
}}
```
"""


def get_locate_user_prompt(target_description: str) -> str:
    """获取定位用户提示"""
    return f"""Please locate the following element on the page:

Target: {target_description}

Analyze the screenshot and find the element that best matches this description.
Return the bounding box coordinates and a brief description of what you found."""
