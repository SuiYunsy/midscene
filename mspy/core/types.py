"""
核心类型定义

从 packages/core/src/types.ts 迁移
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, Literal, Optional, TypeVar

from mspy.shared.types import Rect, Size, LocateResultElement


# ========== AI响应相关类型 ==========

class AIResponseFormat(str, Enum):
    """AI响应格式"""
    JSON = "json_object"
    TEXT = "text"


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
class AISingleElementResponse:
    """AI单元素响应"""
    id: str
    reason: Optional[str] = None
    text: Optional[str] = None


@dataclass
class AIElementCoordinatesResponse:
    """AI元素坐标响应"""
    bbox: tuple[int, int, int, int]  # [x, y, width, height]
    errors: Optional[list[str]] = None


@dataclass
class AIDataExtractionResponse(Generic[TypeVar("T")]):
    """AI数据提取响应"""
    data: Any
    errors: Optional[list[str]] = None
    thought: Optional[str] = None


@dataclass
class AIAssertionResponse:
    """AI断言响应"""
    passed: bool
    thought: str


@dataclass
class AIDescribeElementResponse:
    """AI描述元素响应"""
    description: str
    error: Optional[str] = None


# ========== 上下文相关类型 ==========

@dataclass
class UIContext:
    """UI上下文"""
    screenshot_base64: str
    size: Size
    is_frozen: bool = False


# ========== 服务相关类型 ==========

ServiceAction = Literal["locate", "extract", "assert", "describe"]

ServiceExtractParam = str | dict[str, str]


@dataclass
class LocateResult:
    """定位结果"""
    element: Optional[LocateResultElement] = None
    rect: Optional[Rect] = None


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
    """Dump元信息"""
    log_time: int


@dataclass
class ServiceDump(DumpMeta):
    """服务Dump"""
    type: Literal["locate", "extract", "assert"]
    log_id: str
    user_query: dict[str, Any]
    matched_element: list[LocateResultElement]
    matched_rect: Optional[Rect] = None
    deep_think: bool = False
    data: Any = None
    assertion_pass: Optional[bool] = None
    assertion_thought: Optional[str] = None
    task_info: Optional[ServiceTaskInfo] = None
    error: Optional[str] = None
    output: Any = None


# ========== 执行任务相关类型 ==========

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
    sub_task: bool = False
    param: Optional[dict[str, Any]] = None
    thought: Optional[str] = None
    output: Any = None
    log: Any = None
    recorder: Optional[list[ExecutionRecorderItem]] = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    timing: Optional[ExecutionTaskTiming] = None
    usage: Optional[AIUsageInfo] = None


@dataclass
class ExecutionDump(DumpMeta):
    """执行Dump"""
    name: str
    description: Optional[str] = None
    tasks: list[ExecutionTask] = field(default_factory=list)
    ai_act_context: Optional[str] = None


@dataclass
class GroupedActionDump:
    """分组动作Dump"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: list[str] = field(default_factory=list)
    executions: list[ExecutionDump] = field(default_factory=list)


# ========== 规划相关类型 ==========

@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: dict[str, Any] = field(default_factory=dict)
    thought: Optional[str] = None


@dataclass
class PlanningAIResponse:
    """规划AI响应"""
    actions: Optional[list[PlanningAction]] = None
    more_actions_needed: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None


# ========== Agent配置相关类型 ==========

@dataclass
class CacheConfig:
    """缓存配置"""
    strategy: Literal["read-only", "read-write", "write-only"] = "read-write"
    id: str = ""


@dataclass
class AgentOpt:
    """Agent选项"""
    test_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: Optional[str] = None
    generate_report: bool = True
    auto_print_report_msg: bool = True
    ai_act_context: Optional[str] = None
    report_file_name: Optional[str] = None
    cache: Optional[CacheConfig] = None
    replanning_cycle_limit: Optional[int] = None


# ========== 设备动作相关类型 ==========

@dataclass 
class DeviceAction:
    """设备动作定义"""
    name: str
    description: Optional[str] = None
    interface_alias: Optional[str] = None
    call: Optional[Callable] = None
    delay_after_runner: Optional[int] = None


# ========== 报告相关类型 ==========

TestStatus = Literal["passed", "failed", "timedOut", "skipped", "interrupted"]


@dataclass
class ReportFileWithAttributes:
    """带属性的报告文件"""
    report_file_path: str
    test_duration: int
    test_status: TestStatus
    test_title: str
    test_id: str
    test_description: str
