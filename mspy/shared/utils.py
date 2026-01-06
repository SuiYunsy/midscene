"""
工具函数

从 packages/shared/src/utils.ts 迁移
"""

import hashlib
import json
import re
import uuid as uuid_lib
from typing import Any, Callable, TypeVar


def uuid() -> str:
    """生成UUID"""
    return str(uuid_lib.uuid4())


# 哈希映射缓存
_hash_map: dict[str, str] = {}


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    生成基于矩形和内容的哈希ID
    
    Args:
        rect: 矩形区域对象
        content: 可选的内容字符串
    
    Returns:
        短哈希ID (5-64个字符的字母)
    """
    # 组合输入为字符串
    combined = json.dumps({
        "content": content,
        "rect": rect if isinstance(rect, dict) else vars(rect) if hasattr(rect, '__dict__') else str(rect),
    }, sort_keys=True)
    
    # 生成SHA-256哈希
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # 转换为a-z字符
    def to_letters(hex_str: str) -> str:
        return "".join(
            chr(97 + (int(char, 16) % 26))  # 97 = 'a'
            for char in hex_str
        )
    
    hash_letters = to_letters(hash_hex)
    
    # 找到唯一的短哈希
    slice_length = 5
    sliced_hash = ""
    
    while slice_length <= len(hash_letters):
        sliced_hash = hash_letters[:slice_length]
        if sliced_hash in _hash_map and _hash_map[sliced_hash] != combined:
            slice_length += 1
            continue
        _hash_map[sliced_hash] = combined
        break
    
    return sliced_hash


def assert_condition(condition: Any, message: str = "Assertion failed") -> None:
    """
    断言条件为真，否则抛出异常
    
    Args:
        condition: 要断言的条件
        message: 断言失败时的错误消息
    
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message)


def log_msg(*message: Any) -> None:
    """打印日志消息"""
    print(*message)


async def repeat(times: int, fn: Callable[[int], Any]) -> None:
    """
    重复执行异步函数
    
    Args:
        times: 重复次数
        fn: 要执行的函数，接收索引参数
    """
    for i in range(times):
        await fn(i)


# 转义常量
_REGEXP_LT_ESCAPE = "__midscene_lt__"
_REGEXP_GT_ESCAPE = "__midscene_gt__"


def escape_script_tag(html: str) -> str:
    """转义HTML中的脚本标签"""
    return html.replace("<", _REGEXP_LT_ESCAPE).replace(">", _REGEXP_GT_ESCAPE)


def anti_escape_script_tag(html: str) -> str:
    """反转义HTML中的脚本标签"""
    return html.replace(_REGEXP_LT_ESCAPE, "<").replace(_REGEXP_GT_ESCAPE, ">")


def replace_illegal_path_chars(s: str) -> str:
    """
    替换文件路径中的非法字符和空格
    
    Args:
        s: 原始字符串
    
    Returns:
        处理后的字符串
    """
    return re.sub(r'[:*?"<>|# ]', "-", s)
