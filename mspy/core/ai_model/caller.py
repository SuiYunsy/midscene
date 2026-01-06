"""
AI模型调用器

从 packages/core/src/ai-model/service-caller/index.ts 迁移
"""

import json
import re
import time
from typing import Any, Optional, TypeVar

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from mspy.core.types import AIUsageInfo
from mspy.shared.env import (
    MIDSCENE_MODEL_MAX_TOKENS,
    global_config_manager,
)
from mspy.shared.env.types import ModelConfig
from mspy.shared.logger import get_debug


_debug_call = get_debug("ai:call")
_debug_profile = get_debug("ai:profile:stats")

T = TypeVar("T")


async def _create_chat_client(
    model_config: ModelConfig
) -> tuple[OpenAI, str]:
    """
    创建聊天客户端
    
    Args:
        model_config: 模型配置
    
    Returns:
        (OpenAI客户端, 模型名称)
    """
    # 构建OpenAI客户端参数
    client_kwargs: dict[str, Any] = {
        "api_key": model_config.openai_api_key,
    }
    
    if model_config.openai_base_url:
        client_kwargs["base_url"] = model_config.openai_base_url
    
    if model_config.timeout:
        client_kwargs["timeout"] = model_config.timeout / 1000  # 转换为秒
    
    # 合并额外配置
    if model_config.openai_extra_config:
        client_kwargs.update(model_config.openai_extra_config)
    
    # 创建基础客户端
    base_client = OpenAI(**client_kwargs)
    
    # 如果有自定义客户端工厂，使用它
    if model_config.create_openai_client:
        client = await model_config.create_openai_client(
            base_client,
            client_kwargs
        )
        if client:
            return client, model_config.model_name
    
    return base_client, model_config.model_name


async def call_ai(
    messages: list[ChatCompletionMessageParam],
    action_type: str,
    model_config: ModelConfig,
    stream: bool = False,
    on_chunk: Optional[Any] = None,
) -> dict[str, Any]:
    """
    调用AI模型
    
    Args:
        messages: 消息列表
        action_type: 动作类型
        model_config: 模型配置
        stream: 是否流式响应
        on_chunk: 流式响应回调
    
    Returns:
        {"content": str, "usage": AIUsageInfo, "is_streamed": bool}
    """
    client, model_name = await _create_chat_client(model_config)
    
    # 获取最大token数
    max_tokens_str = global_config_manager.get_env_config_value(
        MIDSCENE_MODEL_MAX_TOKENS
    )
    max_tokens = int(max_tokens_str) if max_tokens_str else None
    
    temperature = model_config.temperature if model_config.temperature is not None else 0
    
    start_time = time.time()
    _debug_call(f"sending request to {model_name}")
    
    try:
        # 构建请求参数
        request_kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            request_kwargs["max_tokens"] = max_tokens
        
        # 特殊模型配置
        if model_config.vl_mode == "qwen2.5-vl":
            request_kwargs["extra_body"] = {"vl_high_resolution_images": True}
        
        # 非流式请求
        response = client.chat.completions.create(**request_kwargs)
        
        time_cost = int((time.time() - start_time) * 1000)
        
        _debug_profile(
            f"model, {model_name}, "
            f"mode, {model_config.vl_mode or 'default'}, "
            f"prompt-tokens, {response.usage.prompt_tokens if response.usage else ''}, "
            f"completion-tokens, {response.usage.completion_tokens if response.usage else ''}, "
            f"total-tokens, {response.usage.total_tokens if response.usage else ''}, "
            f"cost-ms, {time_cost}"
        )
        
        # 检查响应是否有效
        if not response.choices or len(response.choices) == 0:
            raise ValueError(f"empty choices in AI response from {model_name}")
        
        content = response.choices[0].message.content or ""
        
        if not content:
            raise ValueError("empty content from AI response")
        
        _debug_call(f"response: {content[:200]}...")
        
        # 构建使用信息
        usage: Optional[AIUsageInfo] = None
        if response.usage:
            usage = AIUsageInfo(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                time_cost=time_cost,
                model_name=model_name,
                model_description=model_config.model_description,
                intent=model_config.intent,
            )
        
        return {
            "content": content,
            "usage": usage,
            "is_streamed": False,
        }
        
    except Exception as e:
        raise RuntimeError(
            f"failed to call AI model service ({model_name}): {e}\n"
            f"Trouble shooting: https://midscenejs.com/model-provider.html"
        ) from e


def _extract_json_from_code_block(response: str) -> str:
    """从代码块中提取JSON"""
    # 尝试直接匹配JSON对象
    json_match = re.match(r"^\s*(\{[\s\S]*\})\s*$", response)
    if json_match:
        return json_match.group(1)
    
    # 从代码块中提取
    code_block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
    if code_block_match:
        return code_block_match.group(1)
    
    # 查找JSON结构
    json_like_match = re.search(r"\{[\s\S]*\}", response)
    if json_like_match:
        return json_like_match.group(0)
    
    return response


def _normalize_json_object(obj: Any) -> Any:
    """规范化JSON对象（去除键值中的空白）"""
    if obj is None:
        return obj
    
    if isinstance(obj, list):
        return [_normalize_json_object(item) for item in obj]
    
    if isinstance(obj, dict):
        normalized = {}
        for key, value in obj.items():
            trimmed_key = key.strip()
            normalized_value = _normalize_json_object(value)
            if isinstance(normalized_value, str):
                normalized_value = normalized_value.strip()
            normalized[trimmed_key] = normalized_value
        return normalized
    
    if isinstance(obj, str):
        return obj.strip()
    
    return obj


def _safe_parse_json(input_str: str, vl_mode: Optional[str] = None) -> Any:
    """安全解析JSON"""
    clean_json = _extract_json_from_code_block(input_str)
    
    # 检查是否是坐标格式 (x,y)
    point_match = re.match(r"\((\d+),(\d+)\)", clean_json)
    if point_match:
        return [int(point_match.group(1)), int(point_match.group(2))]
    
    try:
        parsed = json.loads(clean_json)
        return _normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        # 尝试修复常见问题
        try:
            # 尝试修复尾随逗号等问题
            import ast
            parsed = ast.literal_eval(clean_json)
            return _normalize_json_object(parsed)
        except Exception:
            pass
        
        raise ValueError(
            f"failed to parse LLM response into JSON. "
            f"Error - {e}. Response - \n{input_str}"
        )


async def call_ai_with_object_response(
    messages: list[ChatCompletionMessageParam],
    action_type: str,
    model_config: ModelConfig,
) -> dict[str, Any]:
    """
    调用AI并解析JSON响应
    
    Returns:
        {"content": 解析后的对象, "content_string": 原始字符串, "usage": AIUsageInfo}
    """
    response = await call_ai(messages, action_type, model_config)
    
    if not response:
        raise ValueError("empty response")
    
    json_content = _safe_parse_json(
        response["content"],
        model_config.vl_mode
    )
    
    if not isinstance(json_content, (dict, list)):
        raise ValueError(
            f"failed to parse json response from model "
            f"({model_config.model_name}): {response['content']}"
        )
    
    return {
        "content": json_content,
        "content_string": response["content"],
        "usage": response.get("usage"),
    }


async def call_ai_with_string_response(
    messages: list[ChatCompletionMessageParam],
    action_type: str,
    model_config: ModelConfig,
) -> dict[str, Any]:
    """
    调用AI并返回字符串响应
    
    Returns:
        {"content": str, "usage": AIUsageInfo}
    """
    response = await call_ai(messages, action_type, model_config)
    return {
        "content": response["content"],
        "usage": response.get("usage"),
    }
