"""
元素定位Prompt
"""

from typing import Optional, List
from openai.types.chat import ChatCompletionMessageParam


def build_locate_prompt(
    user_prompt: str,
    screenshot_base64: str,
    vl_mode: Optional[str] = None,
) -> List[ChatCompletionMessageParam]:
    """
    构建元素定位的Prompt
    
    Args:
        user_prompt: 用户描述的元素
        screenshot_base64: 屏幕截图的Base64编码
        vl_mode: VL模式
        
    Returns:
        消息列表
    """
    from mspy.core.ai_model.prompt.common import bbox_description
    
    bbox_desc = bbox_description(vl_mode)
    
    system_prompt = f"""You are an AI assistant that helps locate UI elements on a screen.

Given a screenshot and a description of the target element, your task is to:
1. Analyze the screenshot carefully
2. Find the element that best matches the description
3. Return the bounding box of the element

Response format (JSON):
{{
  "bbox": [xmin, ymin, xmax, ymax],  // {bbox_desc}
  "reason": "Brief explanation of why this element matches"
}}

If the element cannot be found, respond with:
{{
  "bbox": null,
  "reason": "Explanation of why the element was not found"
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
                    "text": f"Please locate the following element: {user_prompt}",
                },
            ],
        },
    ]
    
    return messages
