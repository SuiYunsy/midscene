"""
类型定义模块
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict, Union
from enum import Enum


@dataclass
class Rect:
    """矩形区域"""
    left: int
    top: int
    width: int
    height: int


@dataclass
class Size:
    """尺寸"""
    width: int
    height: int
    dpr: Optional[float] = None


@dataclass
class Point:
    """坐标点"""
    x: int
    y: int


@dataclass
class LocateResultElement:
    """定位结果元素"""
    center: Tuple[int, int]
    rect: Rect
    description: Optional[str] = None


@dataclass
class UIContext:
    """UI上下文"""
    screenshot_base64: str
    size: Size
    _is_frozen: bool = False


@dataclass
class AIUsageInfo:
    """AI使用信息"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[int] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


@dataclass
class DetailedLocateParam:
    """详细定位参数"""
    prompt: str
    deep_think: bool = False
    cacheable: bool = True
    bbox: Optional[Tuple[int, int, int, int]] = None


@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: Optional[str] = None


@dataclass
class PlanningAIResponse:
    """规划AI响应"""
    actions: List[PlanningAction] = field(default_factory=list)
    more_actions_needed_by_instruction: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None


@dataclass 
class ServiceDump:
    """服务转储信息"""
    type: str
    log_id: str
    log_time: int
    user_query: Dict[str, Any]
    matched_element: List[LocateResultElement]
    matched_rect: Optional[Rect] = None
    data: Any = None
    error: Optional[str] = None


class ServiceError(Exception):
    """服务错误"""
    
    def __init__(self, message: str, dump: Optional[ServiceDump] = None):
        super().__init__(message)
        self.dump = dump


@dataclass
class LocateResultWithDump:
    """带转储的定位结果"""
    element: Optional[LocateResultElement]
    rect: Optional[Rect] = None
    dump: Optional[ServiceDump] = None


@dataclass
class ExecutionRecorderItem:
    """执行记录项"""
    type: str
    ts: int
    screenshot: Optional[str] = None
    timing: Optional[str] = None


class ExecutionTaskStatus(Enum):
    """执行任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionTask:
    """执行任务"""
    type: str
    sub_type: Optional[str] = None
    param: Any = None
    thought: Optional[str] = None
    status: ExecutionTaskStatus = ExecutionTaskStatus.PENDING
    output: Any = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    recorder: List[ExecutionRecorderItem] = field(default_factory=list)
    timing: Optional[Dict[str, int]] = None
    usage: Optional[AIUsageInfo] = None
    log: Any = None
    hit_by: Optional[Dict[str, Any]] = None
    ui_context: Optional[UIContext] = None
    sub_task: bool = False


@dataclass
class ExecutionDump:
    """执行转储"""
    log_time: int
    name: str
    description: Optional[str] = None
    tasks: List[ExecutionTask] = field(default_factory=list)


@dataclass
class GroupedActionDump:
    """分组动作转储"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = field(default_factory=list)
    executions: List[ExecutionDump] = field(default_factory=list)


@dataclass
class DeviceAction:
    """设备动作"""
    name: str
    description: str
    param_schema: Optional[Any] = None
    call: Optional[Callable] = None
    interface_alias: Optional[str] = None
    delay_after_runner: int = 300


@dataclass
class AgentOpt:
    """Agent选项"""
    test_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: str = ""
    generate_report: bool = False
    auto_print_report_msg: bool = False
    ai_act_context: Optional[str] = None
    replanning_cycle_limit: Optional[int] = None
    model_config: Optional[Dict[str, Any]] = None
