# -*- coding: utf-8 -*-
"""
AI 服务调用模块
提供调用 AI 模型的功能，支持 OpenAI 兼容的 API。
"""

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union
from dataclasses import dataclass

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from mspy.shared.types import AIUsageInfo
from mspy.shared.env import IModelConfig, global_config_manager
from mspy.shared.env.constants import MIDSCENE_MODEL_MAX_TOKENS, OPENAI_MAX_TOKENS
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

debug_call = get_debug("ai:call")
debug_profile_stats = get_debug("ai:profile:stats")
debug_profile_detail = get_debug("ai:profile:detail")


class AIActionType:
    """AI 动作类型枚举"""
    ASSERT = 0
    INSPECT_ELEMENT = 1
    EXTRACT_DATA = 2
    PLAN = 3
    DESCRIBE_ELEMENT = 4
    TEXT = 5


@dataclass
class AICallResult:
    """AI 调用结果"""
    content: str
    usage: Optional[AIUsageInfo] = None
    is_streamed: bool = False


T = TypeVar("T")


async def create_chat_client(
    ai_action_type: int,
    model_config: IModelConfig
) -> Tuple[OpenAI, str, str, Optional[str], Optional[str]]:
    """
    创建聊天客户端
    
    Args:
        ai_action_type: AI 动作类型
        model_config: 模型配置
        
    Returns:
        (OpenAI 客户端, 模型名称, 模型描述, UI-TARS 版本, VL 模式)
    """
    openai_options = {
        "base_url": model_config.openai_base_url,
        "api_key": model_config.openai_api_key,
    }
    
    if model_config.timeout:
        openai_options["timeout"] = model_config.timeout
    
    if model_config.openai_extra_config:
        openai_options.update(model_config.openai_extra_config)
    
    client = OpenAI(**openai_options)
    
    # 如果有自定义客户端创建函数，调用它
    if model_config.create_openai_client:
        wrapped_client = await model_config.create_openai_client(client, openai_options)
        if wrapped_client:
            client = wrapped_client
    
    return (
        client,
        model_config.model_name,
        model_config.model_description,
        model_config.ui_tars_model_version,
        model_config.vl_mode,
    )


def build_usage_info(
    usage_data: Optional[Dict[str, Any]],
    time_cost: Optional[float],
    model_name: str,
    model_description: str,
    intent: str
) -> Optional[AIUsageInfo]:
    """
    构建使用信息
    
    Args:
        usage_data: 原始使用数据
        time_cost: 耗时
        model_name: 模型名称
        model_description: 模型描述
        intent: 意图
        
    Returns:
        AI 使用信息
    """
    if not usage_data:
        return None
    
    cached_input = None
    if "prompt_tokens_details" in usage_data:
        cached_input = usage_data["prompt_tokens_details"].get("cached_tokens")
    
    return AIUsageInfo(
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0),
        cached_input=cached_input or 0,
        time_cost=time_cost or 0,
        model_name=model_name,
        model_description=model_description,
        intent=intent,
    )


async def call_ai(
    messages: List[ChatCompletionMessageParam],
    ai_action_type: int,
    model_config: IModelConfig,
    stream: bool = False,
    on_chunk: Optional[Callable] = None,
) -> AICallResult:
    """
    调用 AI 模型
    
    Args:
        messages: 消息列表
        ai_action_type: AI 动作类型
        model_config: 模型配置
        stream: 是否流式输出
        on_chunk: 流式输出回调函数
        
    Returns:
        AI 调用结果
    """
    client, model_name, model_description, ui_tars_version, vl_mode = await create_chat_client(
        ai_action_type, model_config
    )
    
    # 获取最大 token 数
    max_tokens_str = global_config_manager.get_env_config_value(MIDSCENE_MODEL_MAX_TOKENS)
    if not max_tokens_str:
        max_tokens_str = global_config_manager.get_env_config_value(OPENAI_MAX_TOKENS)
    max_tokens = int(max_tokens_str) if max_tokens_str else None
    
    start_time = time.time()
    temperature = model_config.temperature or 0
    
    is_streaming = stream and on_chunk is not None
    
    common_config = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    
    if max_tokens:
        common_config["max_tokens"] = max_tokens
    
    # Qwen VL v2 特定配置
    if vl_mode == "qwen2.5-vl":
        common_config["extra_body"] = {"vl_high_resolution_images": True}
    
    try:
        debug_call(f"sending {'streaming ' if is_streaming else ''}request to {model_name}")
        
        if is_streaming:
            # 流式处理
            accumulated = ""
            usage = None
            
            stream_response = client.chat.completions.create(
                **common_config,
                stream=True,
            )
            
            for chunk in stream_response:
                content = ""
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                
                if hasattr(chunk, "usage") and chunk.usage:
                    usage = chunk.usage.model_dump() if hasattr(chunk.usage, "model_dump") else dict(chunk.usage)
                
                if content:
                    accumulated += content
                    if on_chunk:
                        on_chunk({
                            "content": content,
                            "accumulated": accumulated,
                            "is_complete": False,
                        })
                
                if chunk.choices and chunk.choices[0].finish_reason:
                    time_cost = time.time() - start_time
                    if on_chunk:
                        on_chunk({
                            "content": "",
                            "accumulated": accumulated,
                            "is_complete": True,
                        })
                    break
            
            content = accumulated
            
        else:
            # 非流式处理
            result = client.chat.completions.create(**common_config)
            time_cost = time.time() - start_time
            
            debug_profile_stats(
                f"model, {model_name}, mode, {vl_mode or 'default'}, "
                f"ui-tars-version, {ui_tars_version}, "
                f"prompt-tokens, {result.usage.prompt_tokens if result.usage else ''}, "
                f"completion-tokens, {result.usage.completion_tokens if result.usage else ''}, "
                f"total-tokens, {result.usage.total_tokens if result.usage else ''}, "
                f"cost-ms, {int(time_cost * 1000)}, temperature, {temperature}"
            )
            
            assert_condition(result.choices, f"invalid response from LLM service: {result}")
            content = result.choices[0].message.content or ""
            usage = result.usage.model_dump() if result.usage else None
        
        debug_call(f"response: {content}")
        assert_condition(content, "empty content")
        
        return AICallResult(
            content=content,
            usage=build_usage_info(
                usage, time_cost, model_name, model_description, model_config.intent
            ),
            is_streamed=is_streaming,
        )
        
    except Exception as e:
        print(f"call AI error: {e}")
        raise RuntimeError(
            f"failed to call {'streaming ' if is_streaming else ''}AI model service ({model_name}): {e}\n"
            "Trouble shooting: https://midscenejs.com/model-provider.html"
        ) from e


def extract_json_from_code_block(response: str) -> str:
    """
    从代码块中提取 JSON
    
    Args:
        response: 原始响应
        
    Returns:
        提取的 JSON 字符串
    """
    try:
        # 首先尝试直接匹配 JSON 对象
        json_match = re.match(r'^\s*(\{[\s\S]*\})\s*$', response)
        if json_match:
            return json_match.group(1)
        
        # 尝试从代码块中提取
        code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
        if code_block_match:
            return code_block_match.group(1)
        
        # 尝试找到类似 JSON 的结构
        json_like_match = re.search(r'\{[\s\S]*\}', response)
        if json_like_match:
            return json_like_match.group(0)
    except Exception:
        pass
    
    return response


def preprocess_doubao_bbox_json(input_str: str) -> str:
    """
    预处理豆包模型的 bbox JSON
    
    Args:
        input_str: 输入字符串
        
    Returns:
        处理后的字符串
    """
    if "bbox" in input_str:
        # 当值类似 "940 445 969 490" 时，替换为逗号分隔
        while re.search(r'\d+\s+\d+', input_str):
            input_str = re.sub(r'(\d+)\s+(\d+)', r'\1,\2', input_str)
    return input_str


def normalize_json_object(obj: Any) -> Any:
    """
    标准化 JSON 对象，去除键和值的空白
    
    Args:
        obj: 要标准化的对象
        
    Returns:
        标准化后的对象
    """
    if obj is None:
        return obj
    
    if isinstance(obj, list):
        return [normalize_json_object(item) for item in obj]
    
    if isinstance(obj, dict):
        return {
            key.strip(): normalize_json_object(value)
            for key, value in obj.items()
        }
    
    if isinstance(obj, str):
        return obj.strip()
    
    return obj


def safe_parse_json(input_str: str, vl_mode: Optional[str]) -> Any:
    """
    安全解析 JSON
    
    Args:
        input_str: 输入字符串
        vl_mode: VL 模式
        
    Returns:
        解析后的对象
    """
    clean_json_string = extract_json_from_code_block(input_str)
    
    # 匹配坐标点格式
    point_match = re.search(r'\((\d+),(\d+)\)', clean_json_string)
    if point_match:
        return [int(point_match.group(1)), int(point_match.group(2))]
    
    last_error = None
    
    # 尝试直接解析
    try:
        parsed = json.loads(clean_json_string)
        return normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        last_error = e
    
    # 对于豆包模型，尝试预处理
    if vl_mode in ("doubao-vision", "vlm-ui-tars"):
        json_string = preprocess_doubao_bbox_json(clean_json_string)
        try:
            parsed = json.loads(json_string)
            return normalize_json_object(parsed)
        except json.JSONDecodeError as e:
            last_error = e
    
    raise ValueError(
        f"failed to parse LLM response into JSON. Error - {last_error}. Response - \n {input_str}"
    )


async def call_ai_with_object_response(
    messages: List[ChatCompletionMessageParam],
    ai_action_type: int,
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用 AI 并返回对象响应
    
    Args:
        messages: 消息列表
        ai_action_type: AI 动作类型
        model_config: 模型配置
        
    Returns:
        包含 content, contentString, usage 的字典
    """
    response = await call_ai(messages, ai_action_type, model_config)
    assert_condition(response, "empty response")
    
    vl_mode = model_config.vl_mode
    json_content = safe_parse_json(response.content, vl_mode)
    
    assert_condition(
        isinstance(json_content, (dict, list)),
        f"failed to parse json response from model ({model_config.model_name}): {response.content}"
    )
    
    return {
        "content": json_content,
        "content_string": response.content,
        "usage": response.usage,
    }


async def call_ai_with_string_response(
    messages: List[ChatCompletionMessageParam],
    ai_action_type: int,
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用 AI 并返回字符串响应
    
    Args:
        messages: 消息列表
        ai_action_type: AI 动作类型
        model_config: 模型配置
        
    Returns:
        包含 content, usage 的字典
    """
    result = await call_ai(messages, ai_action_type, model_config)
    return {
        "content": result.content,
        "usage": result.usage,
    }
