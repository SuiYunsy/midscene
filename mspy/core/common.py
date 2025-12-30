# -*- coding: utf-8 -*-
"""
通用工具函数
提供核心模块使用的通用工具函数。
"""

from typing import Optional, Tuple, List

from mspy.shared.types import Rect, Size


def adapt_bbox_to_rect(
    bbox: List[int],
    image_width: int,
    image_height: int,
    offset_left: int = 0,
    offset_top: int = 0,
    original_width: Optional[int] = None,
    original_height: Optional[int] = None,
    vl_mode: Optional[str] = None,
) -> Rect:
    """
    将 bbox 转换为 Rect
    
    Args:
        bbox: 边界框 [xmin, ymin, xmax, ymax] 或 [ymin, xmin, ymax, xmax] (Gemini)
        image_width: 图像宽度
        image_height: 图像高度
        offset_left: 左偏移
        offset_top: 上偏移
        original_width: 原始宽度
        original_height: 原始高度
        vl_mode: VL 模式
        
    Returns:
        矩形区域
    """
    original_width = original_width or image_width
    original_height = original_height or image_height
    
    if len(bbox) < 4:
        raise ValueError(f"Invalid bbox: {bbox}")
    
    # Gemini 使用 [ymin, xmin, ymax, xmax] 归一化到 0-1000
    if vl_mode == "gemini":
        ymin, xmin, ymax, xmax = bbox[:4]
        # 归一化坐标
        left = int(xmin * original_width / 1000)
        top = int(ymin * original_height / 1000)
        right = int(xmax * original_width / 1000)
        bottom = int(ymax * original_height / 1000)
    else:
        # 标准格式 [xmin, ymin, xmax, ymax]
        xmin, ymin, xmax, ymax = bbox[:4]
        left = int(xmin)
        top = int(ymin)
        right = int(xmax)
        bottom = int(ymax)
    
    # 添加偏移
    left += offset_left
    top += offset_top
    
    # 计算宽高
    width = right - xmin
    height = bottom - ymin
    
    return Rect(
        left=max(0, left),
        top=max(0, top),
        width=max(1, width),
        height=max(1, height),
    )


def expand_search_area(
    rect: Rect,
    page_size: Size,
    vl_mode: Optional[str] = None,
    min_size: int = 200,
) -> Rect:
    """
    扩展搜索区域
    
    Args:
        rect: 原始矩形
        page_size: 页面尺寸
        vl_mode: VL 模式
        min_size: 最小尺寸
        
    Returns:
        扩展后的矩形
    """
    # 确保最小尺寸
    target_width = max(rect.width, min_size)
    target_height = max(rect.height, min_size)
    
    # 计算扩展量
    expand_w = (target_width - rect.width) // 2
    expand_h = (target_height - rect.height) // 2
    
    # 扩展矩形
    left = max(0, rect.left - expand_w)
    top = max(0, rect.top - expand_h)
    right = min(page_size.width, rect.left + rect.width + expand_w)
    bottom = min(page_size.height, rect.top + rect.height + expand_h)
    
    return Rect(
        left=left,
        top=top,
        width=right - left,
        height=bottom - top,
    )


def merge_rects(rects: List[Rect]) -> Rect:
    """
    合并多个矩形为一个包含所有矩形的最小矩形
    
    Args:
        rects: 矩形列表
        
    Returns:
        合并后的矩形
    """
    if not rects:
        raise ValueError("Cannot merge empty rect list")
    
    if len(rects) == 1:
        return rects[0]
    
    left = min(r.left for r in rects)
    top = min(r.top for r in rects)
    right = max(r.left + r.width for r in rects)
    bottom = max(r.top + r.height for r in rects)
    
    return Rect(
        left=left,
        top=top,
        width=right - left,
        height=bottom - top,
    )


def overlapped(container: Rect, target: Rect) -> bool:
    """
    检查两个矩形是否重叠
    
    Args:
        container: 容器矩形
        target: 目标矩形
        
    Returns:
        是否重叠
    """
    return (
        container.left < target.left + target.width and
        container.left + container.width > target.left and
        container.top < target.top + target.height and
        container.top + container.height > target.top
    )


async def sleep(ms: int) -> None:
    """
    异步睡眠
    
    Args:
        ms: 毫秒数
    """
    import asyncio
    await asyncio.sleep(ms / 1000)


def replacer_for_page_object(key: str, value) -> str:
    """
    用于 JSON 序列化的替换函数
    
    Args:
        key: 键名
        value: 值
        
    Returns:
        替换后的值
    """
    if value and hasattr(value, "__class__"):
        class_name = value.__class__.__name__
        if class_name == "Page":
            return "[Page object]"
        if class_name == "Browser":
            return "[Browser object]"
    return value
