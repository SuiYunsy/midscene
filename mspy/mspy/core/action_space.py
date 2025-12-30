from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ActionRequest:
    """动作调用请求，抽象 TS 版 AbstractInterface。"""

    name: str
    params: Dict[str, Any] | None = None


@dataclass
class ActionResult:
    ok: bool
    detail: Optional[str] = None
    payload: Optional[Any] = None
