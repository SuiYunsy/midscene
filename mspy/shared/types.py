# -*- coding: utf-8 -*-
"""
类型定义模块
定义所有共享的数据类型和接口。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic


@dataclass
class Point:
    """表示一个二维坐标点"""
    left: int
    top: int


@dataclass
class Size:
    """表示尺寸信息"""
    width: int
    height: int
    dpr: Optional[float] = None  # 设备像素比


@dataclass
class Rect:
    """表示一个矩形区域"""
    left: int
    top: int
    width: int
    height: int
    zoom: Optional[float] = None


@dataclass
class BaseElement:
    """基础元素类型，表示页面上的一个元素"""
    id: str
    rect: Rect
    center: Tuple[int, int]
    content: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocateResultElement:
    """定位结果元素，包含元素的位置和描述信息"""
    center: Tuple[int, int]
    rect: Rect
    description: str = ""


T = TypeVar('T')


@dataclass
class ElementTreeNode(Generic[T]):
    """元素树节点，用于表示 DOM 树结构"""
    node: T
    children: List['ElementTreeNode[T]'] = field(default_factory=list)


# AI 响应格式
class AIResponseFormat:
    """AI 响应格式枚举"""
    JSON = "json_object"
    TEXT = "text"


@dataclass
class AIUsageInfo:
    """AI 使用信息，记录 token 消耗等"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[float] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


@dataclass
class AISingleElementResponseById:
    """按 ID 返回的单个元素响应"""
    id: str
    reason: Optional[str] = None
    text: Optional[str] = None
    xpaths: Optional[List[str]] = None


@dataclass
class AIElementCoordinatesResponse:
    """AI 元素坐标响应"""
    bbox: Tuple[int, int, int, int]
    errors: Optional[List[str]] = None


@dataclass
class AIDataExtractionResponse:
    """AI 数据提取响应"""
    data: Any
    errors: Optional[List[str]] = None
    thought: Optional[str] = None


@dataclass
class AISectionLocatorResponse:
    """AI 区域定位响应"""
    bbox: Tuple[int, int, int, int]
    references_bbox: Optional[List[Tuple[int, int, int, int]]] = None
    error: Optional[str] = None


@dataclass
class AIAssertionResponse:
    """AI 断言响应"""
    pass_: bool  # pass 是 Python 关键字，使用 pass_
    thought: str


@dataclass
class AIDescribeElementResponse:
    """AI 元素描述响应"""
    description: str
    error: Optional[str] = None


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
class DetailedLocateParam:
    """详细定位参数"""
    prompt: str
    deep_think: bool = False
    cacheable: bool = True
    xpath: Optional[str] = None


@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: Optional[str] = None


@dataclass
class PlanningAIResponse:
    """规划 AI 响应"""
    actions: Optional[List[PlanningAction]] = None
    more_actions_needed_by_instruction: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None


# 用户提示类型
class TMultimodalPrompt:
    """多模态提示信息"""
    def __init__(
        self,
        images: Optional[List[Dict[str, str]]] = None,
        convert_http_image_to_base64: bool = False
    ):
        self.images = images or []
        self.convert_http_image_to_base64 = convert_http_image_to_base64


# TUserPrompt 可以是字符串或带有 prompt 字段的对象
TUserPrompt = str | Dict[str, Any]


@dataclass
class ExecutionRecorderItem:
    """执行记录项"""
    type: str  # 'screenshot'
    ts: int  # 时间戳
    screenshot: Optional[str] = None
    timing: Optional[str] = None


@dataclass 
class ExecutionDump:
    """执行转储信息"""
    log_time: int
    name: str
    description: Optional[str] = None
    tasks: List[Any] = field(default_factory=list)
    ai_act_context: Optional[str] = None


@dataclass
class GroupedActionDump:
    """分组动作转储"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = field(default_factory=list)
    executions: List[ExecutionDump] = field(default_factory=list)


# YAML 脚本相关类型
@dataclass
class MidsceneYamlFlowItem:
    """YAML 流程项"""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


@dataclass
class MidsceneYamlTask:
    """YAML 任务"""
    name: str
    flow: List[MidsceneYamlFlowItem] = field(default_factory=list)
    continue_on_error: bool = False


@dataclass
class MidsceneYamlScript:
    """YAML 脚本"""
    tasks: List[MidsceneYamlTask] = field(default_factory=list)
    target: Optional[Dict[str, Any]] = None
    web: Optional[Dict[str, Any]] = None
    android: Optional[Dict[str, Any]] = None
    ios: Optional[Dict[str, Any]] = None
    agent: Optional[Dict[str, Any]] = None


class ServiceError(Exception):
    """服务错误异常"""
    def __init__(self, message: str, dump: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.dump = dump or {}
