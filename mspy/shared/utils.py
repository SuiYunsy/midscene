"""
Utils - 工具函数模块
提供通用工具函数
"""

import sys
import hashlib
import json
from typing import Any, Optional
import uuid as uuid_lib


# 环境检测
if_in_node = True  # Python 环境下始终为 True（类似 Node.js 环境）


def uuid() -> str:
    """
    生成 UUID
    
    Returns:
        UUID 字符串
    """
    return str(uuid_lib.uuid4())


# 哈希映射缓存
_hash_map: dict[str, str] = {}


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    生成基于内容和矩形的哈希 ID
    
    Args:
        rect: 矩形区域
        content: 内容字符串
        
    Returns:
        哈希 ID
    """
    global _hash_map
    
    # 将输入组合为字符串
    combined = json.dumps({
        "content": content,
        "rect": rect if isinstance(rect, dict) else vars(rect) if hasattr(rect, '__dict__') else str(rect),
    }, sort_keys=True)
    
    # 生成 SHA-256 哈希
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # 将十六进制转换为字母
    def to_letters(hex_str: str) -> str:
        result = []
        for char in hex_str:
            code = int(char, 16)
            result.append(chr(97 + (code % 26)))  # 97 是 'a' 的 ASCII 码
        return "".join(result)
    
    hash_letters = to_letters(hash_hex)
    
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


def assert_condition(condition: Any, message: Optional[str] = None) -> None:
    """
    断言条件为真，否则抛出异常
    
    Args:
        condition: 断言条件
        message: 错误消息
        
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message or "Assertion failed")


def escape_script_tag(html: str) -> str:
    """
    转义脚本标签
    
    Args:
        html: HTML 字符串
        
    Returns:
        转义后的字符串
    """
    return html.replace("<", "__midscene_lt__").replace(">", "__midscene_gt__")


def anti_escape_script_tag(html: str) -> str:
    """
    反转义脚本标签
    
    Args:
        html: 转义后的字符串
        
    Returns:
        原始 HTML 字符串
    """
    return html.replace("__midscene_lt__", "<").replace("__midscene_gt__", ">")


def replace_illegal_path_chars(s: str) -> str:
    """
    替换文件名中的非法字符和空格
    
    Args:
        s: 输入字符串
        
    Returns:
        处理后的字符串
    """
    import re
    return re.sub(r'[:*?"<>|# ]', '-', s)


def safe_parse_json(input_str: str) -> Any:
    """
    安全解析 JSON 字符串
    
    Args:
        input_str: JSON 字符串
        
    Returns:
        解析后的对象
    """
    # 尝试提取 JSON
    clean_json = extract_json_from_code_block(input_str)
    
    try:
        return json.loads(clean_json)
    except json.JSONDecodeError:
        # 尝试修复常见的 JSON 错误
        try:
            # 移除尾随逗号
            import re
            fixed = re.sub(r',\s*}', '}', clean_json)
            fixed = re.sub(r',\s*]', ']', fixed)
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}. Input: {input_str}")


def extract_json_from_code_block(response: str) -> str:
    """
    从代码块中提取 JSON
    
    Args:
        response: 响应字符串
        
    Returns:
        提取的 JSON 字符串
    """
    import re
    
    # 尝试直接匹配 JSON 对象
    json_match = re.match(r'^\s*(\{[\s\S]*\})\s*$', response)
    if json_match:
        return json_match.group(1)
    
    # 尝试从代码块中提取
    code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if code_block_match:
        return code_block_match.group(1)
    
    # 尝试查找 JSON 结构
    json_like_match = re.search(r'\{[\s\S]*\}', response)
    if json_like_match:
        return json_like_match.group(0)
    
    return response
