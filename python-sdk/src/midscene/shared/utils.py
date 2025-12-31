"""Utility functions for Midscene."""

import hashlib
import re
import uuid as uuid_module
from typing import Any, Dict

# Hash map for deduplication
_hash_map: Dict[str, str] = {}


def uuid() -> str:
    """Generate a UUID v4 string."""
    return str(uuid_module.uuid4())


def generate_hash_id(rect: Any, content: str = "") -> str:
    """
    Generate a hash ID from rect and content.
    
    Args:
        rect: Rectangle object with coordinates
        content: Optional content string
        
    Returns:
        A short hash string using a-z characters
    """
    import json
    
    # Combine the input into a string
    combined = json.dumps({
        "content": content,
        "rect": rect if isinstance(rect, dict) else str(rect),
    }, sort_keys=True)
    
    # Generate SHA-256 hash
    hash_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    # Convert hex to a-z by mapping each hex char to a letter
    def to_letters(hex_str: str) -> str:
        return ''.join(
            chr(97 + (int(char, 16) % 26))  # 97 is 'a' in ASCII
            for char in hex_str
        )
    
    hash_letters = to_letters(hash_hex)
    
    # Find unique prefix
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
    Assert a condition and raise an error if false.
    
    Args:
        condition: The condition to assert
        message: Error message if assertion fails
        
    Raises:
        AssertionError: If condition is falsy
    """
    if not condition:
        raise AssertionError(message)


# Constants for script tag escaping
_REGEXP_LT_ESCAPE = "__midscene_lt__"
_REGEXP_GT_ESCAPE = "__midscene_gt__"


def escape_script_tag(html: str) -> str:
    """
    Escape < and > characters in HTML.
    
    Args:
        html: HTML string to escape
        
    Returns:
        Escaped HTML string
    """
    return html.replace("<", _REGEXP_LT_ESCAPE).replace(">", _REGEXP_GT_ESCAPE)


def anti_escape_script_tag(html: str) -> str:
    """
    Unescape < and > characters in HTML.
    
    Args:
        html: Escaped HTML string
        
    Returns:
        Unescaped HTML string
    """
    return html.replace(_REGEXP_LT_ESCAPE, "<").replace(_REGEXP_GT_ESCAPE, ">")


def replace_illegal_path_chars_and_space(path: str) -> str:
    """
    Replace illegal filename characters and spaces with dashes.
    
    Args:
        path: Path string to sanitize
        
    Returns:
        Sanitized path string
    """
    return re.sub(r'[:*?"<>|# ]', '-', path)


async def repeat(times: int, fn) -> None:
    """
    Repeat an async function a number of times.
    
    Args:
        times: Number of repetitions
        fn: Async function that takes index as argument
    """
    for i in range(times):
        await fn(i)
