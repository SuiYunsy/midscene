"""
图像信息处理

从 packages/shared/src/img/info.ts 迁移
"""

import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image


@dataclass
class ImageInfo:
    """图像信息"""
    width: int
    height: int
    image: Image.Image


def image_info(image: Union[str, bytes, Path, Image.Image]) -> ImageInfo:
    """
    获取图像尺寸信息
    
    Args:
        image: 图像路径、字节数据或PIL Image对象
    
    Returns:
        ImageInfo对象，包含宽度、高度和PIL Image实例
    
    Raises:
        ValueError: 如果图像数据无效
    """
    pil_image: Image.Image
    
    if isinstance(image, Image.Image):
        pil_image = image
    elif isinstance(image, (str, Path)):
        pil_image = Image.open(image)
    elif isinstance(image, bytes):
        pil_image = Image.open(BytesIO(image))
    else:
        raise ValueError("Invalid image input: must be a string path, bytes, or PIL Image")
    
    width, height = pil_image.size
    
    if not width or not height:
        raise ValueError(f"Invalid image dimensions: {width}x{height}")
    
    return ImageInfo(width=width, height=height, image=pil_image)


def image_info_of_base64(image_base64: str) -> ImageInfo:
    """
    从Base64编码的字符串获取图像尺寸信息
    
    Args:
        image_base64: Base64编码的图像数据
    
    Returns:
        ImageInfo对象
    """
    buffer = buffer_from_base64(image_base64)
    return image_info(buffer)


def buffer_from_base64(image_base64: str) -> bytes:
    """
    从Base64字符串解码为字节数据
    
    Args:
        image_base64: Base64编码的图像数据（可包含data URI前缀）
    
    Returns:
        解码后的字节数据
    """
    # 移除可能的data URI前缀
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    
    return base64.b64decode(image_base64)


def is_valid_png_buffer(buffer: bytes) -> bool:
    """
    检查字节数据是否为有效的PNG图像
    
    Args:
        buffer: 要检查的字节数据
    
    Returns:
        如果是有效的PNG图像则返回True
    """
    if not buffer or len(buffer) < 8:
        return False
    
    # PNG签名: 89 50 4E 47 0D 0A 1A 0A
    return (
        buffer[0] == 0x89 and
        buffer[1] == 0x50 and
        buffer[2] == 0x4E and
        buffer[3] == 0x47
    )
