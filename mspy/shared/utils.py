"""
共享工具函数模块
Shared utility functions module
"""
import hashlib
import os
import uuid as uuid_lib
from typing import Any


def uuid() -> str:
    """Generate a UUID string."""
    return str(uuid_lib.uuid4())


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    Generate a hash ID from rect and content.
    生成基于rect和content的哈希ID
    """
    combined = str({"content": content, "rect": rect})
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # Convert hex to a-z by mapping each hex char to a letter
    def to_letters(hex_str: str) -> str:
        return "".join(chr(97 + (int(char, 16) % 26)) for char in hex_str)
    
    hash_letters = to_letters(hash_hex)
    return hash_letters[:5]


def assert_condition(condition: Any, message: str = "Assertion failed") -> None:
    """
    Assert a condition and raise an error if false.
    断言条件，如果为假则抛出错误
    """
    if not condition:
        raise AssertionError(message)


def if_in_browser() -> bool:
    """Check if running in browser environment."""
    return False


def if_in_node() -> bool:
    """Check if running in Node.js-like environment (Python is like Node)."""
    return True


def escape_script_tag(html: str) -> str:
    """Escape script tags in HTML."""
    return html.replace("<", "__midscene_lt__").replace(">", "__midscene_gt__")


def anti_escape_script_tag(html: str) -> str:
    """Unescape script tags in HTML."""
    return html.replace("__midscene_lt__", "<").replace("__midscene_gt__", ">")


def replace_illegal_path_chars_and_space(s: str) -> str:
    """Replace illegal path characters and spaces with hyphens."""
    illegal_chars = ':*?"<>|# '
    result = s
    for char in illegal_chars:
        result = result.replace(char, "-")
    return result


def sleep_ms(ms: int) -> None:
    """Sleep for specified milliseconds."""
    import time
    time.sleep(ms / 1000.0)
