"""
数据提取Prompt
"""

from typing import Optional, List, Union, Dict
from openai.types.chat import ChatCompletionMessageParam


def build_extraction_prompt(
    data_demand: Union[str, Dict[str, str]],
    screenshot_base64: str,
) -> List[ChatCompletionMessageParam]:
    """
    构建数据提取的Prompt
    
    Args:
        data_demand: 数据需求描述（字符串或字典）
        screenshot_base64: 屏幕截图的Base64编码
        
    Returns:
        消息列表
    """
    if isinstance(data_demand, dict):
        demand_text = "Please extract the following information:\n"
        for key, desc in data_demand.items():
            demand_text += f"- {key}: {desc}\n"
    else:
        demand_text = f"Please extract: {data_demand}"
    
    system_prompt = """You are an AI assistant that helps extract information from UI screenshots.

Given a screenshot and a data extraction request, your task is to:
1. Analyze the screenshot carefully
2. Extract the requested information
3. Return the extracted data in a structured format

Response format (JSON):
{
  "data": <extracted data matching the request structure>,
  "thought": "Brief explanation of how you extracted the data"
}

If the data cannot be found, explain why in the thought field and set data to null.
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
                    "text": demand_text,
                },
            ],
        },
    ]
    
    return messages
