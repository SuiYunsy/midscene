"""
AI模型服务调用模块
AI model service caller for Midscene Python SDK
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic
from dataclasses import dataclass

from ..shared import (
    get_debug,
    log_request_response,
    IModelConfig,
    AIUsageInfo,
)

debug = get_debug("ai:call")
debug_profile = get_debug("ai:profile:stats")

T = TypeVar('T')


@dataclass
class AIResponse(Generic[T]):
    """AI响应结果"""
    content: T
    content_string: str
    usage: Optional[AIUsageInfo] = None


async def call_ai(
    messages: List[Dict[str, Any]],
    ai_action_type: str,
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用AI模型
    
    Args:
        messages: 消息列表
        ai_action_type: AI动作类型
        model_config: 模型配置
        
    Returns:
        包含content、usage等的字典
    """
    try:
        import httpx
    except ImportError:
        raise ImportError("httpx is required. Install with: pip install httpx")
    
    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("openai is required. Install with: pip install openai")
    
    model_name = model_config.model_name
    base_url = model_config.openai_base_url
    api_key = model_config.openai_api_key
    temperature = model_config.temperature or 0
    timeout = model_config.timeout
    skip_cert = model_config.skip_cert_verification
    http_proxy = model_config.http_proxy
    
    debug(f"Calling AI model: {model_name} at {base_url}")
    
    # 配置HTTP客户端
    http_client_kwargs = {}
    
    if skip_cert:
        debug("Skip certificate verification enabled")
        http_client_kwargs['verify'] = False
    
    if http_proxy:
        debug(f"Using HTTP proxy: {http_proxy}")
        http_client_kwargs['proxy'] = http_proxy
    
    # 创建HTTP客户端
    if http_client_kwargs:
        http_client = httpx.AsyncClient(**http_client_kwargs)
    else:
        http_client = None
    
    # 创建OpenAI客户端
    client_kwargs = {
        'base_url': base_url,
        'api_key': api_key,
    }
    
    if http_client:
        client_kwargs['http_client'] = http_client
    
    if timeout:
        client_kwargs['timeout'] = timeout
    
    client = AsyncOpenAI(**client_kwargs)
    
    # 记录请求日志
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        if isinstance(content, str):
            log_request_response(role, content)
        elif isinstance(content, list):
            for item in content:
                if item.get('type') == 'text':
                    log_request_response(role, item.get('text', ''))
    
    try:
        import time
        start_time = time.time()
        
        # 调用API
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        content = response.choices[0].message.content
        usage_data = response.usage
        
        debug(f"AI response received, time_cost={time_cost}ms")
        
        # 记录响应日志
        if content:
            log_request_response('assistant', content)
        
        # 构建usage信息
        usage = None
        if usage_data:
            usage = AIUsageInfo(
                prompt_tokens=usage_data.prompt_tokens,
                completion_tokens=usage_data.completion_tokens,
                total_tokens=usage_data.total_tokens,
                time_cost=time_cost,
                model_name=model_name,
                model_description=model_config.model_description,
                intent=model_config.intent,
            )
        
        return {
            'content': content or '',
            'usage': usage,
            'is_streamed': False,
        }
        
    finally:
        if http_client:
            await http_client.aclose()
        await client.close()


def extract_json_from_code_block(response: str) -> str:
    """
    从代码块中提取JSON
    
    支持以下提取模式（按优先级顺序）：
    1. 直接匹配：如果响应本身就是一个JSON对象（可能有首尾空白）
    2. 代码块提取：从 ```json {...} ``` 或 ``` {...} ``` 格式中提取
    3. 模糊匹配：在响应文本中查找类似JSON的结构（{...}）
    
    Args:
        response: AI响应文本
        
    Returns:
        提取出的JSON字符串，如果没有找到则返回原始响应
    """
    # 尝试直接匹配JSON对象
    json_match = re.match(r'^\s*(\{[\s\S]*\})\s*$', response)
    if json_match:
        return json_match.group(1)
    
    # 尝试从代码块中提取
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if code_block_match:
        return code_block_match.group(1)
    
    # 尝试找到类JSON结构
    json_like_match = re.search(r'\{[\s\S]*\}', response)
    if json_like_match:
        return json_like_match.group(0)
    
    return response


def normalize_json_object(obj: Any) -> Any:
    """
    规范化JSON对象，清理键值中的空白
    
    Args:
        obj: 要规范化的对象
        
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


def safe_parse_json(input_str: str, vl_mode: Optional[str] = None) -> Any:
    """
    安全解析JSON
    
    Args:
        input_str: 输入字符串
        vl_mode: VL模式
        
    Returns:
        解析后的对象
        
    Raises:
        ValueError: 解析失败时
    """
    clean_json_str = extract_json_from_code_block(input_str)
    
    # 检查是否是坐标点格式
    point_match = re.search(r'\((\d+),(\d+)\)', clean_json_str)
    if point_match:
        return [int(point_match.group(1)), int(point_match.group(2))]
    
    last_error = None
    
    # 尝试直接解析
    try:
        parsed = json.loads(clean_json_str)
        return normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        last_error = e
    
    # 尝试修复JSON
    try:
        # 移除尾部逗号
        fixed = re.sub(r',\s*([}\]])', r'\1', clean_json_str)
        # 修复单引号
        fixed = fixed.replace("'", '"')
        parsed = json.loads(fixed)
        return normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        last_error = e
    
    raise ValueError(
        f"Failed to parse LLM response into JSON. Error - {str(last_error)}. "
        f"Response - \n {input_str}"
    )


async def call_ai_with_object_response(
    messages: List[Dict[str, Any]],
    ai_action_type: str,
    model_config: IModelConfig,
) -> AIResponse:
    """
    调用AI并返回对象响应
    
    Args:
        messages: 消息列表
        ai_action_type: AI动作类型
        model_config: 模型配置
        
    Returns:
        AIResponse对象
    """
    response = await call_ai(messages, ai_action_type, model_config)
    
    content_str = response['content']
    if not content_str:
        raise ValueError("Empty response from AI")
    
    vl_mode = model_config.vl_mode
    json_content = safe_parse_json(content_str, vl_mode)
    
    if not isinstance(json_content, dict):
        raise ValueError(
            f"Failed to parse json response from model ({model_config.model_name}): {content_str}"
        )
    
    return AIResponse(
        content=json_content,
        content_string=content_str,
        usage=response.get('usage'),
    )
