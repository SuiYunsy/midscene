"""
AI 模型服务调用模块
AI model service caller module
"""
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Callable

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from ..shared import (
    get_debug,
    ModelConfig,
    AIUsageInfo,
    assert_condition,
)

debug = get_debug("ai:call")


def create_chat_client(
    model_config: ModelConfig,
) -> Tuple[OpenAI, str, Optional[str]]:
    """
    Create OpenAI chat client with proxy support.
    创建支持代理的OpenAI聊天客户端
    """
    http_proxy = model_config.http_proxy
    socks_proxy = model_config.socks_proxy
    
    # 构建客户端参数
    client_kwargs: Dict[str, Any] = {
        "api_key": model_config.openai_api_key or "EMPTY",
        "base_url": model_config.openai_base_url,
    }
    
    # 处理超时
    if model_config.timeout:
        client_kwargs["timeout"] = model_config.timeout
    
    # 处理HTTP代理
    if http_proxy:
        debug.info(f"Using HTTP proxy: {_sanitize_proxy_url(http_proxy)}")
        try:
            from httpx import Client
            http_client = Client(proxy=http_proxy)
            client_kwargs["http_client"] = http_client
        except ImportError:
            debug.warning("httpx not available, HTTP proxy will not be used")
    
    client = OpenAI(**client_kwargs)
    
    return client, model_config.model_name, model_config.vl_mode


def _sanitize_proxy_url(url: str) -> str:
    """Sanitize proxy URL for logging (hide credentials)."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        if parsed.password:
            # Replace password with asterisks
            netloc = f"{parsed.username}:****@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return url


def call_ai(
    messages: List[ChatCompletionMessageParam],
    model_config: ModelConfig,
) -> Dict[str, Any]:
    """
    Call AI model with messages.
    调用AI模型
    
    Args:
        messages: Chat messages
        model_config: Model configuration
        
    Returns:
        Dict with content and usage info
    """
    client, model_name, vl_mode = create_chat_client(model_config)
    
    temperature = model_config.temperature or 0
    
    start_time = time.time()
    debug.info(f"Sending request to {model_name}")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        content = response.choices[0].message.content
        assert_condition(content, "Empty content from AI response")
        
        usage = response.usage
        usage_info = None
        if usage:
            usage_info = AIUsageInfo(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                total_tokens=usage.total_tokens or 0,
                cached_input=0,
                time_cost=time_cost,
                model_name=model_name,
                model_description=model_config.model_description,
                intent=model_config.intent,
            )
        
        debug.info(f"Response received, time_cost={time_cost}ms")
        
        return {
            "content": content,
            "usage": usage_info,
            "is_streamed": False,
        }
    except Exception as e:
        debug.error(f"AI call error: {e}")
        raise RuntimeError(
            f"Failed to call AI model ({model_name}): {e}. "
            "Troubleshooting: https://midscenejs.com/model-provider.html"
        ) from e


def extract_json_from_code_block(response: str) -> str:
    """
    Extract JSON from code block in response.
    从响应中的代码块提取JSON
    """
    import re
    
    # 首先尝试直接匹配JSON对象
    json_match = re.match(r'^\s*(\{[\s\S]*\})\s*$', response)
    if json_match:
        return json_match.group(1)
    
    # 从代码块中提取
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if code_block_match:
        return code_block_match.group(1)
    
    # 查找类JSON结构
    json_like_match = re.search(r'\{[\s\S]*\}', response)
    if json_like_match:
        return json_like_match.group(0)
    
    return response


def safe_parse_json(input_str: str, vl_mode: Optional[str] = None) -> Any:
    """
    Safely parse JSON from AI response.
    安全解析AI响应中的JSON
    """
    clean_json_string = extract_json_from_code_block(input_str)
    
    # 尝试直接解析
    try:
        result = json.loads(clean_json_string)
        return _normalize_json_object(result)
    except json.JSONDecodeError:
        pass
    
    # 尝试修复后解析
    try:
        # 移除可能的尾部逗号
        fixed = clean_json_string.replace(",}", "}").replace(",]", "]")
        result = json.loads(fixed)
        return _normalize_json_object(result)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response into JSON. Error - {e}. Response - {input_str}"
        ) from e


def _normalize_json_object(obj: Any) -> Any:
    """
    Normalize JSON object by trimming whitespace.
    规范化JSON对象，去除空白
    """
    if obj is None:
        return obj
    
    if isinstance(obj, list):
        return [_normalize_json_object(item) for item in obj]
    
    if isinstance(obj, dict):
        return {
            k.strip() if isinstance(k, str) else k: (
                v.strip() if isinstance(v, str) else _normalize_json_object(v)
            )
            for k, v in obj.items()
        }
    
    if isinstance(obj, str):
        return obj.strip()
    
    return obj


def call_ai_with_object_response(
    messages: List[ChatCompletionMessageParam],
    model_config: ModelConfig,
) -> Dict[str, Any]:
    """
    Call AI and parse response as JSON object.
    调用AI并将响应解析为JSON对象
    """
    response = call_ai(messages, model_config)
    content = response["content"]
    
    json_content = safe_parse_json(content, model_config.vl_mode)
    assert_condition(
        isinstance(json_content, dict),
        f"Failed to parse JSON response from model ({model_config.model_name}): {content}"
    )
    
    return {
        "content": json_content,
        "content_string": content,
        "usage": response.get("usage"),
    }
