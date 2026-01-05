"""
AI模型服务调用

提供OpenAI兼容API的调用功能。
"""

import json
import re
import logging
from typing import Optional, Any, TypeVar, List

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from mspy.shared.env import ModelConfig, global_config_manager
from mspy.shared.env.types import (
    MIDSCENE_MODEL_MAX_TOKENS,
    MIDSCENE_LANGSMITH_DEBUG,
    MIDSCENE_LANGFUSE_DEBUG,
)
from mspy.shared.types import AIUsageInfo
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

logger = logging.getLogger("midscene.ai")
debug_call = get_debug("ai:call")
debug_profile_stats = get_debug("ai:profile:stats")


T = TypeVar("T")


async def create_chat_client(
    model_config: ModelConfig,
) -> tuple[AsyncOpenAI, str, str, Optional[str], Optional[str]]:
    """
    创建聊天客户端
    
    Args:
        model_config: 模型配置
        
    Returns:
        (client, model_name, model_description, vl_mode, ui_tars_version)
    """
    debug_proxy = get_debug("ai:call:proxy")
    
    # 处理代理 - 通过httpx配置
    http_proxy = model_config.http_proxy
    socks_proxy = model_config.socks_proxy
    
    # 构建http_client配置
    http_client = None
    if http_proxy:
        debug_proxy(f"Using HTTP proxy: {http_proxy[:20]}***")
        import httpx
        http_client = httpx.AsyncClient(proxy=http_proxy)
    elif socks_proxy:
        debug_proxy(f"Using SOCKS proxy: {socks_proxy[:20]}***")
        # SOCKS代理需要httpx-socks库支持
        logger.warning("SOCKS proxy support requires httpx-socks package")
    
    client = AsyncOpenAI(
        base_url=model_config.openai_base_url,
        api_key=model_config.openai_api_key,
        timeout=model_config.timeout / 1000 if model_config.timeout else None,
        http_client=http_client,
    )
    
    # 如果有自定义客户端创建函数，调用它
    if model_config.create_openai_client:
        client = await model_config.create_openai_client(client, {
            "base_url": model_config.openai_base_url,
            "api_key": model_config.openai_api_key,
        })
    
    return (
        client,
        model_config.model_name,
        model_config.model_description,
        model_config.vl_mode,
        model_config.ui_tars_model_version.value if model_config.ui_tars_model_version else None,
    )


def build_usage_info(
    usage: Optional[Any],
    time_cost: int,
    model_name: str,
    model_description: str,
    intent: str,
) -> Optional[AIUsageInfo]:
    """
    构建使用信息
    
    Args:
        usage: OpenAI返回的usage对象
        time_cost: 耗时（毫秒）
        model_name: 模型名称
        model_description: 模型描述
        intent: 意图
        
    Returns:
        AI使用信息
    """
    if not usage:
        return None
    
    cached_input = None
    if hasattr(usage, "prompt_tokens_details"):
        cached_input = getattr(usage.prompt_tokens_details, "cached_tokens", None)
    
    return AIUsageInfo(
        prompt_tokens=usage.prompt_tokens or 0,
        completion_tokens=usage.completion_tokens or 0,
        total_tokens=usage.total_tokens or 0,
        cached_input=cached_input or 0,
        time_cost=time_cost,
        model_name=model_name,
        model_description=model_description,
        intent=intent,
    )


async def call_ai(
    messages: List[ChatCompletionMessageParam],
    action_type: str,
    model_config: ModelConfig,
) -> tuple[str, Optional[AIUsageInfo]]:
    """
    调用AI模型
    
    Args:
        messages: 聊天消息列表
        action_type: 操作类型
        model_config: 模型配置
        
    Returns:
        (响应内容, 使用信息)
    """
    import time
    
    client, model_name, model_description, vl_mode, ui_tars_version = await create_chat_client(
        model_config
    )
    
    # 获取max_tokens配置
    max_tokens_str = global_config_manager.get_env_config_value(MIDSCENE_MODEL_MAX_TOKENS)
    max_tokens = int(max_tokens_str) if max_tokens_str else None
    
    temperature = model_config.temperature or 0
    
    start_time = time.time()
    
    try:
        debug_call(f"Sending request to {model_name}")
        
        # 构建请求参数
        request_params: dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        # 特殊模型配置
        if vl_mode == "qwen2.5-vl":
            request_params["extra_body"] = {"vl_high_resolution_images": True}
        
        result = await client.chat.completions.create(**request_params)
        
        time_cost = int((time.time() - start_time) * 1000)
        
        debug_profile_stats(
            f"model={model_name}, mode={vl_mode or 'default'}, "
            f"ui-tars-version={ui_tars_version or 'N/A'}, "
            f"prompt-tokens={result.usage.prompt_tokens if result.usage else ''}, "
            f"completion-tokens={result.usage.completion_tokens if result.usage else ''}, "
            f"cost-ms={time_cost}"
        )
        
        assert_condition(result.choices, f"Invalid response from LLM service: {result}")
        
        content = result.choices[0].message.content or ""
        
        debug_call(f"Response: {content[:200]}...")
        assert_condition(content, "Empty content from AI")
        
        usage_info = build_usage_info(
            result.usage,
            time_cost,
            model_name,
            model_description,
            model_config.intent,
        )
        
        return content, usage_info
    
    except Exception as e:
        logger.error(f"Call AI error: {e}")
        raise RuntimeError(
            f"Failed to call AI model service ({model_name}): {e}\n"
            "Trouble shooting: https://midscenejs.com/model-provider.html"
        ) from e


async def call_ai_with_object_response(
    messages: List[ChatCompletionMessageParam],
    action_type: str,
    model_config: ModelConfig,
) -> tuple[Any, str, Optional[AIUsageInfo]]:
    """
    调用AI并解析JSON响应
    
    Args:
        messages: 聊天消息列表
        action_type: 操作类型
        model_config: 模型配置
        
    Returns:
        (解析后的对象, 原始响应字符串, 使用信息)
    """
    content, usage = await call_ai(messages, action_type, model_config)
    
    json_content = safe_parse_json(content, model_config.vl_mode)
    assert_condition(
        isinstance(json_content, (dict, list)),
        f"Failed to parse JSON response from model ({model_config.model_name}): {content}"
    )
    
    return json_content, content, usage


async def call_ai_with_string_response(
    messages: List[ChatCompletionMessageParam],
    action_type: str,
    model_config: ModelConfig,
) -> tuple[str, Optional[AIUsageInfo]]:
    """
    调用AI并返回字符串响应
    
    Args:
        messages: 聊天消息列表
        action_type: 操作类型
        model_config: 模型配置
        
    Returns:
        (响应内容, 使用信息)
    """
    return await call_ai(messages, action_type, model_config)


def extract_json_from_code_block(response: str) -> str:
    """
    从代码块中提取JSON
    
    Args:
        response: 响应字符串
        
    Returns:
        提取的JSON字符串
    """
    # 尝试直接匹配JSON对象
    json_match = re.match(r"^\s*(\{[\s\S]*\})\s*$", response)
    if json_match:
        return json_match.group(1)
    
    # 尝试从代码块中提取
    code_block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response)
    if code_block_match:
        return code_block_match.group(1)
    
    # 尝试查找JSON结构
    json_like_match = re.search(r"\{[\s\S]*\}", response)
    if json_like_match:
        return json_like_match.group(0)
    
    return response


def preprocess_doubao_bbox_json(input_str: str) -> str:
    """
    预处理Doubao的bbox JSON
    
    某些模型返回的bbox格式为"940 445 969 490"，需要转换为"940,445,969,490"
    
    Args:
        input_str: 输入字符串
        
    Returns:
        处理后的字符串
    """
    if "bbox" in input_str:
        while re.search(r"\d+\s+\d+", input_str):
            input_str = re.sub(r"(\d+)\s+(\d+)", r"\1,\2", input_str)
    return input_str


def normalize_json_object(obj: Any) -> Any:
    """
    规范化JSON对象，移除键和值的前后空格
    
    Args:
        obj: JSON对象
        
    Returns:
        规范化后的对象
    """
    if obj is None:
        return obj
    
    if isinstance(obj, list):
        return [normalize_json_object(item) for item in obj]
    
    if isinstance(obj, dict):
        normalized = {}
        for key, value in obj.items():
            trimmed_key = key.strip() if isinstance(key, str) else key
            normalized_value = normalize_json_object(value)
            if isinstance(normalized_value, str):
                normalized_value = normalized_value.strip()
            normalized[trimmed_key] = normalized_value
        return normalized
    
    if isinstance(obj, str):
        return obj.strip()
    
    return obj


def safe_parse_json(input_str: str, vl_mode: Optional[str]) -> Any:
    """
    安全解析JSON
    
    Args:
        input_str: JSON字符串
        vl_mode: VL模式
        
    Returns:
        解析后的对象
        
    Raises:
        ValueError: 如果解析失败
    """
    clean_json_string = extract_json_from_code_block(input_str)
    
    # 检查是否是坐标格式 (x,y)
    point_match = re.search(r"\((\d+),(\d+)\)", clean_json_string)
    if point_match:
        return [int(point_match.group(1)), int(point_match.group(2))]
    
    last_error: Optional[Exception] = None
    
    # 尝试直接解析
    try:
        parsed = json.loads(clean_json_string)
        return normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        last_error = e
    
    # 对于特定模型，尝试预处理
    if vl_mode in ("doubao-vision", "vlm-ui-tars"):
        json_string = preprocess_doubao_bbox_json(clean_json_string)
        try:
            parsed = json.loads(json_string)
            return normalize_json_object(parsed)
        except json.JSONDecodeError as e:
            last_error = e
    
    raise ValueError(
        f"Failed to parse LLM response into JSON. Error: {last_error}. "
        f"Response:\n{input_str}"
    )
