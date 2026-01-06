"""
元素描述提示词

从 packages/core/src/ai-model/prompt/describe.ts 迁移
"""

from mspy.core.ai_model.prompt.common import get_user_instruction_base


def element_describer_instruction() -> str:
    """生成元素描述的系统提示词"""
    base_instruction = get_user_instruction_base()
    
    return f"""{base_instruction}

You are an AI assistant specialized in describing UI elements.

## Task
Given a screenshot with a UI element marked by a red box, provide a concise and accurate description of that element.

## Response Format
Respond with a JSON object containing:
- "description": A clear, concise description of the element
- "error": Error message if the element cannot be described (optional)

## Guidelines for Description
1. Focus on what the element IS (button, link, input field, etc.)
2. Include the visible text or label if any
3. Mention distinctive visual features (color, icon, position)
4. Keep it concise but specific enough to uniquely identify the element
5. The description should work as a locator prompt to find this element again

## Good Description Examples
- "Blue 'Submit' button"
- "Search input field with magnifying glass icon"
- "Profile avatar in the top-right corner"
- "Red 'Delete' link under the item name"

## Bad Description Examples
- "A button" (too vague)
- "The element in the center of the screen" (not descriptive)
- "A clickable thing" (not specific)

## Example Response
```json
{{
  "description": "Blue 'Sign In' button in the navigation bar"
}}
```
"""


def get_describe_user_prompt() -> str:
    """获取描述用户提示"""
    return """Please describe the UI element marked with the red box in the screenshot.

The description should be:
1. Concise (1-2 sentences)
2. Specific enough to uniquely identify this element
3. Suitable for use as a locator prompt

Focus on visual characteristics and the element's purpose."""
