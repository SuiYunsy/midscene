"""
图像信息获取

提供图像尺寸、格式等信息的获取功能。
"""

import base64
import io
from typing import Optional, Tuple

from PIL import Image


class ImageInfo:
    """图像信息"""
    def __init__(self, width: int, height: int, format: Optional[str] = None):
        self.width = width
        self.height = height
        self.format = format


def buffer_from_base64(base64_str: str) -> bytes:
    """
    从Base64字符串解码为字节数据
    
    Args:
        base64_str: Base64编码的字符串（可包含data URI前缀）
        
    Returns:
        解码后的字节数据
    """
    # 移除data URI前缀（如果存在）
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    
    return base64.b64decode(base64_str)


def image_info(image_buffer: bytes) -> ImageInfo:
    """
    获取图像信息
    
    Args:
        image_buffer: 图像字节数据
        
    Returns:
        图像信息对象
    """
    with Image.open(io.BytesIO(image_buffer)) as img:
        return ImageInfo(
            width=img.width,
            height=img.height,
            format=img.format,
        )


async def image_info_of_base64(base64_str: str) -> ImageInfo:
    """
    从Base64字符串获取图像信息
    
    Args:
        base64_str: Base64编码的图像字符串
        
    Returns:
        图像信息对象
    """
    buffer = buffer_from_base64(base64_str)
    return image_info(buffer)


def is_valid_png_image_buffer(buffer: bytes) -> bool:
    """
    检查是否为有效的PNG图像
    
    Args:
        buffer: 图像字节数据
        
    Returns:
        是否为有效的PNG图像
    """
    # PNG文件头
    PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
    
    if len(buffer) < len(PNG_SIGNATURE):
        return False
    
    return buffer[:len(PNG_SIGNATURE)] == PNG_SIGNATURE
