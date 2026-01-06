# -*- coding: utf-8 -*-
"""
core 模块类型定义
定义核心模块使用的数据类型。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod

from mspy.shared.types import (
    Rect,
    Size,
    Point,
    LocateResultElement,
    AIUsageInfo,
    ServiceTaskInfo,
    ExecutionRecorderItem,
    ExecutionDump,
    GroupedActionDump,
    PlanningAction,
    PlanningAIResponse,
    DetailedLocateParam,
    MidsceneYamlFlowItem,
)


class UIContext(ABC):
    """UI 上下文抽象类"""
    
    @property
    @abstractmethod
    def screenshot_base64(self) -> str:
        """获取截图的 base64 编码"""
        pass
    
    @property
    @abstractmethod
    def size(self) -> Size:
        """获取页面尺寸"""
        pass
    
    @property
    def is_frozen(self) -> bool:
        """是否被冻结"""
        return False


@dataclass
class ServiceDump:
    """服务转储信息"""
    type: str  # 'locate' | 'extract' | 'assert'
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
    """服务错误异常"""
    
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
    """带转储信息的定位结果"""
    dump: Optional[ServiceDump] = None


@dataclass
class ServiceExtractResult:
    """服务提取结果"""
    data: Any
    thought: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    dump: Optional[ServiceDump] = None


@dataclass
class ServiceAssertionResponse:
    """服务断言响应"""
    pass_: bool  # pass 是 Python 关键字
    thought: str
    usage: Optional[AIUsageInfo] = None


# 任务相关类型
@dataclass
class ExecutionTask:
    """执行任务"""
    type: str  # 'Planning' | 'Insight' | 'Action Space' | 'Log'
    sub_type: Optional[str] = None
    sub_task: bool = False
    param: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None
    ui_context: Optional[UIContext] = None
    
    status: str = "pending"  # 'pending' | 'running' | 'finished' | 'failed' | 'cancelled'
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    
    output: Any = None
    log: Any = None
    recorder: Optional[List[ExecutionRecorderItem]] = None
    
    timing: Optional[Dict[str, Any]] = None
    usage: Optional[AIUsageInfo] = None


# Action 相关类型
@dataclass
class DeviceAction:
    """设备动作定义"""
    name: str
    description: str = ""
    interface_alias: Optional[str] = None
    param_schema: Optional[Any] = None  # 可以是 Pydantic 模型或字典
    call: Optional[Callable] = None
    delay_after_runner: Optional[int] = None


# Agent 配置
@dataclass
class AgentOpt:
    """Agent 配置选项"""
    test_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: str = ""
    generate_report: bool = True
    auto_print_report_msg: bool = True
    on_task_start_tip: Optional[Callable[[str], None]] = None
    ai_act_context: Optional[str] = None
    report_file_name: Optional[str] = None
    model_config: Optional[Dict[str, str]] = None
    replanning_cycle_limit: Optional[int] = None


# 滚动参数
@dataclass
class ScrollParam:
    """滚动参数"""
    scroll_type: str = "singleAction"  # 'singleAction' | 'scrollToBottom' | 'scrollToTop' | 'scrollToRight' | 'scrollToLeft'
    direction: str = "down"  # 'down' | 'up' | 'right' | 'left'
    distance: Optional[int] = None


# 重新导出 shared 中的类型
__all__ = [
    "UIContext",
    "ServiceDump",
    "ServiceError",
    "LocateResult",
    "LocateResultWithDump",
    "ServiceExtractResult",
    "ServiceAssertionResponse",
    "ExecutionTask",
    "DeviceAction",
    "AgentOpt",
    "ScrollParam",
    # 从 shared 重导出
    "AIUsageInfo",
    "ServiceTaskInfo",
    "ExecutionRecorderItem",
    "ExecutionDump",
    "GroupedActionDump",
    "PlanningAction",
    "PlanningAIResponse",
    "DetailedLocateParam",
    "MidsceneYamlFlowItem",
    "Rect",
    "Size",
    "Point",
    "LocateResultElement",
]
