"""
工具函数

提供UUID生成、哈希计算、断言等通用工具函数。
"""

import hashlib
import json
import uuid as uuid_lib
from typing import Any, TypeVar

T = TypeVar("T")


def uuid() -> str:
    """
    生成UUID
    
    Returns:
        UUID字符串
    """
    return str(uuid_lib.uuid4())


# 哈希缓存，用于检测冲突
_hash_map: dict[str, str] = {}


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    根据矩形和内容生成哈希ID
    
    Args:
        rect: 矩形信息
        content: 内容字符串
        
    Returns:
        哈希ID（5-N个小写字母）
    """
    # 组合输入
    combined = json.dumps({"content": content, "rect": rect}, sort_keys=True)
    
    # 生成SHA-256哈希
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # 将十六进制转换为a-z字母
    def to_letters(hex_str: str) -> str:
        letters = []
        for char in hex_str:
            code = int(char, 16)
            letters.append(chr(97 + (code % 26)))  # 97是ASCII中的'a'
        return "".join(letters)
    
    hash_letters = to_letters(hash_hex)
    
    # 从5个字符开始，逐渐增加长度以避免冲突
    slice_length = 5
    while slice_length < len(hash_letters) - 1:
        sliced_hash = hash_letters[:slice_length]
        if sliced_hash in _hash_map and _hash_map[sliced_hash] != combined:
            slice_length += 1
            continue
        _hash_map[sliced_hash] = combined
        break
    
    return hash_letters[:slice_length]


def assert_condition(condition: Any, message: str = "Assertion failed") -> None:
    """
    断言条件为真
    
    Args:
        condition: 要检查的条件
        message: 断言失败时的错误消息
        
    Raises:
        AssertionError: 如果条件为假
    """
    if not condition:
        raise AssertionError(message)


# 正则表达式转义
REGEXP_LT_ESCAPE = "__midscene_lt__"
REGEXP_GT_ESCAPE = "__midscene_gt__"


def escape_script_tag(html: str) -> str:
    """
    转义HTML中的<>字符
    
    Args:
        html: HTML字符串
        
    Returns:
        转义后的字符串
    """
    return html.replace("<", REGEXP_LT_ESCAPE).replace(">", REGEXP_GT_ESCAPE)


def anti_escape_script_tag(html: str) -> str:
    """
    反转义HTML中的<>字符
    
    Args:
        html: 转义后的字符串
        
    Returns:
        原始字符串
    """
    return html.replace(REGEXP_LT_ESCAPE, "<").replace(REGEXP_GT_ESCAPE, ">")


def replace_illegal_path_chars_and_space(s: str) -> str:
    """
    替换文件名中的非法字符和空格
    
    替换的字符包括：: * ? " < > | # 空格
    
    Args:
        s: 原始字符串
        
    Returns:
        替换后的字符串
    """
    import re
    # 匹配文件名中的非法字符：冒号、星号、问号、引号、尖括号、竖线、井号、空格
    illegal_chars_pattern = r'[:*?"<>|# ]'
    return re.sub(illegal_chars_pattern, "-", s)


async def repeat(times: int, fn: Any) -> None:
    """
    重复执行异步函数
    
    Args:
        times: 重复次数
        fn: 异步函数，接受index参数
    """
    for i in range(times):
        await fn(i)
