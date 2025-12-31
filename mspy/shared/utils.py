"""通用工具函数。"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Iterable


def assert_true(condition: bool, message: str) -> None:
    """断言包装，避免直接依赖pytest等。"""
    if not condition:
        raise AssertionError(message)


def b64_to_bytes(data_url: str) -> bytes:
    """将 data:image/...;base64,xxx 或纯 base64 转成 bytes。"""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    return base64.b64decode(data_url)


def bytes_to_data_url(raw: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def coalesce(*values: Any, default: Any = None) -> Any:
    for val in values:
        if val is not None:
            return val
    return default


def compact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """删除值为 None 的字段。"""
    return {k: v for k, v in data.items() if v is not None}


def json_dumps_clean(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def chunk(iterable: Iterable[Any], size: int) -> Iterable[list[Any]]:
    buf: list[Any] = []
    for item in iterable:
        buf.append(item)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf
