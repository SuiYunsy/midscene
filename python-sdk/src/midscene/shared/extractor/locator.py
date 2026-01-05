"""Element locator utilities."""

from typing import Any, Dict, List, Optional, Tuple

from midscene.shared.types import ElementInfo, Rect


class Locator:
    """Utility class for locating elements."""
    
    def __init__(self, elements: List[ElementInfo]):
        """
        Initialize locator with elements.
        
        Args:
            elements: List of elements to search within
        """
        self.elements = elements
    
    def find_by_content(self, content: str) -> List[ElementInfo]:
        """
        Find elements by text content.
        
        Args:
            content: Text to search for
            
        Returns:
            Matching elements
        """
        return [
            el for el in self.elements
            if content.lower() in el.content.lower()
        ]
    
    def find_by_id(self, element_id: str) -> Optional[ElementInfo]:
        """
        Find element by ID.
        
        Args:
            element_id: Element ID to find
            
        Returns:
            Matching element or None
        """
        for el in self.elements:
            if el.id == element_id:
                return el
        return None
    
    def find_at_point(
        self, 
        x: float, 
        y: float
    ) -> List[ElementInfo]:
        """
        Find elements at a specific point.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Elements containing the point
        """
        results = []
        for el in self.elements:
            rect = el.rect
            if (rect.left <= x <= rect.left + rect.width and
                rect.top <= y <= rect.top + rect.height):
                results.append(el)
        return results
