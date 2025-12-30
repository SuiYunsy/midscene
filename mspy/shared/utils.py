"""
工具函数模块 - 提供通用的工具函数

对应TypeScript源码: packages/shared/src/utils.ts
"""

import asyncio
import time
from typing import Any, TypeVar, Optional


T = TypeVar('T')


def assert_condition(condition: Any, message: str = "Assertion failed") -> None:
    """断言条件为真
    
    Args:
        condition: 要检查的条件
        message: 断言失败时的错误信息
        
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message)


def sleep_ms(milliseconds: int) -> None:
    """同步休眠指定毫秒数
    
    Args:
        milliseconds: 休眠时间（毫秒）
    """
    time.sleep(milliseconds / 1000)


async def async_sleep_ms(milliseconds: int) -> None:
    """异步休眠指定毫秒数
    
    Args:
        milliseconds: 休眠时间（毫秒）
    """
    await asyncio.sleep(milliseconds / 1000)


def deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典
    
    Args:
        base: 基础字典
        override: 覆盖字典
        
    Returns:
        合并后的新字典
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串
    
    Args:
        s: 要截断的字符串
        max_length: 最大长度
        suffix: 截断后添加的后缀
        
    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def is_valid_url(url: str) -> bool:
    """检查URL是否有效
    
    Args:
        url: 要检查的URL
        
    Returns:
        是否为有效URL
    """
    return url.startswith(('http://', 'https://', 'file://'))


def generate_id() -> str:
    """生成唯一ID
    
    Returns:
        唯一ID字符串
    """
    import uuid
    return str(uuid.uuid4())


def get_timestamp() -> int:
    """获取当前时间戳（毫秒）
    
    Returns:
        当前时间戳
    """
    return int(time.time() * 1000)


def format_duration(ms: int) -> str:
    """格式化持续时间
    
    Args:
        ms: 毫秒数
        
    Returns:
        格式化后的时间字符串
    """
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms / 1000:.2f}s"
    else:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes}m {seconds:.2f}s"


def safe_json_parse(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析后的对象或默认值
    """
    import json
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_stringify(obj: Any, default: str = "{}") -> str:
    """安全的JSON序列化
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        
    Returns:
        JSON字符串
    """
    import json
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default
