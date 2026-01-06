"""
类型定义模块
Type definitions module
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union
from enum import Enum


@dataclass
class Point:
    """Point type with left and top coordinates."""
    left: int
    top: int


@dataclass
class Size:
    """Size type with width, height and optional dpr."""
    width: int
    height: int
    dpr: Optional[float] = None


@dataclass
class Rect:
    """Rectangle type with position and size."""
    left: int
    top: int
    width: int
    height: int
    dpr: Optional[float] = None


@dataclass
class LocateResultElement:
    """Locate result element with center and rect."""
    center: Tuple[int, int]
    rect: Rect
    description: Optional[str] = None


@dataclass
class UIContext:
    """UI Context containing screenshot and size."""
    screenshot_base64: str
    size: Size
    is_frozen: bool = False


@dataclass
class PlanningAction:
    """Planning action from AI."""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: str = ""


@dataclass
class PlanningAIResponse:
    """Response from planning AI."""
    actions: List[PlanningAction] = field(default_factory=list)
    more_actions_needed_by_instruction: bool = False
    log: str = ""
    error: Optional[str] = None
    sleep: Optional[int] = None
    raw_response: Optional[str] = None


@dataclass 
class AIUsageInfo:
    """AI usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_input: int = 0
    time_cost: int = 0
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


class ServiceAction(str, Enum):
    """Service action types."""
    LOCATE = "locate"
    EXTRACT = "extract"
    ASSERT = "assert"
    DESCRIBE = "describe"


@dataclass
class ServiceDump:
    """Service dump data."""
    log_time: int
    log_id: str
    type: str
    user_query: Dict[str, Any]
    matched_element: List[LocateResultElement]
    matched_rect: Optional[Rect]
    data: Any
    task_info: Dict[str, Any]
    deep_think: bool = False
    error: Optional[str] = None


class ServiceError(Exception):
    """Service error with dump."""
    
    def __init__(self, message: str, dump: Optional[ServiceDump] = None):
        super().__init__(message)
        self.dump = dump


@dataclass
class LocateResult:
    """Locate result."""
    element: Optional[LocateResultElement]
    rect: Optional[Rect] = None


@dataclass
class LocateResultWithDump(LocateResult):
    """Locate result with dump."""
    dump: Optional[ServiceDump] = None


@dataclass
class DetailedLocateParam:
    """Detailed locate parameter."""
    prompt: str
    deep_think: bool = False
    cacheable: bool = True
    bbox: Optional[Tuple[int, int, int, int]] = None


@dataclass
class ExecutionTask:
    """Execution task."""
    type: str
    sub_type: str
    param: Any
    thought: str = ""
    status: str = "pending"
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    output: Any = None


@dataclass
class ExecutionDump:
    """Execution dump."""
    log_time: int
    name: str
    description: str = ""
    tasks: List[ExecutionTask] = field(default_factory=list)


# Action types
@dataclass
class ActionTapParam:
    """Tap action parameter."""
    locate: LocateResultElement


@dataclass
class ActionInputParam:
    """Input action parameter."""
    value: str
    locate: Optional[LocateResultElement] = None
    mode: str = "replace"  # replace, clear, append


@dataclass
class ActionScrollParam:
    """Scroll action parameter."""
    direction: str = "down"  # up, down, left, right
    scroll_type: str = "singleAction"
    distance: Optional[int] = None
    locate: Optional[LocateResultElement] = None


@dataclass
class ActionKeyboardPressParam:
    """Keyboard press action parameter."""
    key_name: str
    locate: Optional[LocateResultElement] = None


@dataclass
class ActionAssertParam:
    """Assert action parameter."""
    condition: str
    thought: str
    result: bool
