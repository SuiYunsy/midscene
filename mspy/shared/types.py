"""
类型定义

从 packages/shared/src/types/index.ts 迁移
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar

from mspy.shared.constants import NodeType


@dataclass
class Point:
    """坐标点"""
    left: int
    top: int


@dataclass
class Size:
    """尺寸"""
    width: int
    height: int
    dpr: Optional[float] = None  # 已弃用，不要使用


@dataclass
class Rect:
    """矩形区域"""
    left: int
    top: int
    width: int
    height: int
    zoom: Optional[float] = None
    dpr: Optional[float] = None


class BaseElement(ABC):
    """元素基类"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """元素ID"""
        pass
    
    @property
    @abstractmethod
    def attributes(self) -> dict[str, Any]:
        """元素属性，必须包含 nodeType"""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """元素内容"""
        pass
    
    @property
    @abstractmethod
    def rect(self) -> Rect:
        """元素矩形区域"""
        pass
    
    @property
    @abstractmethod
    def center(self) -> tuple[int, int]:
        """元素中心坐标"""
        pass
    
    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """元素是否可见"""
        pass


ElementType = TypeVar("ElementType", bound=BaseElement)


@dataclass
class ElementTreeNode(Generic[ElementType]):
    """元素树节点"""
    node: Optional[ElementType] = None
    children: list["ElementTreeNode[ElementType]"] = field(default_factory=list)


@dataclass
class LocateResultElement:
    """定位结果元素"""
    description: str  # 元素描述
    center: tuple[int, int]  # 中心坐标
    rect: Rect  # 矩形区域
