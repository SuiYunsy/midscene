"""核心类型定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class Size:
    width: int
    height: int


@dataclass
class UIContext:
    screenshot_base64: str
    size: Size
    url: Optional[str] = None
    title: Optional[str] = None
    user_agent: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocateResult:
    center: Tuple[float, float]
    bbox: Tuple[float, float, float, float]
    description: Optional[str] = None


@dataclass
class ActionSpaceItem:
    name: str
    description: str
    param_hint: Optional[str] = None


@dataclass
class PlanOutput:
    log: str
    action: Optional[Dict[str, Any]]
    more_actions_needed_by_instruction: bool
    sleep: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    success: bool
    message: Optional[str] = None
    raw: Any = None
