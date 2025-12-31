"""
通用工具函数
"""

import asyncio
import hashlib
import json
import re
import time
import uuid as uuid_lib
from typing import Any, Optional


def uuid() -> str:
    """生成UUID"""
    return str(uuid_lib.uuid4())


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    生成基于矩形和内容的哈希ID
    
    Args:
        rect: 矩形信息
        content: 内容字符串
    
    Returns:
        哈希ID字符串
    """
    combined = json.dumps({
        'content': content,
        'rect': rect,
    }, sort_keys=True)
    
    # 生成SHA-256哈希
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # 转换为字母（a-z）
    def to_letters(hex_str: str) -> str:
        return ''.join(
            chr(97 + (int(char, 16) % 26))
            for char in hex_str
        )
    
    hash_letters = to_letters(hash_hex)
    return hash_letters[:5]


def assert_condition(condition: Any, message: Optional[str] = None) -> None:
    """
    断言条件为真，否则抛出异常
    
    Args:
        condition: 要断言的条件
        message: 断言失败时的错误消息
    
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message or "Assertion failed")


def replace_illegal_path_chars(s: str) -> str:
    """
    替换路径中的非法字符和空格
    
    Args:
        s: 原始字符串
    
    Returns:
        处理后的字符串
    """
    return re.sub(r'[:*?"<>|# ]', '-', s)


def sleep(ms: int) -> None:
    """
    同步睡眠指定毫秒数
    
    Args:
        ms: 毫秒数
    """
    time.sleep(ms / 1000)


async def async_sleep(ms: int) -> None:
    """
    异步睡眠指定毫秒数
    
    Args:
        ms: 毫秒数
    """
    await asyncio.sleep(ms / 1000)
