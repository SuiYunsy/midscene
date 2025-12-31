# -*- coding: utf-8 -*-
"""
Midscene Service Caller Module
AI服务调用模块，负责与OpenAI兼容的API进行通信
"""

import json
import ssl
import httpx
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time
import re

from ..shared import (
    get_logger,
    ModelConfig,
    AIUsageInfo,
    assert_condition,
)

logger = get_logger("ai:call")


def _mask_base64_in_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    遮蔽消息中的base64图像数据，用于日志输出
    - system的text打印前50个字符，超出则省略号
    - user、assistant的text全部保留
    - image_url的base64用masked替代
    """
    masked = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content")
        
        if isinstance(content, str):
            # 字符串内容
            if role == "system":
                if len(content) > 50:
                    masked.append({"role": role, "content": content[:50] + "..."})
                else:
                    masked.append({"role": role, "content": content})
            else:
                masked.append({"role": role, "content": content})
        elif isinstance(content, list):
            # 数组内容
            masked_content = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    if item_type == "image_url":
                        image_url = item.get("image_url", {})
                        if isinstance(image_url, dict):
                            url = image_url.get("url", "")
                            if url and ("base64" in url or len(url) > 200):
                                masked_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": "base64 is masked", "detail": image_url.get("detail", "auto")}
                                })
                            else:
                                masked_content.append(item)
                        else:
                            masked_content.append(item)
                    elif item_type == "text":
                        text = item.get("text", "")
                        if role == "system" and len(text) > 50:
                            masked_content.append({"type": "text", "text": text[:50] + "..."})
                        else:
                            masked_content.append(item)
                    else:
                        masked_content.append(item)
                else:
                    masked_content.append(item)
            masked.append({"role": role, "content": masked_content})
        else:
            masked.append(msg)
    
    return masked


def _extract_json_from_code_block(response: str) -> str:
    """
    从响应中提取JSON内容
    """
    # 首先尝试直接匹配JSON对象
    json_match = re.match(r'^\s*(\{[\s\S]*\})\s*$', response)
    if json_match:
        return json_match.group(1)
    
    # 尝试从代码块中提取
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if code_block_match:
        return code_block_match.group(1)
    
    # 尝试查找类似JSON的结构
    json_like_match = re.search(r'\{[\s\S]*\}', response)
    if json_like_match:
        return json_like_match.group(0)
    
    return response


def _safe_parse_json(input_str: str) -> Any:
    """
    安全解析JSON，处理可能的格式问题
    """
    clean_json = _extract_json_from_code_block(input_str)
    
    # 首先尝试直接解析
    try:
        return json.loads(clean_json)
    except json.JSONDecodeError:
        pass
    
    # 尝试修复常见问题后再解析
    # 移除可能的尾部逗号
    fixed = re.sub(r',\s*}', '}', clean_json)
    fixed = re.sub(r',\s*]', ']', fixed)
    
    try:
        return json.loads(fixed)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response into JSON. Error - {str(e)}. Response - \n{input_str}"
        )


def _normalize_json_object(obj: Any) -> Any:
    """
    标准化JSON对象，去除键和值中的空白
    """
    if obj is None:
        return obj
    
    if isinstance(obj, list):
        return [_normalize_json_object(item) for item in obj]
    
    if isinstance(obj, dict):
        normalized = {}
        for key, value in obj.items():
            trimmed_key = key.strip() if isinstance(key, str) else key
            normalized_value = _normalize_json_object(value)
            if isinstance(normalized_value, str):
                normalized_value = normalized_value.strip()
            normalized[trimmed_key] = normalized_value
        return normalized
    
    if isinstance(obj, str):
        return obj.strip()
    
    return obj


async def call_ai(
    messages: List[Dict[str, Any]],
    model_config: ModelConfig,
) -> Dict[str, Any]:
    """
    调用AI模型服务
    
    Args:
        messages: 消息列表
        model_config: 模型配置
    
    Returns:
        包含content和usage的字典
    """
    # 打印请求日志（遮蔽base64）
    masked_messages = _mask_base64_in_messages(messages)
    logger.info(f"Request messages: {json.dumps(masked_messages, ensure_ascii=False)}")
    
    # 构建请求
    model_name = model_config.model_name
    base_url = model_config.openai_base_url or "https://api.openai.com/v1"
    api_key = model_config.openai_api_key or ""
    http_proxy = model_config.http_proxy
    timeout = model_config.timeout or 600000  # 默认10分钟
    temperature = model_config.temperature if model_config.temperature is not None else 0
    max_tokens = model_config.max_tokens
    skip_cert = model_config.skip_cert_verification
    
    # 确保base_url以正确的路径结尾
    if not base_url.endswith("/"):
        base_url += "/"
    if not base_url.endswith("v1/"):
        if "v1" not in base_url:
            base_url += "v1/"
    
    url = f"{base_url}chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    request_body = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    
    if max_tokens:
        request_body["max_tokens"] = max_tokens
    
    # 配置HTTP客户端
    ssl_context = None
    if skip_cert:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    client_kwargs = {
        "timeout": httpx.Timeout(timeout / 1000.0),  # 转换为秒
    }
    
    if skip_cert:
        client_kwargs["verify"] = False
    
    if http_proxy:
        client_kwargs["proxy"] = http_proxy
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.post(
                url,
                headers=headers,
                json=request_body,
            )
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error calling AI model service ({model_name}): {str(e)}")
        raise RuntimeError(
            f"Failed to call AI model service ({model_name}): {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error calling AI model service ({model_name}): {str(e)}")
        raise RuntimeError(
            f"Failed to call AI model service ({model_name}): {str(e)}"
        )
    
    time_cost = int((time.time() - start_time) * 1000)
    
    # 解析响应
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"Invalid response from LLM service: {json.dumps(result)}")
    
    content = choices[0].get("message", {}).get("content", "")
    usage_data = result.get("usage", {})
    
    # 打印响应日志
    logger.info(f"Response content: {content}")
    
    usage = AIUsageInfo(
        prompt_tokens=usage_data.get("prompt_tokens"),
        completion_tokens=usage_data.get("completion_tokens"),
        total_tokens=usage_data.get("total_tokens"),
        cached_input=usage_data.get("prompt_tokens_details", {}).get("cached_tokens"),
        time_cost=time_cost,
        model_name=model_name,
        model_description=model_config.model_description,
        intent=model_config.intent,
    )
    
    return {
        "content": content,
        "usage": usage,
    }


async def call_ai_with_object_response(
    messages: List[Dict[str, Any]],
    model_config: ModelConfig,
) -> Dict[str, Any]:
    """
    调用AI并解析为JSON对象响应
    
    Args:
        messages: 消息列表
        model_config: 模型配置
    
    Returns:
        包含content (解析后的对象)、contentString和usage的字典
    """
    response = await call_ai(messages, model_config)
    
    content_str = response["content"]
    usage = response["usage"]
    
    try:
        parsed = _safe_parse_json(content_str)
        normalized = _normalize_json_object(parsed)
    except ValueError as e:
        raise RuntimeError(
            f"Failed to parse json response from model ({model_config.model_name}): {content_str}"
        )
    
    return {
        "content": normalized,
        "contentString": content_str,
        "usage": usage,
    }
