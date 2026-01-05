"""类型定义"""
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional, List, Dict, Tuple
from enum import Enum

@dataclass
class Point:
    """坐标点"""
    left: int
    top: int

@dataclass
class Size:
    """尺寸"""
    width: int
    height: int
    dpr: float = 1.0

@dataclass
class Rect:
    """矩形区域"""
    left: int
    top: int
    width: int
    height: int

@dataclass
class LocateResult:
    """定位结果"""
    center: Tuple[int, int]
    rect: Rect
    prompt: str = ""
    bbox: Optional[List[int]] = None  # [x1, y1, x2, y2]

@dataclass
class UIContext:
    """UI上下文"""
    screenshot_base64: str
    size: Size
    url: str = ""
    description: str = ""

@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: str = ""

@dataclass
class PlanningResponse:
    """规划响应"""
    log: str
    more_actions_needed: bool
    actions: List[PlanningAction]
    error: Optional[str] = None
    sleep: Optional[int] = None
    raw_response: str = ""
    usage: Optional[Dict[str, Any]] = None
    yaml_flow: Optional[List[Dict[str, Any]]] = None

@dataclass
class ActionResult:
    """动作执行结果"""
    success: bool
    output: Any = None
    error: Optional[str] = None
    thought: Optional[str] = None

@dataclass
class DeviceAction:
    """设备动作定义"""
    name: str
    description: str
    call: Callable[..., Coroutine[Any, Any, Any]]
    param_schema: Optional[Dict[str, Any]] = None
    interface_alias: Optional[str] = None

@dataclass
class ExecutionDump:
    """执行记录"""
    log_time: int
    name: str
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""

@dataclass
class TaskTiming:
    """任务时间信息"""
    start: int
    end: Optional[int] = None
    cost: Optional[int] = None

@dataclass
class ExecutionTask:
    """执行任务"""
    type: str
    sub_type: str
    status: str = "pending"
    param: Dict[str, Any] = field(default_factory=dict)
    output: Any = None
    thought: Optional[str] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    timing: Optional[TaskTiming] = None
    usage: Optional[Dict[str, Any]] = None
    recorder: List[Dict[str, Any]] = field(default_factory=list)
    ui_context: Optional[UIContext] = None
    log: Optional[Dict[str, Any]] = None

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"
