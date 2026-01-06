"""
通用类型定义。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class LocateParam:
    """表示定位参数。"""

    prompt: str
    bbox: Optional[List[float]] = None


@dataclass
class DeviceAction:
    """设备动作定义，简化版。"""

    name: str
    description: str
    param_schema: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable[[Dict[str, Any]], Any]] = None
