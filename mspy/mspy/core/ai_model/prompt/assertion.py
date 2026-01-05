"""
断言Prompt
"""

from typing import Optional, List
from openai.types.chat import ChatCompletionMessageParam


def build_assertion_prompt(
    assertion: str,
    screenshot_base64: str,
) -> List[ChatCompletionMessageParam]:
    """
    构建断言的Prompt
    
    Args:
        assertion: 断言描述
        screenshot_base64: 屏幕截图的Base64编码
        
    Returns:
        消息列表
    """
    system_prompt = """You are an AI assistant that helps verify UI assertions.

Given a screenshot and an assertion statement, your task is to:
1. Analyze the screenshot carefully
2. Determine if the assertion is true or false based on what you see
3. Provide a clear explanation for your decision

Response format (JSON):
{
  "pass": true/false,
  "thought": "Detailed explanation of your reasoning"
}
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
                    "text": f"Please verify the following assertion: {assertion}",
                },
            ],
        },
    ]
    
    return messages
