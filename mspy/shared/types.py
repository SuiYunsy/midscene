"""
Types - 类型定义模块
包含所有核心数据类型和接口定义
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Awaitable
from abc import ABC, abstractmethod
import uuid as uuid_lib


class NodeType(str, Enum):
    """节点类型枚举"""
    TEXT = "TEXT"
    BUTTON = "BUTTON"
    INPUT = "INPUT"
    IMG = "IMG"
    FORM_ITEM = "FORM_ITEM"
    CONTAINER = "CONTAINER"


@dataclass
class Point:
    """坐标点"""
    left: float
    top: float


@dataclass
class Size:
    """尺寸"""
    width: float  # 图像宽度（逻辑像素）
    height: float  # 图像高度（逻辑像素）
    dpr: Optional[float] = None  # 已弃用，请勿使用


@dataclass
class Rect(Point, Size):
    """矩形区域"""
    zoom: Optional[float] = None


@dataclass
class AIUsageInfo:
    """AI 使用信息"""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_input: Optional[int] = None
    time_cost: Optional[float] = None
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    intent: Optional[str] = None


@dataclass
class AIAssertionResponse:
    """AI 断言响应"""
    passed: bool
    thought: str


@dataclass
class LocateResultElement:
    """定位结果元素"""
    description: str  # 元素描述
    center: tuple[float, float]  # 中心坐标
    rect: Rect  # 矩形区域


class BaseElement(ABC):
    """基础元素抽象类"""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """元素 ID"""
        pass
    
    @property
    @abstractmethod
    def attributes(self) -> Dict[str, str]:
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
    def center(self) -> tuple[float, float]:
        """元素中心坐标"""
        pass
    
    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """元素是否可见"""
        pass


@dataclass
class ElementTreeNode:
    """元素树节点"""
    node: Optional[BaseElement] = None
    children: List["ElementTreeNode"] = field(default_factory=list)


@dataclass
class PlanningAction:
    """规划动作"""
    type: str
    param: Dict[str, Any] = field(default_factory=dict)
    thought: Optional[str] = None


@dataclass
class PlanningAIResponse:
    """规划 AI 响应"""
    actions: List[PlanningAction] = field(default_factory=list)
    more_actions_needed_by_instruction: bool = False
    log: str = ""
    sleep: Optional[int] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None
    raw_response: Optional[str] = None


class UIContext(ABC):
    """UI 上下文抽象类"""
    
    @property
    @abstractmethod
    def screenshot_base64(self) -> str:
        """截图 base64 编码"""
        pass
    
    @property
    @abstractmethod
    def size(self) -> Size:
        """页面尺寸"""
        pass
    
    @property
    def is_frozen(self) -> bool:
        """是否冻结"""
        return getattr(self, '_is_frozen', False)
    
    @is_frozen.setter
    def is_frozen(self, value: bool):
        self._is_frozen = value


@dataclass
class DeviceAction:
    """设备动作定义"""
    name: str
    description: str = ""
    interface_alias: Optional[str] = None
    param_schema: Optional[Any] = None  # Pydantic model or dict schema
    call: Optional[Callable[..., Any]] = None
    delay_after_runner: Optional[int] = None


# 类型别名
TIntent = str  # 'insight' | 'planning' | 'default'
TModelConfig = Dict[str, Union[str, int, None]]

# VL 模式类型
TVlModeTypes = str  # 'qwen2.5-vl' | 'qwen3-vl' | 'doubao-vision' | 'gemini' | 'vlm-ui-tars'


@dataclass
class IModelConfig:
    """模型配置接口"""
    model_name: str
    model_description: str = ""
    intent: str = "default"
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_extra_config: Optional[Dict[str, Any]] = None
    socks_proxy: Optional[str] = None
    http_proxy: Optional[str] = None
    timeout: Optional[int] = None
    temperature: float = 0.0
    vl_mode_raw: Optional[str] = None
    vl_mode: Optional[str] = None  # TVlModeTypes
    ui_tars_model_version: Optional[str] = None
    create_openai_client: Optional[Callable[..., Any]] = None
