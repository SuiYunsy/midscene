"""
共享类型定义模块
Shared type definitions for Midscene Python SDK
"""
from dataclasses import dataclass, field
from typing import Any, Optional, List, Tuple, Dict, TypedDict
from enum import Enum


@dataclass
class Rect:
    """矩形区域"""
    left: int
    top: int
    width: int
    height: int
    dpr: Optional[float] = None


@dataclass
class Size:
    """尺寸信息"""
    width: int
    height: int
    dpr: Optional[float] = None


@dataclass
class Point:
    """点坐标"""
    left: int
    top: int


@dataclass
class BaseElement:
    """基础元素信息"""
    id: str
    rect: Rect
    center: Tuple[int, int]
    content: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocateResultElement:
    """定位结果元素"""
    center: Tuple[int, int]
    rect: Rect
    description: str = ""


@dataclass 
class AIUsageInfo:
    """AI使用信息"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[float] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


class AIResponseFormat(Enum):
    """AI响应格式"""
    JSON = "json_object"
    TEXT = "text"


@dataclass
class UIContext:
    """UI上下文"""
    screenshot_base64: str
    size: Size
    _is_frozen: bool = False


@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: str = ""


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
    yaml_flow: Optional[List[Dict[str, Any]]] = None


class ServiceAction(Enum):
    """服务动作类型"""
    LOCATE = "locate"
    EXTRACT = "extract"
    ASSERT = "assert"
    DESCRIBE = "describe"


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
class ServiceDump:
    """服务转储信息"""
    type: str
    log_id: str
    log_time: int
    user_query: Dict[str, Any]
    matched_element: List[LocateResultElement]
    matched_rect: Optional[Rect] = None
    deep_think: bool = False
    data: Any = None
    assertion_pass: Optional[bool] = None
    assertion_thought: Optional[str] = None
    task_info: Optional[ServiceTaskInfo] = None
    error: Optional[str] = None
    output: Any = None


class ServiceError(Exception):
    """服务错误"""
    def __init__(self, message: str, dump: Optional[ServiceDump] = None):
        super().__init__(message)
        self.dump = dump


@dataclass
class LocateResult:
    """定位结果"""
    element: Optional[LocateResultElement] = None
    rect: Optional[Rect] = None


@dataclass
class LocateResultWithDump(LocateResult):
    """带转储的定位结果"""
    dump: Optional[ServiceDump] = None


# 定义VL模式类型
TVlModeTypes = str  # 'qwen2.5-vl' | 'qwen3-vl' | 'doubao-vision' | 'gemini' | 'vlm-ui-tars'


@dataclass
class IModelConfig:
    """模型配置"""
    model_name: str
    model_description: str = ""
    intent: str = "default"
    socks_proxy: Optional[str] = None
    http_proxy: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_extra_config: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    temperature: Optional[float] = None
    vl_mode_raw: Optional[str] = None
    vl_mode: Optional[str] = None
    skip_cert_verification: bool = False


# 定义意图类型
TIntent = str  # 'insight' | 'planning' | 'default'


# 定义可选的配置类型
TModelConfig = Dict[str, Any]


@dataclass
class DetailedLocateParam:
    """详细定位参数"""
    prompt: str
    deep_think: bool = False
    cacheable: Optional[bool] = None
    xpath: Optional[str] = None
    bbox: Optional[Tuple[int, int, int, int]] = None


@dataclass
class PlanningLocateParam(DetailedLocateParam):
    """规划定位参数，继承DetailedLocateParam"""
    pass
