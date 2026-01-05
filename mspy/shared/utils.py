"""工具函数"""
import asyncio
import base64
import re
from pathlib import Path
from typing import Optional

def assert_condition(condition: bool, message: str = "Assertion failed") -> None:
    """断言检查，失败时抛出异常"""
    if not condition:
        raise AssertionError(message)

async def sleep_ms(ms: int) -> None:
    """异步等待指定毫秒数"""
    await asyncio.sleep(ms / 1000.0)

def encode_image_base64(image_path: str) -> str:
    """将图片文件编码为base64字符串（带data URI前缀）"""
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/png")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{data}"

def decode_base64_to_bytes(base64_str: str) -> bytes:
    """将base64字符串解码为字节，支持带data URI前缀"""
    if base64_str.startswith("data:"):
        # 去除 data:image/xxx;base64, 前缀
        base64_str = base64_str.split(",", 1)[1]
    return base64.b64decode(base64_str)

def mask_base64_in_text(text: str) -> str:
    """将文本中的base64内容替换为占位符"""
    # 匹配 data:image/xxx;base64,... 格式
    pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+'
    return re.sub(pattern, "base64 is masked.", text)

def truncate_text(text: str, max_length: int = 50) -> str:
    """截断文本，超出长度时添加省略号"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def create_image_base64_from_bytes(data: bytes, mime_type: str = "image/jpeg") -> str:
    """从字节数据创建base64图片字符串"""
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"
