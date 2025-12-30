"""
AI服务调用实现

对应TypeScript源码: packages/core/src/ai-model/service-caller/index.ts
"""

import json
import time
import base64
from typing import Any, Dict, List, Optional, TypeVar

from mspy.shared.logger import get_debug
from mspy.shared.env import IModelConfig
from mspy.shared.types import AIUsageInfo
from mspy.core.ai_model.types import AIActionType, AIArgs

debug = get_debug('ai:service-caller')

T = TypeVar('T')

# Default timeout in seconds for AI model calls
DEFAULT_TIMEOUT_SECONDS = 120


def build_vision_message(
    system_prompt: str,
    user_prompt: str,
    screenshot_base64: Optional[str] = None
) -> AIArgs:
    """Build messages for vision models
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        screenshot_base64: Optional base64 encoded screenshot
        
    Returns:
        List of messages for AI model
    """
    messages = [{"role": "system", "content": system_prompt}]
    
    if screenshot_base64:
        # Vision model message with image
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_base64}"
                    }
                },
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        })
    else:
        messages.append({"role": "user", "content": user_prompt})
    
    return messages


async def call_ai(
    messages: AIArgs,
    action_type: AIActionType,
    model_config: IModelConfig,
    response_format: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """调用AI模型
    
    Args:
        messages: 消息列表
        action_type: 动作类型
        model_config: 模型配置
        response_format: 响应格式
        
    Returns:
        AI响应
    """
    debug(f"call_ai: action_type={action_type}, model={model_config.model_name}")
    
    try:
        # 尝试使用OpenAI SDK
        import openai
        
        # 创建客户端
        client = openai.OpenAI(
            api_key=model_config.openai_api_key,
            base_url=model_config.openai_base_url,
            timeout=model_config.timeout / 1000 if model_config.timeout else DEFAULT_TIMEOUT_SECONDS,
        )
        
        # 准备请求参数
        request_params = {
            "model": model_config.model_name,
            "messages": messages,
            "temperature": model_config.temperature if model_config.temperature is not None else 0.0,
            "max_tokens": 4096,
        }
        
        # 添加响应格式（如果支持）
        if response_format and response_format.get('type') == 'json_object':
            request_params['response_format'] = {"type": "json_object"}
        
        # 调用模型
        start_time = time.time()
        response = client.chat.completions.create(**request_params)
        end_time = time.time()
        
        # 解析响应
        content = response.choices[0].message.content
        usage = AIUsageInfo(
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=response.usage.completion_tokens if response.usage else None,
            total_tokens=response.usage.total_tokens if response.usage else None,
            time_cost=end_time - start_time,
            model_name=model_config.model_name,
        )
        
        debug(f"AI响应: {content[:200]}..." if len(str(content)) > 200 else f"AI响应: {content}")
        
        return {
            'content': content,
            'usage': usage,
        }
        
    except ImportError:
        debug("OpenAI SDK未安装，返回模拟响应")
        return {
            'content': '{}',
            'usage': AIUsageInfo(
                model_name=model_config.model_name,
            ),
        }
    except Exception as e:
        debug(f"AI调用失败: {e}")
        raise


async def call_ai_with_string_response(
    messages: AIArgs,
    action_type: AIActionType,
    model_config: IModelConfig,
) -> str:
    """调用AI模型并返回字符串响应
    
    Args:
        messages: 消息列表
        action_type: 动作类型
        model_config: 模型配置
        
    Returns:
        字符串响应
    """
    result = await call_ai(messages, action_type, model_config)
    return result.get('content', '')


def extract_json_from_response(content: str) -> Dict[str, Any]:
    """Extract JSON from AI response that may contain markdown code blocks
    
    Args:
        content: Raw AI response content
        
    Returns:
        Parsed JSON object
    """
    if not content:
        return {}
    
    # Try direct JSON parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code block
    import re
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, content)
    
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Try to find JSON object in the content
    brace_pattern = r'\{[\s\S]*\}'
    matches = re.findall(brace_pattern, content)
    
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    return {}


async def call_ai_with_object_response(
    messages: AIArgs,
    action_type: AIActionType,
    model_config: IModelConfig,
    response_format: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """调用AI模型并返回JSON对象响应
    
    Args:
        messages: 消息列表
        action_type: 动作类型
        model_config: 模型配置
        response_format: 响应格式
        
    Returns:
        JSON对象响应
    """
    result = await call_ai(messages, action_type, model_config, response_format)
    content = result.get('content', '{}')
    
    parsed = extract_json_from_response(content)
    return {
        'content': parsed,
        'usage': result.get('usage'),
        'raw_response': content,
    }
