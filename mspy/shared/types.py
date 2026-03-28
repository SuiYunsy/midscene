# -*- coding: utf-8 -*-
"""
Midscene Type Definitions
类型定义模块
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union


@dataclass
class Point:
    """点坐标"""
    left: int
    top: int


@dataclass
class Size:
    """尺寸"""
    width: int
    height: int
    dpr: Optional[float] = None


@dataclass
class Rect:
    """矩形区域"""
    left: int
    top: int
    width: int
    height: int
    dpr: Optional[float] = None
    zoom: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }
        if self.dpr is not None:
            result["dpr"] = self.dpr
        if self.zoom is not None:
            result["zoom"] = self.zoom
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rect":
        """从字典创建"""
        return cls(
            left=data.get("left", 0),
            top=data.get("top", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            dpr=data.get("dpr"),
            zoom=data.get("zoom"),
        )


@dataclass
class LocateResultElement:
    """定位结果元素"""
    center: Tuple[int, int]
    rect: Rect
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "center": list(self.center),
            "rect": self.rect.to_dict(),
        }
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class UIContext:
    """UI上下文"""
    screenshot_base64: str
    size: Size
    _is_frozen: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "screenshotBase64": self.screenshot_base64,
            "size": {
                "width": self.size.width,
                "height": self.size.height,
                "dpr": self.size.dpr,
            },
            "_isFrozen": self._is_frozen,
        }


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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cached_input": self.cached_input,
            "time_cost": self.time_cost,
            "model_name": self.model_name,
            "model_description": self.model_description,
            "intent": self.intent,
        }


@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "type": self.type,
            "param": self.param,
        }
        if self.thought is not None:
            result["thought"] = self.thought
        return result


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
class DetailedLocateParam:
    """详细定位参数"""
    prompt: str
    deep_think: bool = False
    cacheable: bool = True
    xpath: Optional[str] = None
    bbox: Optional[Tuple[int, int, int, int]] = None


@dataclass
class ServiceDump:
    """服务转储"""
    type: str
    log_id: str
    log_time: int
    user_query: Dict[str, Any] = field(default_factory=dict)
    matched_element: List[LocateResultElement] = field(default_factory=list)
    matched_rect: Optional[Rect] = None
    data: Any = None
    task_info: Dict[str, Any] = field(default_factory=dict)
    deep_think: bool = False
    error: Optional[str] = None


class ServiceError(Exception):
    """服务错误"""
    
    def __init__(self, message: str, dump: Optional[ServiceDump] = None):
        super().__init__(message)
        self.dump = dump


@dataclass 
class ExecutionTaskTiming:
    """执行任务时间信息"""
    start: int
    end: Optional[int] = None
    cost: Optional[int] = None


@dataclass
class ExecutionTask:
    """执行任务"""
    type: str
    sub_type: Optional[str] = None
    status: str = "pending"  # pending, running, finished, failed, cancelled
    param: Any = None
    thought: Optional[str] = None
    output: Any = None
    log: Any = None
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    timing: Optional[ExecutionTaskTiming] = None
    usage: Optional[AIUsageInfo] = None
    recorder: List[Dict[str, Any]] = field(default_factory=list)
    sub_task: bool = False
    ui_context: Optional[UIContext] = None
    hit_by: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionDump:
    """执行转储"""
    log_time: int
    name: str
    description: Optional[str] = None
    tasks: List[ExecutionTask] = field(default_factory=list)
    ai_act_context: Optional[str] = None


@dataclass
class GroupedActionDump:
    """分组动作转储"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = field(default_factory=list)
    executions: List[ExecutionDump] = field(default_factory=list)


# 类型别名
TUserPrompt = Union[str, Dict[str, Any]]
ServiceAction = str  # "locate" | "extract" | "assert" | "describe"
ServiceExtractParam = Union[str, Dict[str, str]]
