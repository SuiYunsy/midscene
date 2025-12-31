"""
共享类型定义

定义基础类型，如Point、Size、Rect、BaseElement等。
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel
from enum import Enum


class NodeType(str, Enum):
    """节点类型"""
    CONTAINER = "CONTAINER Node"
    FORM_ITEM = "FORM_ITEM Node"
    BUTTON = "BUTTON Node"
    A = "Anchor Node"
    IMG = "IMG Node"
    TEXT = "TEXT Node"
    POSITION = "POSITION Node"


class Point(BaseModel):
    """点坐标"""
    left: float
    top: float


class Size(BaseModel):
    """尺寸"""
    width: float
    height: float
    dpr: Optional[float] = None  # 已废弃，不要使用


class Rect(BaseModel):
    """矩形区域"""
    left: float
    top: float
    width: float
    height: float
    zoom: Optional[float] = None


class BaseElement(ABC):
    """
    基础元素抽象类
    
    所有UI元素的基类。
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """元素ID"""
        ...
    
    @property
    @abstractmethod
    def attributes(self) -> dict[str, str]:
        """元素属性"""
        ...
    
    @property
    @abstractmethod
    def content(self) -> str:
        """元素内容"""
        ...
    
    @property
    @abstractmethod
    def rect(self) -> Rect:
        """元素矩形区域"""
        ...
    
    @property
    @abstractmethod
    def center(self) -> tuple[float, float]:
        """元素中心点坐标"""
        ...
    
    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """元素是否可见"""
        ...


class ElementTreeNode(BaseModel):
    """元素树节点"""
    node: Optional[Any] = None  # BaseElement实例
    children: list["ElementTreeNode"] = []
    
    class Config:
        arbitrary_types_allowed = True


class LocateResultElement(BaseModel):
    """定位结果元素"""
    description: str  # 元素描述
    center: tuple[float, float]  # 中心点坐标
    rect: Rect  # 矩形区域


class AIUsageInfo(BaseModel):
    """AI使用信息"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[int] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


class ServiceTaskInfo(BaseModel):
    """服务任务信息"""
    duration_ms: int
    format_response: Optional[str] = None
    raw_response: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    search_area: Optional[Rect] = None
    search_area_raw_response: Optional[str] = None
    search_area_usage: Optional[AIUsageInfo] = None
