"""
AI服务调用模块 - 封装OpenAI兼容的API调用
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, TypeVar, Union
import httpx
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from ...shared import (
    get_debug,
    IModelConfig,
    AIUsageInfo,
)

T = TypeVar('T')

debug = get_debug('ai:call')
debug_proxy = get_debug('ai:call:proxy')
debug_profile = get_debug('ai:profile:stats')


def mask_base64_in_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    掩码消息中的base64内容用于日志输出
    
    - image_url 的 base64 内容用 "base64 is masked" 替代
    - system 的 text 打印前50个字符，超出则省略号
    - user、assistant 的 text 全部保留
    """
    masked_messages = []
    
    for msg in messages:
        masked_msg = {'role': msg.get('role', '')}
        content = msg.get('content')
        
        if isinstance(content, str):
            # 字符串内容
            if msg.get('role') == 'system':
                if len(content) > 50:
                    masked_msg['content'] = content[:50] + '...'
                else:
                    masked_msg['content'] = content
            else:
                masked_msg['content'] = content
        elif isinstance(content, list):
            # 多模态内容
            masked_content = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'image_url':
                        image_url = item.get('image_url', {})
                        url = image_url.get('url', '')
                        if url.startswith('data:'):
                            # base64图像，掩码内容
                            masked_content.append({
                                'type': 'image_url',
                                'image_url': {
                                    'url': 'base64 is masked',
                                    'detail': image_url.get('detail', 'auto')
                                }
                            })
                        else:
                            masked_content.append(item)
                    elif item.get('type') == 'text':
                        text = item.get('text', '')
                        if msg.get('role') == 'system':
                            if len(text) > 50:
                                masked_content.append({
                                    'type': 'text',
                                    'text': text[:50] + '...'
                                })
                            else:
                                masked_content.append(item)
                        else:
                            masked_content.append(item)
                    else:
                        masked_content.append(item)
                else:
                    masked_content.append(item)
            masked_msg['content'] = masked_content
        else:
            masked_msg['content'] = content
        
        masked_messages.append(masked_msg)
    
    return masked_messages


def create_openai_client(model_config: IModelConfig) -> OpenAI:
    """
    创建OpenAI客户端
    
    Args:
        model_config: 模型配置
    
    Returns:
        OpenAI客户端实例
    """
    http_client = None
    
    # 配置HTTP代理
    if model_config.http_proxy:
        debug_proxy(f"using http proxy: {model_config.http_proxy}")
        
        # 配置证书验证
        verify = not model_config.skip_cert_verification
        if not verify:
            debug_proxy("SSL certificate verification is disabled")
        
        http_client = httpx.Client(
            proxy=model_config.http_proxy,
            verify=verify,
            timeout=httpx.Timeout(model_config.timeout or 600.0)
        )
    elif model_config.skip_cert_verification:
        debug_proxy("SSL certificate verification is disabled (no proxy)")
        http_client = httpx.Client(
            verify=False,
            timeout=httpx.Timeout(model_config.timeout or 600.0)
        )
    
    client = OpenAI(
        api_key=model_config.openai_api_key,
        base_url=model_config.openai_base_url,
        http_client=http_client,
        timeout=model_config.timeout or 600.0,
    )
    
    return client


async def call_ai(
    messages: List[ChatCompletionMessageParam],
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用AI服务
    
    Args:
        messages: 消息列表
        model_config: 模型配置
    
    Returns:
        {'content': str, 'usage': AIUsageInfo}
    """
    # 打印请求日志（掩码base64）
    masked_messages = mask_base64_in_messages([dict(m) for m in messages])
    debug(f"Sending request to {model_config.model_name}")
    debug(f"Messages: {json.dumps(masked_messages, ensure_ascii=False)}")
    
    client = create_openai_client(model_config)
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model_config.model_name,
            messages=messages,
            temperature=model_config.temperature or 0,
            max_tokens=None,  # 使用模型默认值
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        content = response.choices[0].message.content or ""
        usage = response.usage
        
        # 打印响应日志
        debug(f"Response: {content[:500]}..." if len(content) > 500 else f"Response: {content}")
        
        usage_info = AIUsageInfo(
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            time_cost=time_cost,
            model_name=model_config.model_name,
            model_description=model_config.model_description,
            intent=model_config.intent,
        )
        
        debug_profile(
            f"model, {model_config.model_name}, "
            f"mode, {model_config.vl_mode or 'default'}, "
            f"prompt-tokens, {usage.prompt_tokens if usage else ''}, "
            f"completion-tokens, {usage.completion_tokens if usage else ''}, "
            f"cost-ms, {time_cost}"
        )
        
        if not content:
            raise ValueError("Empty content from AI response")
        
        return {
            'content': content,
            'usage': usage_info,
        }
    
    except Exception as e:
        debug(f"AI call error: {e}")
        raise RuntimeError(
            f"Failed to call AI model service ({model_config.model_name}): {e}\n"
            "Troubleshooting: https://midscenejs.com/model-provider.html"
        ) from e


def extract_json_from_code_block(response: str) -> str:
    """
    从响应中提取JSON
    
    Args:
        response: AI响应文本
    
    Returns:
        提取的JSON字符串
    """
    try:
        # 尝试直接匹配JSON对象
        json_match = re.match(r'^\s*(\{[\s\S]*\})\s*$', response)
        if json_match:
            return json_match.group(1)
        
        # 尝试从代码块中提取
        code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
        if code_block_match:
            return code_block_match.group(1)
        
        # 尝试查找JSON-like结构
        json_like_match = re.search(r'\{[\s\S]*\}', response)
        if json_like_match:
            return json_like_match.group(0)
    except Exception:
        pass
    
    return response


def normalize_json_object(obj: Any) -> Any:
    """
    规范化JSON对象（去除字符串首尾空格）
    
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
            trimmed_key = key.strip()
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
    安全地解析JSON
    
    Args:
        input_str: JSON字符串
        vl_mode: VL模式
    
    Returns:
        解析后的对象
    """
    clean_json_string = extract_json_from_code_block(input_str)
    
    # 检查是否是坐标格式
    point_match = re.match(r'\((\d+),(\d+)\)', clean_json_string)
    if point_match:
        return [int(point_match.group(1)), int(point_match.group(2))]
    
    last_error = None
    
    # 尝试直接解析
    try:
        parsed = json.loads(clean_json_string)
        return normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        last_error = e
    
    # 尝试修复常见的JSON错误
    try:
        # 尝试修复单引号
        fixed = clean_json_string.replace("'", '"')
        parsed = json.loads(fixed)
        return normalize_json_object(parsed)
    except json.JSONDecodeError as e:
        last_error = e
    
    raise ValueError(
        f"Failed to parse LLM response into JSON. "
        f"Error - {last_error}. Response - \n{input_str}"
    )


async def call_ai_with_object_response(
    messages: List[ChatCompletionMessageParam],
    model_config: IModelConfig,
) -> Dict[str, Any]:
    """
    调用AI并返回JSON对象响应
    
    Args:
        messages: 消息列表
        model_config: 模型配置
    
    Returns:
        {'content': parsed_object, 'content_string': str, 'usage': AIUsageInfo}
    """
    response = await call_ai(messages, model_config)
    
    if not response:
        raise ValueError("Empty response from AI")
    
    content_str = response['content']
    json_content = safe_parse_json(content_str, model_config.vl_mode)
    
    if not isinstance(json_content, dict):
        raise ValueError(
            f"Failed to parse JSON response from model "
            f"({model_config.model_name}): {content_str}"
        )
    
    return {
        'content': json_content,
        'content_string': content_str,
        'usage': response.get('usage'),
    }
