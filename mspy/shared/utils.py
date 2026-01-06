"""
工具函数模块
Utility functions for Midscene Python SDK
"""
import uuid as uuid_lib
import time
import asyncio
from typing import Any, Optional


def uuid() -> str:
    """生成UUID"""
    return str(uuid_lib.uuid4())


async def sleep(ms: int):
    """
    异步等待指定毫秒数
    
    Args:
        ms: 毫秒数
    """
    await asyncio.sleep(ms / 1000.0)


def assert_value(condition: Any, message: str = "Assertion failed"):
    """
    断言条件为真
    
    Args:
        condition: 要断言的条件
        message: 失败时的错误消息
        
    Raises:
        AssertionError: 当条件为假时
    """
    if not condition:
        raise AssertionError(message)


def current_timestamp_ms() -> int:
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)


def escape_script_tag(content: str) -> str:
    """转义script标签"""
    return content.replace("</script>", "<\\/script>")


def distance_of_two_points(p1: tuple, p2: tuple) -> int:
    """
    计算两点之间的距离
    
    Args:
        p1: 第一个点 (x, y)
        p2: 第二个点 (x, y)
        
    Returns:
        两点之间的距离（四舍五入到整数）
    """
    x1, y1 = p1
    x2, y2 = p2
    return round(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5)


def included_in_rect(point: tuple, rect: dict) -> bool:
    """
    检查点是否在矩形内
    
    Args:
        point: 点坐标 (x, y)
        rect: 矩形 {'left': int, 'top': int, 'width': int, 'height': int}
        
    Returns:
        点是否在矩形内
    """
    x, y = point
    left = rect.get('left', 0)
    top = rect.get('top', 0)
    width = rect.get('width', 0)
    height = rect.get('height', 0)
    
    return left <= x <= left + width and top <= y <= top + height


def overlapped(container: dict, target: dict) -> bool:
    """
    检查两个矩形是否有重叠
    
    Args:
        container: 容器矩形
        target: 目标矩形
        
    Returns:
        是否重叠
    """
    return (
        container.get('left', 0) < target.get('left', 0) + target.get('width', 0) and
        container.get('left', 0) + container.get('width', 0) > target.get('left', 0) and
        container.get('top', 0) < target.get('top', 0) + target.get('height', 0) and
        container.get('top', 0) + container.get('height', 0) > target.get('top', 0)
    )


def log_msg(message: str):
    """打印日志消息"""
    print(f"[Midscene] {message}")
