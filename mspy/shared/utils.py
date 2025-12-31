# -*- coding: utf-8 -*-
"""
Midscene Utility Functions
工具函数模块
"""

import asyncio
from typing import Any, Optional


def assert_condition(condition: Any, message: str = "Assertion failed") -> None:
    """
    断言检查，类似于TypeScript中的assert
    
    Args:
        condition: 要检查的条件
        message: 失败时的错误消息
    
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message)


async def sleep_ms(ms: int) -> None:
    """
    异步睡眠指定毫秒数
    
    Args:
        ms: 毫秒数
    """
    await asyncio.sleep(ms / 1000.0)


def sleep_ms_sync(ms: int) -> None:
    """
    同步睡眠指定毫秒数
    
    Args:
        ms: 毫秒数
    """
    import time
    time.sleep(ms / 1000.0)


def distance_of_two_points(p1: tuple, p2: tuple) -> int:
    """
    计算两点之间的距离
    
    Args:
        p1: 第一个点 (x, y)
        p2: 第二个点 (x, y)
    
    Returns:
        两点之间的距离（四舍五入到整数）
    """
    import math
    x1, y1 = p1
    x2, y2 = p2
    return round(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


def included_in_rect(point: tuple, rect: dict) -> bool:
    """
    检查点是否在矩形内
    
    Args:
        point: 点坐标 (x, y)
        rect: 矩形 {"left", "top", "width", "height"}
    
    Returns:
        是否在矩形内
    """
    x, y = point
    left = rect.get("left", 0)
    top = rect.get("top", 0)
    width = rect.get("width", 0)
    height = rect.get("height", 0)
    return left <= x <= left + width and top <= y <= top + height
