"""
数据提取提示词

从 packages/core/src/ai-model/prompt/extraction.ts 迁移
"""

from typing import Any, Optional

from mspy.core.ai_model.prompt.common import get_user_instruction_base


def system_prompt_to_extract_data() -> str:
    """生成数据提取的系统提示词"""
    base_instruction = get_user_instruction_base()
    
    return f"""{base_instruction}

You are an AI assistant specialized in extracting structured data from UI screenshots.

## Task
Given a screenshot of a page and a data extraction request, analyze the visual content and extract the requested information.

## Response Format
Respond with a JSON object containing:
- "data": The extracted data matching the requested structure
- "thought": Your reasoning process for the extraction
- "errors": Array of error messages if any issues occurred

## Guidelines
1. Extract data exactly as shown in the UI
2. Maintain the requested data structure
3. If data is not found, return null for that field
4. Be accurate with text extraction - avoid typos

## Example
If asked to extract user profile information:
```json
{{
  "data": {{
    "username": "john_doe",
    "email": "john@example.com",
    "status": "Active"
  }},
  "thought": "Found user profile card in the top-right corner with username, email, and status badge",
  "errors": []
}}
```
"""


def get_extraction_user_prompt(
    data_demand: Any,
    page_description: Optional[str] = None
) -> str:
    """获取提取用户提示"""
    demand_str = str(data_demand)
    
    prompt = f"""Please extract the following information from the page:

Requested Data: {demand_str}
"""
    
    if page_description:
        prompt += f"""
Page Context: {page_description}
"""
    
    prompt += """
Analyze the screenshot and extract the requested information.
Return the data in the specified format."""
    
    return prompt
