"""
Prompt Utilities

Corresponding to TypeScript source: packages/core/src/ai-model/prompt/util.ts
"""

from typing import Any


def describe_size(size: Any) -> str:
    """Describe the size of a page
    
    Args:
        size: Size object with width and height
        
    Returns:
        Size description string
    """
    if hasattr(size, 'width') and hasattr(size, 'height'):
        return f"{size.width} x {size.height}"
    elif isinstance(size, dict):
        return f"{size.get('width', 0)} x {size.get('height', 0)}"
    return "Unknown size"


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Get attribute from object or dict
    
    Args:
        obj: Object or dict
        name: Attribute name
        default: Default value if not found
        
    Returns:
        Attribute value
    """
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def describe_element(elements: list) -> str:
    """Describe elements for prompts
    
    Args:
        elements: List of element objects
        
    Returns:
        Element descriptions
    """
    slice_length = 80
    descriptions = []
    
    for item in elements:
        element_id = _get_attr(item, 'id', '')
        rect = _get_attr(item, 'rect', {})
        content = _get_attr(item, 'content', '')
        
        left = _get_attr(rect, 'left', 0)
        top = _get_attr(rect, 'top', 0)
        width = _get_attr(rect, 'width', 0)
        height = _get_attr(rect, 'height', 0)
        
        truncated_content = content[:slice_length] + '...' if len(content) > slice_length else content
        
        descriptions.append(
            f"{element_id}, {left}, {top}, {left + width}, {top + height}, {truncated_content}"
        )
    
    return '\n'.join(descriptions)


# Distance threshold for element matching
DISTANCE_THRESHOLD = 16


def distance(point1: dict, point2: dict) -> float:
    """Calculate distance between two points
    
    Args:
        point1: First point {x, y}
        point2: Second point {x, y}
        
    Returns:
        Distance between points
    """
    x1, y1 = point1.get('x', 0), point1.get('y', 0)
    x2, y2 = point2.get('x', 0), point2.get('y', 0)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


SAMPLE_PAGE_DESCRIPTION = """
And the page is described as follows:
====================
The size of the page: 1280 x 720
Some of the elements are marked with a rectangle in the screenshot corresponding to the markerId, some are not.

Description of all the elements in screenshot:
<div id="969f1637" markerId="1" left="100" top="100" width="100" height="100"> // The markerId indicated by the rectangle label in the screenshot
  <h4 id="b211ecb2" markerId="5" left="150" top="150" width="90" height="60">
    The username is accepted
  </h4>
  ...many more
</div>
====================
"""


async def describe_user_page(context: Any) -> str:
    """Describe user page from context
    
    Args:
        context: UI context object
        
    Returns:
        Page description string
    """
    size = context.size if hasattr(context, 'size') else context.get('size', {})
    return f"The size of the page: {describe_size(size)}"
