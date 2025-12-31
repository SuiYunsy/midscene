"""
元素描述Prompt
"""

from typing import Optional, List, Tuple
from openai.types.chat import ChatCompletionMessageParam


def build_describe_prompt(
    center: Tuple[int, int],
    screenshot_base64: str,
    deep_think: bool = False,
) -> List[ChatCompletionMessageParam]:
    """
    构建元素描述的Prompt
    
    Args:
        center: 元素中心点坐标
        screenshot_base64: 屏幕截图的Base64编码
        deep_think: 是否启用深度思考模式
        
    Returns:
        消息列表
    """
    x, y = center
    
    think_instruction = ""
    if deep_think:
        think_instruction = """
Please think carefully and provide a very precise description that uniquely identifies this element.
Consider:
- The exact text content of the element
- Its visual appearance (color, size, style)
- Its position relative to other elements
- Any unique characteristics that distinguish it from similar elements
"""
    
    system_prompt = f"""You are an AI assistant that helps describe UI elements.

Given a screenshot and a coordinate point, your task is to:
1. Identify the element at or near the specified coordinates
2. Provide a clear, concise description that could be used to locate this element again
{think_instruction}

Response format (JSON):
{{
  "description": "A prompt that uniquely describes this element",
  "error": null  // or an error message if the element cannot be identified
}}
"""
    
    messages: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": screenshot_base64},
                },
                {
                    "type": "text",
                    "text": f"Please describe the element at coordinates ({x}, {y})",
                },
            ],
        },
    ]
    
    return messages
