"""
核心类型定义
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict, Callable, Awaitable, Literal, Union
from pydantic import BaseModel
from enum import Enum

from mspy.shared.types import Rect, Size, LocateResultElement, AIUsageInfo


class UIContext(ABC):
    """
    UI上下文抽象类
    
    定义获取屏幕截图和尺寸的接口。
    """
    
    @property
    @abstractmethod
    def screenshot_base64(self) -> str:
        """屏幕截图的Base64编码"""
        ...
    
    @property
    @abstractmethod
    def size(self) -> Size:
        """屏幕尺寸"""
        ...
    
    @property
    def is_frozen(self) -> bool:
        """是否冻结上下文"""
        return False


class WebUIContext(UIContext):
    """Web UI上下文"""
    
    def __init__(self, screenshot_base64: str, size: Size):
        self._screenshot_base64 = screenshot_base64
        self._size = size
        self._is_frozen = False
    
    @property
    def screenshot_base64(self) -> str:
        return self._screenshot_base64
    
    @screenshot_base64.setter
    def screenshot_base64(self, value: str) -> None:
        self._screenshot_base64 = value
    
    @property
    def size(self) -> Size:
        return self._size
    
    @property
    def is_frozen(self) -> bool:
        return self._is_frozen
    
    @is_frozen.setter
    def is_frozen(self, value: bool) -> None:
        self._is_frozen = value


class ServiceAction(str, Enum):
    """服务操作类型"""
    LOCATE = "locate"
    EXTRACT = "extract"
    ASSERT = "assert"
    DESCRIBE = "describe"


class ServiceExtractOption(BaseModel):
    """服务提取选项"""
    dom_included: bool = False
    screenshot_included: bool = True


class LocateResult(BaseModel):
    """定位结果"""
    element: Optional[LocateResultElement] = None
    rect: Optional[Rect] = None


class PlanningAction(BaseModel):
    """规划动作"""
    thought: Optional[str] = None
    type: str
    param: Dict[str, Any] = {}


class PlanningAIResponse(BaseModel):
    """规划AI响应"""
    actions: Optional[List[PlanningAction]] = None
    more_actions_needed_by_instruction: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None


class ExecutionRecorderItem(BaseModel):
    """执行记录项"""
    type: Literal["screenshot"]
    ts: int
    screenshot: Optional[str] = None
    timing: Optional[str] = None


class ExecutionTaskStatus(str, Enum):
    """执行任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionTaskTiming(BaseModel):
    """执行任务时间信息"""
    start: int
    end: Optional[int] = None
    cost: Optional[int] = None


class ExecutionTask(BaseModel):
    """执行任务"""
    type: str  # Planning, Insight, Action Space, Log
    sub_type: Optional[str] = None
    sub_task: bool = False
    param: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None
    status: ExecutionTaskStatus = ExecutionTaskStatus.PENDING
    output: Optional[Any] = None
    log: Optional[Any] = None
    recorder: Optional[List[ExecutionRecorderItem]] = None
    error: Optional[str] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    timing: Optional[ExecutionTaskTiming] = None
    usage: Optional[AIUsageInfo] = None
    
    class Config:
        arbitrary_types_allowed = True


class ExecutionDump(BaseModel):
    """执行转储"""
    log_time: int
    name: str
    description: Optional[str] = None
    tasks: List[ExecutionTask] = []
    ai_act_context: Optional[str] = None


class GroupedActionDump(BaseModel):
    """分组操作转储"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = []
    executions: List[ExecutionDump] = []


class ServiceError(Exception):
    """服务错误"""
    
    def __init__(self, message: str, dump: Optional[Any] = None):
        super().__init__(message)
        self.dump = dump


# Agent相关类型

class AgentWaitForOpt(BaseModel):
    """等待选项"""
    check_interval_ms: Optional[int] = None
    timeout_ms: Optional[int] = None


class AgentAssertOpt(BaseModel):
    """断言选项"""
    keep_raw_response: bool = False


class CacheStrategy(str, Enum):
    """缓存策略"""
    READ_ONLY = "read-only"
    READ_WRITE = "read-write"
    WRITE_ONLY = "write-only"


class CacheConfig(BaseModel):
    """缓存配置"""
    strategy: Optional[CacheStrategy] = None
    id: str


class ScrollDirection(str, Enum):
    """滚动方向"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class ScrollType(str, Enum):
    """滚动类型"""
    SINGLE_ACTION = "singleAction"
    SCROLL_TO_BOTTOM = "scrollToBottom"
    SCROLL_TO_TOP = "scrollToTop"
    SCROLL_TO_RIGHT = "scrollToRight"
    SCROLL_TO_LEFT = "scrollToLeft"


class ScrollParam(BaseModel):
    """滚动参数"""
    direction: Optional[ScrollDirection] = None
    scroll_type: Optional[ScrollType] = None
    distance: Optional[int] = None


class LocateOption(BaseModel):
    """定位选项"""
    deep_think: bool = False
    cacheable: bool = True
    
    class Config:
        extra = "allow"


class DetailedLocateParam(BaseModel):
    """详细定位参数"""
    prompt: str
    deep_think: bool = False
    cacheable: bool = True
    
    class Config:
        extra = "allow"
