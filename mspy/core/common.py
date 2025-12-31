# -*- coding: utf-8 -*-
"""
Midscene Common Module
通用函数和常量模块
"""

from typing import Dict, Any, List, Optional, Tuple

from ..shared import (
    Rect,
    Size,
    PlanningAction,
    assert_condition,
)


def normalized_0_1000(
    bbox: List[int],
    width: int,
    height: int,
) -> Tuple[int, int, int, int]:
    """
    将0-1000归一化的bbox转换为实际像素坐标
    x1, y1, x2, y2 -> 0-1000
    """
    return (
        round((bbox[0] * width) / 1000),
        round((bbox[1] * height) / 1000),
        round((bbox[2] * width) / 1000),
        round((bbox[3] * height) / 1000),
    )


def adapt_bbox(
    bbox: Any,
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str] = None,
) -> Tuple[int, int, int, int]:
    """
    适配bbox坐标
    
    Args:
        bbox: 原始bbox
        width: 图像宽度
        height: 图像高度
        right_limit: 右边界限制
        bottom_limit: 下边界限制
        vl_mode: VL模式
    
    Returns:
        适配后的bbox (left, top, right, bottom)
    """
    # 处理嵌套数组
    normalized_bbox = bbox
    if isinstance(bbox, list) and len(bbox) > 0 and isinstance(bbox[0], list):
        normalized_bbox = bbox[0]
    
    # 确保是数字列表
    if isinstance(normalized_bbox, str):
        # 尝试解析字符串格式的bbox
        parts = normalized_bbox.split()
        normalized_bbox = [int(p) for p in parts]
    
    # qwen3-vl使用0-1000归一化
    if vl_mode == "qwen3-vl":
        result = normalized_0_1000(normalized_bbox, width, height)
    else:
        # 默认直接使用坐标
        result = (
            round(normalized_bbox[0]),
            round(normalized_bbox[1]),
            round(normalized_bbox[2]) if len(normalized_bbox) > 2 else round(normalized_bbox[0] + 20),
            round(normalized_bbox[3]) if len(normalized_bbox) > 3 else round(normalized_bbox[1] + 20),
        )
    
    # 应用边界限制
    result = (
        result[0],
        result[1],
        min(result[2], right_limit),
        min(result[3], bottom_limit),
    )
    
    return result


def fill_bbox_param(
    locate: Dict[str, Any],
    width: int,
    height: int,
    right_limit: int,
    bottom_limit: int,
    vl_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    填充定位参数中的bbox
    
    Args:
        locate: 定位参数
        width: 图像宽度
        height: 图像高度
        right_limit: 右边界限制
        bottom_limit: 下边界限制
        vl_mode: VL模式
    
    Returns:
        处理后的定位参数
    """
    # 处理bbox_2d别名
    if "bbox_2d" in locate and "bbox" not in locate:
        locate["bbox"] = locate.pop("bbox_2d")
    
    if "bbox" in locate and locate["bbox"]:
        locate["bbox"] = list(adapt_bbox(
            locate["bbox"],
            width,
            height,
            right_limit,
            bottom_limit,
            vl_mode,
        ))
    
    return locate


def adapt_bbox_to_rect(
    bbox: List[int],
    width: int,
    height: int,
    offset_x: int = 0,
    offset_y: int = 0,
    right_limit: Optional[int] = None,
    bottom_limit: Optional[int] = None,
    vl_mode: Optional[str] = None,
) -> Rect:
    """
    将bbox转换为Rect
    
    Args:
        bbox: bbox坐标
        width: 图像宽度
        height: 图像高度
        offset_x: X偏移
        offset_y: Y偏移
        right_limit: 右边界限制
        bottom_limit: 下边界限制
        vl_mode: VL模式
    
    Returns:
        Rect对象
    """
    if right_limit is None:
        right_limit = width
    if bottom_limit is None:
        bottom_limit = height
    
    left, top, right, bottom = adapt_bbox(
        bbox,
        width,
        height,
        right_limit,
        bottom_limit,
        vl_mode,
    )
    
    rect_width = right - left
    rect_height = bottom - top
    
    # 确保不超过图像边界
    if left + rect_width > width:
        rect_width = width - left
    if top + rect_height > height:
        rect_height = height - top
    
    # 确保最小尺寸
    rect_width = max(1, rect_width)
    rect_height = max(1, rect_height)
    
    return Rect(
        left=left + offset_x,
        top=top + offset_y,
        width=rect_width,
        height=rect_height,
    )


def merge_rects(rects: List[Rect]) -> Rect:
    """
    合并多个矩形
    
    Args:
        rects: 矩形列表
    
    Returns:
        合并后的矩形
    """
    min_left = min(r.left for r in rects)
    min_top = min(r.top for r in rects)
    max_right = max(r.left + r.width for r in rects)
    max_bottom = max(r.top + r.height for r in rects)
    
    return Rect(
        left=min_left,
        top=min_top,
        width=max_right - min_left,
        height=max_bottom - min_top,
    )


def expand_search_area(
    rect: Rect,
    screen_size: Size,
    vl_mode: Optional[str] = None,
) -> Rect:
    """
    扩展搜索区域
    
    Args:
        rect: 原始矩形
        screen_size: 屏幕尺寸
        vl_mode: VL模式
    
    Returns:
        扩展后的矩形
    """
    min_edge_size = 700 if vl_mode == "qwen3-vl" else 500
    default_padding = 160
    
    # 计算填充
    padding_h = (
        (min_edge_size - rect.width) // 2
        if rect.width < min_edge_size
        else default_padding
    )
    padding_v = (
        (min_edge_size - rect.height) // 2
        if rect.height < min_edge_size
        else default_padding
    )
    
    # 计算新尺寸
    new_width = max(min_edge_size, rect.width + padding_h * 2)
    new_height = max(min_edge_size, rect.height + padding_v * 2)
    
    # 计算新位置
    new_left = rect.left - padding_h
    new_top = rect.top - padding_v
    
    # 确保不超过屏幕边界
    if new_left + new_width > screen_size.width:
        new_left = screen_size.width - new_width
    if new_top + new_height > screen_size.height:
        new_top = screen_size.height - new_height
    
    new_left = max(0, new_left)
    new_top = max(0, new_top)
    
    if new_left + new_width > screen_size.width:
        new_width = screen_size.width - new_left
    if new_top + new_height > screen_size.height:
        new_height = screen_size.height - new_top
    
    return Rect(
        left=new_left,
        top=new_top,
        width=new_width,
        height=new_height,
    )


def build_yaml_flow_from_plans(
    plans: List[PlanningAction],
    action_space: List[Dict[str, Any]],
    sleep: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    从规划动作构建YAML流程
    
    Args:
        plans: 规划动作列表
        action_space: 动作空间
        sleep: 睡眠时间
    
    Returns:
        YAML流程项列表
    """
    flow = []
    
    for plan in plans:
        verb = plan.type
        action = next((a for a in action_space if a.get("name") == verb), None)
        
        if not action:
            continue
        
        flow_key = action.get("interface_alias") or verb
        flow_item = {flow_key: "", **(plan.param or {})}
        flow.append(flow_item)
    
    if sleep:
        flow.append({"sleep": sleep})
    
    return flow


def generate_element_by_position(
    position: Dict[str, int],
    description: str = "",
) -> Dict[str, Any]:
    """
    根据位置生成元素信息
    
    Args:
        position: 位置 {"x": int, "y": int}
        description: 描述
    
    Returns:
        元素信息
    """
    x = position.get("x", 0)
    y = position.get("y", 0)
    
    # 默认大小
    default_size = 30
    half_size = default_size // 2
    
    return {
        "center": (x, y),
        "rect": Rect(
            left=x - half_size,
            top=y - half_size,
            width=default_size,
            height=default_size,
        ),
        "description": description,
    }
