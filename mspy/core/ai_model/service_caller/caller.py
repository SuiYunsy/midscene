"""
AI服务调用实现

对应TypeScript源码: packages/core/src/ai-model/service-caller/index.ts
"""

import json
import time
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from mspy.shared.logger import get_debug
from mspy.shared.env import IModelConfig
from mspy.shared.types import AIUsageInfo
from mspy.core.ai_model.types import AIActionType, AIArgs

debug = get_debug('ai:service-caller')

T = TypeVar('T')


async def call_ai(
    messages: AIArgs,
    action_type: AIActionType,
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """调用AI模型
    
    Args:
        messages: 消息列表
        action_type: 动作类型
        model_config: 模型配置
        
    Returns:
        AI响应
    """
    debug(f"call_ai: action_type={action_type}")
    
    try:
        # 尝试使用OpenAI SDK
        import openai
        
        # 创建客户端
        client = openai.OpenAI(
            api_key=model_config.openai_api_key,
            base_url=model_config.openai_base_url,
            timeout=model_config.timeout / 1000 if model_config.timeout else None,
        )
        
        # 调用模型
        start_time = time.time()
        response = client.chat.completions.create(
            model=model_config.model_name,
            messages=messages,
            temperature=model_config.temperature or 0.7,
        )
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


async def call_ai_with_object_response(
    messages: AIArgs,
    action_type: AIActionType,
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """调用AI模型并返回JSON对象响应
    
    Args:
        messages: 消息列表
        action_type: 动作类型
        model_config: 模型配置
        
    Returns:
        JSON对象响应
    """
    result = await call_ai(messages, action_type, model_config)
    content = result.get('content', '{}')
    
    try:
        parsed = json.loads(content)
        return {
            'content': parsed,
            'usage': result.get('usage'),
        }
    except json.JSONDecodeError:
        debug(f"JSON解析失败: {content}")
        return {
            'content': {},
            'usage': result.get('usage'),
        }
