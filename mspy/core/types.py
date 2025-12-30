"""
核心类型定义

对应TypeScript源码: packages/core/src/types.ts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Literal, Optional, TypeVar, Union
from enum import Enum

from mspy.shared.types import (
    BaseElement,
    Rect,
    Size,
    Point,
    LocateResultElement,
    AIUsageInfo,
)


# ============ 响应格式枚举 ============

class AIResponseFormat(Enum):
    """AI响应格式"""
    JSON = "json_object"
    TEXT = "text"


# ============ UI上下文 ============

class UIContext(ABC):
    """UI上下文抽象类
    
    定义了获取页面截图和尺寸的接口
    """
    
    @property
    @abstractmethod
    def screenshot_base64(self) -> str:
        """获取页面截图的Base64编码"""
        pass
    
    @property
    @abstractmethod
    def size(self) -> Size:
        """获取页面尺寸"""
        pass
    
    @property
    def is_frozen(self) -> bool:
        """是否为冻结的上下文"""
        return getattr(self, '_is_frozen', False)
    
    @is_frozen.setter
    def is_frozen(self, value: bool):
        self._is_frozen = value


# ============ 服务相关类型 ============

ServiceAction = Literal["locate", "extract", "assert", "describe"]
ServiceExtractParam = Union[str, Dict[str, str]]


@dataclass
class ServiceTaskInfo:
    """服务任务信息"""
    duration_ms: int
    format_response: Optional[str] = None
    raw_response: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    search_area: Optional[Rect] = None
    search_area_raw_response: Optional[str] = None
    search_area_usage: Optional[AIUsageInfo] = None


@dataclass
class DumpMeta:
    """Dump元数据"""
    log_time: int


@dataclass
class ServiceDump(DumpMeta):
    """服务Dump数据"""
    type: Literal["locate", "extract", "assert"]
    log_id: str
    user_query: Dict[str, Any]
    matched_element: List[LocateResultElement]
    matched_rect: Optional[Rect] = None
    deep_think: Optional[bool] = None
    data: Any = None
    assertion_pass: Optional[bool] = None
    assertion_thought: Optional[str] = None
    task_info: Optional[ServiceTaskInfo] = None
    error: Optional[str] = None
    output: Any = None


class ServiceError(Exception):
    """服务错误
    
    当AI服务调用失败时抛出此异常
    """
    
    def __init__(self, message: str, dump: ServiceDump):
        super().__init__(message)
        self.dump = dump
        self.name = "ServiceError"


# ============ 定位结果 ============

@dataclass
class LocateResult:
    """定位结果"""
    element: Optional[LocateResultElement]
    rect: Optional[Rect] = None


@dataclass
class LocateResultWithDump(LocateResult):
    """带Dump的定位结果"""
    dump: Optional[ServiceDump] = None


@dataclass
class ServiceExtractResult(Generic[TypeVar('T')]):
    """服务提取结果"""
    data: Any
    thought: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    dump: Optional[ServiceDump] = None


# ============ 规划相关类型 ============

@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Any
    thought: Optional[str] = None


@dataclass
class PlanningAIResponse:
    """规划AI响应"""
    actions: Optional[List[PlanningAction]] = None
    more_actions_needed: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None
    yaml_flow: Optional[List[Dict[str, Any]]] = None
    yaml_string: Optional[str] = None


# ============ 执行任务相关类型 ============

ExecutionTaskType = Literal["Planning", "Insight", "Action Space", "Log"]
ExecutionTaskStatus = Literal["pending", "running", "finished", "failed", "cancelled"]


@dataclass
class ExecutionRecorderItem:
    """执行记录项"""
    type: Literal["screenshot"]
    ts: int
    screenshot: Optional[str] = None
    timing: Optional[str] = None


@dataclass
class ExecutionTaskTiming:
    """执行任务计时"""
    start: int
    end: Optional[int] = None
    cost: Optional[int] = None


@dataclass
class ExecutionTask:
    """执行任务"""
    type: ExecutionTaskType
    status: ExecutionTaskStatus = "pending"
    sub_type: Optional[str] = None
    sub_task: Optional[bool] = None
    param: Any = None
    thought: Optional[str] = None
    output: Any = None
    log: Any = None
    recorder: Optional[List[ExecutionRecorderItem]] = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    timing: Optional[ExecutionTaskTiming] = None
    usage: Optional[AIUsageInfo] = None
    search_area_usage: Optional[AIUsageInfo] = None


@dataclass
class ExecutionDump(DumpMeta):
    """执行Dump"""
    name: str
    description: Optional[str] = None
    tasks: List[ExecutionTask] = field(default_factory=list)
    ai_act_context: Optional[str] = None


@dataclass
class GroupedActionDump:
    """分组动作Dump"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = field(default_factory=list)
    executions: List[ExecutionDump] = field(default_factory=list)


# ============ Agent相关类型 ============

ThinkingLevel = Literal["off", "medium", "high"]
TestStatus = Literal["passed", "failed", "timedOut", "skipped", "interrupted"]


@dataclass
class AgentWaitForOpt:
    """Agent等待选项"""
    check_interval_ms: int = 3000
    timeout_ms: int = 15000


@dataclass
class AgentAssertOpt:
    """Agent断言选项"""
    keep_raw_response: bool = False


@dataclass
class CacheConfig:
    """缓存配置"""
    strategy: Literal["read-only", "read-write", "write-only"] = "read-write"
    id: str = ""


Cache = Union[bool, CacheConfig]


@dataclass
class LocateValidatorResult:
    """定位验证结果"""
    passed: bool
    rect: Rect
    center: tuple  # [number, number]
    center_distance: Optional[int] = None


@dataclass
class AgentDescribeElementAtPointResult:
    """Agent描述元素结果"""
    prompt: str
    deep_think: bool
    verify_result: Optional[LocateValidatorResult] = None


# ============ 设备动作相关类型 ============

@dataclass
class DeviceAction:
    """设备动作定义"""
    name: str
    description: str = ""
    interface_alias: Optional[str] = None
    param_schema: Any = None  # zod schema
    call: Optional[Callable] = None
    delay_after_runner: Optional[int] = None


# ============ 接口类型 ============

InterfaceType = Literal[
    "puppeteer",
    "playwright", 
    "static",
    "chrome-extension-proxy",
    "android",
]


# ============ 代码生成相关类型 ============

@dataclass
class CodeGenerationChunk:
    """代码生成块"""
    content: str
    reasoning_content: str
    accumulated: str
    is_complete: bool
    usage: Optional[AIUsageInfo] = None


StreamingCallback = Callable[[CodeGenerationChunk], None]


@dataclass 
class StreamingCodeGenerationOptions:
    """流式代码生成选项"""
    stream: bool = False
    on_chunk: Optional[StreamingCallback] = None
    on_complete: Optional[Callable[[str], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None


# ============ Web特定类型 ============

@dataclass
class WebElementInfo(BaseElement):
    """Web元素信息"""
    _id: str = ""
    _attributes: Dict[str, str] = field(default_factory=dict)
    _content: str = ""
    _rect: Optional[Rect] = None
    _center: tuple = (0, 0)
    _is_visible: bool = True
    zoom: float = 1.0
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def attributes(self) -> Dict[str, str]:
        return self._attributes
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def rect(self) -> Rect:
        return self._rect or Rect()
    
    @property
    def center(self) -> tuple:
        return self._center
    
    @property
    def is_visible(self) -> bool:
        return self._is_visible
