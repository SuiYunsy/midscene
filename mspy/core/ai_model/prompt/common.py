# -*- coding: utf-8 -*-
"""
通用提示词工具
定义各种提示词相关的工具函数。
"""

from typing import Optional


def bbox_description(vl_mode: Optional[str]) -> str:
    """
    获取 bbox 描述文本
    
    Args:
        vl_mode: VL 模式类型
        
    Returns:
        bbox 描述字符串
    """
    if vl_mode == "gemini":
        return "box_2d bounding box for the target element, should be [ymin, xmin, ymax, xmax] normalized to 0-1000."
    return "2d bounding box as [xmin, ymin, xmax, ymax]"
