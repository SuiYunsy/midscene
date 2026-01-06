"""
类型定义模块 - 定义Midscene中使用的基本类型

对应TypeScript源码: packages/shared/src/types/index.ts
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypedDict, Generic, TypeVar


@dataclass
class Point:
    """点坐标类型"""
    left: float
    top: float


@dataclass 
class Size:
    """尺寸类型
    
    Attributes:
        width: 图片宽度（逻辑像素）
        height: 图片高度（逻辑像素）
        dpr: 设备像素比（已废弃，请勿使用）
    """
    width: float
    height: float
    dpr: Optional[float] = None  # deprecated


@dataclass
class Rect(Point, Size):
    """矩形区域类型，包含位置和尺寸
    
    Attributes:
        left: 左边界坐标
        top: 上边界坐标
        width: 宽度
        height: 高度
        zoom: 缩放比例（可选）
    """
    left: float = 0
    top: float = 0
    width: float = 0
    height: float = 0
    zoom: Optional[float] = None


class NodeType:
    """节点类型常量"""
    TEXT = "TEXT"
    IMG = "IMG"
    BUTTON = "BUTTON"
    INPUT = "INPUT"
    FORM_ITEM = "FORM_ITEM"
    CONTAINER = "CONTAINER"


class BaseElement(ABC):
    """基础元素抽象类
    
    定义了所有UI元素的基本属性和方法
    """
    
    @property
    @abstractmethod
    def id(self) -> str:
        """元素唯一标识符"""
        pass
    
    @property
    @abstractmethod
    def attributes(self) -> Dict[str, str]:
        """元素属性字典，必须包含nodeType键"""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """元素文本内容"""
        pass
    
    @property
    @abstractmethod
    def rect(self) -> Rect:
        """元素的矩形区域"""
        pass
    
    @property
    @abstractmethod
    def center(self) -> tuple:
        """元素中心点坐标 (x, y)"""
        pass
    
    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """元素是否可见"""
        pass


T = TypeVar('T', bound=BaseElement)


@dataclass
class ElementTreeNode(Generic[T]):
    """元素树节点
    
    用于表示页面元素的层级结构
    
    Attributes:
        node: 当前节点的元素（可为空）
        children: 子节点列表
    """
    node: Optional[T] = None
    children: List['ElementTreeNode[T]'] = field(default_factory=list)


@dataclass
class LocateResultElement:
    """定位结果元素
    
    AI定位后返回的元素信息
    
    Attributes:
        description: 元素描述
        center: 元素中心点坐标 [x, y]
        rect: 元素矩形区域
    """
    description: str
    center: tuple  # [number, number]
    rect: Rect


@dataclass
class WebElementInfo(BaseElement):
    """Web元素信息
    
    继承自BaseElement，添加zoom属性
    """
    _id: str
    _attributes: Dict[str, str]
    _content: str
    _rect: Rect
    _center: tuple
    _is_visible: bool
    zoom: float = 1.0
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def attributes(self) -> Dict[str, str]:
        return self._attributes
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def rect(self) -> Rect:
        return self._rect
    
    @property
    def center(self) -> tuple:
        return self._center
    
    @property
    def is_visible(self) -> bool:
        return self._is_visible


# AI响应相关类型
class AIResponseFormat:
    """AI响应格式"""
    JSON = "json_object"
    TEXT = "text"


@dataclass
class AIUsageInfo:
    """AI使用信息
    
    记录AI调用的token使用情况
    """
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[float] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


@dataclass
class AISingleElementResponse:
    """AI单元素响应"""
    id: str
    reason: Optional[str] = None
    text: Optional[str] = None
    xpaths: Optional[List[str]] = None


@dataclass
class AIElementCoordinatesResponse:
    """AI元素坐标响应"""
    bbox: tuple  # [number, number, number, number]
    errors: Optional[List[str]] = None


@dataclass
class AIDataExtractionResponse(Generic[T]):
    """AI数据提取响应"""
    data: T
    errors: Optional[List[str]] = None
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
