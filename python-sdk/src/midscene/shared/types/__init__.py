"""Base types for Midscene."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel

from midscene.shared.constants import NodeType


class Point(BaseModel):
    """A point in 2D space."""
    
    left: float
    top: float


class Size(BaseModel):
    """Size dimensions."""
    
    width: float  # Logical pixel width
    height: float  # Logical pixel height
    dpr: Optional[float] = None  # Deprecated, do not use


class Rect(Point, Size):
    """A rectangle with position and size."""
    
    zoom: Optional[float] = None


class BaseElement(ABC):
    """Abstract base class for UI elements."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Element unique identifier."""
        pass
    
    @property
    @abstractmethod
    def attributes(self) -> Dict[str, str]:
        """Element attributes including nodeType."""
        pass
    
    @property
    @abstractmethod
    def content(self) -> str:
        """Element text content."""
        pass
    
    @property
    @abstractmethod
    def rect(self) -> Rect:
        """Element bounding rectangle."""
        pass
    
    @property
    @abstractmethod
    def center(self) -> Tuple[float, float]:
        """Element center coordinates."""
        pass
    
    @property
    @abstractmethod
    def is_visible(self) -> bool:
        """Whether the element is visible."""
        pass


ElementType = TypeVar("ElementType", bound=BaseElement)


class ElementTreeNode(BaseModel, Generic[ElementType]):
    """Tree node for element hierarchy."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    node: Optional[Any] = None  # ElementType
    children: List["ElementTreeNode[ElementType]"] = []


class ElementInfo(BaseModel):
    """Information about a UI element."""
    
    id: str
    node_type: str
    content: str
    rect: Rect
    center: Tuple[float, float]
    attributes: Dict[str, str] = {}
    is_visible: bool = True


class WebElementInfo(ElementInfo):
    """Web-specific element information."""
    
    zoom: float = 1.0


class LocateResultElement(BaseModel):
    """Result of locating an element."""
    
    description: str  # Description of the element
    center: Tuple[float, float]
    rect: Rect
