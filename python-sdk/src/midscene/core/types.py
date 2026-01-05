"""Type definitions for Midscene core module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, TypedDict, Union

from pydantic import BaseModel

from midscene.shared.types import Rect, Size


class AIResponseFormat(str, Enum):
    """AI response format types."""
    
    JSON = "json_object"
    TEXT = "text"


class AIUsageInfo(BaseModel):
    """AI usage information."""
    
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[float] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


class UIContext(ABC):
    """Abstract UI context for page state."""
    
    @property
    @abstractmethod
    def screenshot_base64(self) -> str:
        """Get the screenshot as base64 string."""
        pass
    
    @property
    @abstractmethod
    def size(self) -> Size:
        """Get the page size."""
        pass
    
    @property
    def is_frozen(self) -> bool:
        """Whether the context is frozen."""
        return getattr(self, "_is_frozen", False)
    
    @is_frozen.setter
    def is_frozen(self, value: bool) -> None:
        self._is_frozen = value


class SimpleUIContext(UIContext):
    """Simple implementation of UIContext."""
    
    def __init__(self, screenshot_base64: str, size: Size):
        self._screenshot_base64 = screenshot_base64
        self._size = size
        self._is_frozen = False
    
    @property
    def screenshot_base64(self) -> str:
        return self._screenshot_base64
    
    @property
    def size(self) -> Size:
        return self._size


class LocateResultElement(BaseModel):
    """Result element from locate operation."""
    
    description: str
    center: Tuple[float, float]
    rect: Rect


class LocateResult(BaseModel):
    """Result of locate operation."""
    
    element: Optional[LocateResultElement] = None
    rect: Optional[Rect] = None


class ServiceTaskInfo(BaseModel):
    """Information about a service task."""
    
    duration_ms: float = 0
    format_response: Optional[str] = None
    raw_response: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    search_area: Optional[Rect] = None
    search_area_raw_response: Optional[str] = None
    search_area_usage: Optional[AIUsageInfo] = None


class ServiceDump(BaseModel):
    """Dump of service execution."""
    
    log_time: int
    log_id: str
    type: Literal["locate", "extract", "assert"]
    user_query: Dict[str, Any] = {}
    matched_element: List[LocateResultElement] = []
    matched_rect: Optional[Rect] = None
    deep_think: bool = False
    data: Any = None
    assertion_pass: Optional[bool] = None
    assertion_thought: Optional[str] = None
    task_info: ServiceTaskInfo = ServiceTaskInfo()
    error: Optional[str] = None
    output: Any = None


class ServiceError(Exception):
    """Error from service execution."""
    
    def __init__(self, message: str, dump: Optional[ServiceDump] = None):
        super().__init__(message)
        self.name = "ServiceError"
        self.dump = dump


class PlanningAction(BaseModel):
    """A planning action to be executed."""
    
    thought: Optional[str] = None
    type: str
    param: Dict[str, Any] = {}


class PlanningAIResponse(BaseModel):
    """AI response for planning."""
    
    actions: List[PlanningAction] = []
    more_actions_needed: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None


class LocateOption(BaseModel):
    """Options for locate operation."""
    
    deep_think: bool = False
    timeout_ms: Optional[int] = None


class DetailedLocateParam(BaseModel):
    """Detailed locate parameters."""
    
    prompt: str
    deep_think: bool = False


class AgentWaitForOpt(BaseModel):
    """Options for wait for operation."""
    
    check_interval_ms: int = 3000
    timeout_ms: int = 15000


class AgentAssertOpt(BaseModel):
    """Options for assertion operation."""
    
    keep_raw_response: bool = False


class ServiceExtractOption(BaseModel):
    """Options for extract operation."""
    
    dom_included: bool = False
    screenshot_included: bool = True


class CacheConfig(BaseModel):
    """Cache configuration."""
    
    strategy: Literal["read-only", "read-write", "write-only"] = "read-write"
    id: str


CacheType = Union[bool, CacheConfig]


class AgentOpt(BaseModel):
    """Agent options."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    test_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: Optional[str] = None
    generate_report: bool = True
    auto_print_report_msg: bool = True
    on_task_start_tip: Optional[Callable[[str], Any]] = None
    ai_act_context: Optional[str] = None
    report_file_name: Optional[str] = None
    model_config_dict: Optional[Dict[str, Any]] = None
    cache: Optional[CacheType] = None
    replanning_cycle_limit: Optional[int] = None


# Execution task types
ExecutionTaskType = Literal["Planning", "Insight", "Action Space", "Log"]
ExecutionTaskStatus = Literal["pending", "running", "finished", "failed", "cancelled"]


class ExecutionRecorderItem(BaseModel):
    """Recorder item for execution."""
    
    type: Literal["screenshot"]
    ts: int
    screenshot: Optional[str] = None
    timing: Optional[str] = None


class ExecutionTask(BaseModel):
    """Execution task."""
    
    type: ExecutionTaskType
    sub_type: Optional[str] = None
    sub_task: bool = False
    param: Dict[str, Any] = {}
    thought: Optional[str] = None
    status: ExecutionTaskStatus = "pending"
    error: Optional[str] = None
    error_message: Optional[str] = None
    timing: Optional[Dict[str, Any]] = None
    usage: Optional[AIUsageInfo] = None
    recorder: List[ExecutionRecorderItem] = []
    output: Any = None
    log: Any = None


class ExecutionDump(BaseModel):
    """Dump of execution."""
    
    log_time: int
    name: str
    description: Optional[str] = None
    tasks: List[ExecutionTask] = []
    ai_act_context: Optional[str] = None


class GroupedActionDump(BaseModel):
    """Grouped action dump for reporting."""
    
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = []
    executions: List[ExecutionDump] = []


# Interface types
InterfaceType = Literal[
    "puppeteer",
    "playwright", 
    "static",
    "chrome-extension-proxy",
    "android",
]


class TestStatus(str, Enum):
    """Test execution status."""
    
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timedOut"
    SKIPPED = "skipped"
    INTERRUPTED = "interrupted"
