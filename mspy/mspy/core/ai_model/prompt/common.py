"""
公共Prompt工具
"""

from typing import Optional


def bbox_description(vl_mode: Optional[str]) -> str:
    """
    获取bbox描述
    
    Args:
        vl_mode: VL模式
        
    Returns:
        bbox描述字符串
    """
    if vl_mode == "gemini":
        return "box_2d bounding box for the target element, should be [ymin, xmin, ymax, xmax] normalized to 0-1000."
    return "2d bounding box as [xmin, ymin, xmax, ymax]"
