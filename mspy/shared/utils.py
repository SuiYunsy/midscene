# -*- coding: utf-8 -*-
"""
工具函数模块
提供通用的工具函数。
"""

import hashlib
import re
import uuid as uuid_lib
from typing import Any


def uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid_lib.uuid4())


# 用于存储已生成的哈希值，避免冲突
_hash_map: dict[str, str] = {}


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    根据矩形区域和内容生成唯一的哈希 ID
    
    Args:
        rect: 矩形区域对象
        content: 内容字符串
        
    Returns:
        生成的哈希 ID
    """
    import json
    
    # 组合输入为字符串
    if hasattr(rect, '__dict__'):
        rect_dict = rect.__dict__
    elif isinstance(rect, dict):
        rect_dict = rect
    else:
        rect_dict = {"value": str(rect)}
    
    combined = json.dumps({
        "content": content,
        "rect": rect_dict,
    }, sort_keys=True)
    
    # 生成 SHA-256 哈希
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # 将十六进制转换为字母（a-z）
    def to_letters(hex_str: str) -> str:
        result = []
        for char in hex_str:
            code = int(char, 16)
            result.append(chr(97 + (code % 26)))  # 97 是 'a' 的 ASCII 码
        return ''.join(result)
    
    hash_letters = to_letters(hash_hex)
    
    # 找到最短的唯一前缀
    slice_length = 5
    sliced_hash = ""
    
    while slice_length < len(hash_letters) - 1:
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
        message: 断言失败时的错误信息
        
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message)


# 正则表达式常量
REGEXP_LT_ESCAPE = '__midscene_lt__'
REGEXP_GT_ESCAPE = '__midscene_gt__'


def escape_script_tag(html: str) -> str:
    """
    转义 HTML 中的 script 标签，防止注入
    
    Args:
        html: HTML 字符串
        
    Returns:
        转义后的字符串
    """
    return html.replace('<', REGEXP_LT_ESCAPE).replace('>', REGEXP_GT_ESCAPE)


def anti_escape_script_tag(html: str) -> str:
    """
    反转义之前转义的标签
    
    Args:
        html: 转义后的 HTML 字符串
        
    Returns:
        原始 HTML 字符串
    """
    return html.replace(REGEXP_LT_ESCAPE, '<').replace(REGEXP_GT_ESCAPE, '>')


def replace_illegal_path_chars(s: str) -> str:
    """
    替换文件路径中的非法字符
    
    Args:
        s: 原始字符串
        
    Returns:
        替换后的字符串
    """
    # 只替换文件名中非法的字符，保留路径分隔符
    return re.sub(r'[:*?"<>|# ]', '-', s)


# 全局变量，标记是否为 MCP 模式
_is_mcp = False


def set_is_mcp(value: bool) -> None:
    """设置 MCP 模式标志"""
    global _is_mcp
    _is_mcp = value


def log_msg(*message: Any) -> None:
    """
    打印日志消息
    MCP 模式下需要使用特定格式
    """
    if not _is_mcp:
        print(*message)


async def repeat(times: int, fn) -> None:
    """
    重复执行异步函数
    
    Args:
        times: 执行次数
        fn: 要执行的异步函数，接受索引参数
    """
    for i in range(times):
        await fn(i)


def if_in_browser() -> bool:
    """检查是否在浏览器环境（Python 中始终为 False）"""
    return False


def if_in_worker() -> bool:
    """检查是否在 Worker 环境（Python 中始终为 False）"""
    return False


def if_in_node() -> bool:
    """检查是否在 Node.js 环境（Python 中视为类似环境，返回 True）"""
    return True
