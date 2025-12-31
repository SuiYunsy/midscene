# -*- coding: utf-8 -*-
"""
Midscene Image Processing Module
图像处理模块
"""

import base64
import io
from typing import Tuple, Optional, Dict, Any
from PIL import Image


def image_info_of_base64(base64_str: str) -> Dict[str, int]:
    """
    获取base64图像的信息
    
    Args:
        base64_str: base64编码的图像字符串
    
    Returns:
        包含width和height的字典
    """
    # 移除可能存在的data URL前缀
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    return {
        "width": image.width,
        "height": image.height,
    }


def resize_img_base64(
    base64_str: str,
    size: Dict[str, int],
) -> str:
    """
    调整base64图像大小
    
    Args:
        base64_str: base64编码的图像字符串
        size: 目标尺寸 {"width": int, "height": int}
    
    Returns:
        调整后的base64编码图像字符串
    """
    # 移除可能存在的data URL前缀
    prefix = ""
    if "," in base64_str:
        parts = base64_str.split(",")
        prefix = parts[0] + ","
        base64_str = parts[1]
    
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    
    # 调整大小
    resized = image.resize((size["width"], size["height"]), Image.Resampling.LANCZOS)
    
    # 转换回base64
    buffer = io.BytesIO()
    img_format = image.format or "JPEG"
    resized.save(buffer, format=img_format, quality=90)
    result_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # 添加回前缀
    if prefix:
        return prefix + result_base64
    return result_base64


def create_img_base64_by_format(img_format: str, base64_content: str) -> str:
    """
    创建带格式的base64图像URL
    
    Args:
        img_format: 图像格式 (jpeg, png, etc.)
        base64_content: base64编码的图像内容
    
    Returns:
        完整的data URL
    """
    mime_type = f"image/{img_format}"
    return f"data:{mime_type};base64,{base64_content}"


def parse_base64(base64_str: str) -> Tuple[str, str]:
    """
    解析base64字符串，分离MIME类型和数据
    
    Args:
        base64_str: base64编码的字符串
    
    Returns:
        (mime_type, data) 元组
    """
    if "," in base64_str:
        header, data = base64_str.split(",", 1)
        # 从 "data:image/jpeg;base64" 提取 MIME 类型
        if ":" in header and ";" in header:
            mime_type = header.split(":")[1].split(";")[0]
            return mime_type, data
        return "image/jpeg", data
    return "image/jpeg", base64_str


def crop_by_rect(
    base64_str: str,
    rect: Dict[str, int],
) -> Dict[str, Any]:
    """
    按矩形裁剪图像
    
    Args:
        base64_str: base64编码的图像字符串
        rect: 裁剪区域 {"left", "top", "width", "height"}
    
    Returns:
        包含裁剪后图像的字典
    """
    # 移除可能存在的data URL前缀
    prefix = ""
    if "," in base64_str:
        parts = base64_str.split(",")
        prefix = parts[0] + ","
        base64_str = parts[1]
    
    image_data = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_data))
    
    left = rect.get("left", 0)
    top = rect.get("top", 0)
    width = rect.get("width", image.width)
    height = rect.get("height", image.height)
    
    # 裁剪
    cropped = image.crop((left, top, left + width, top + height))
    
    # 转换回base64
    buffer = io.BytesIO()
    img_format = image.format or "JPEG"
    cropped.save(buffer, format=img_format, quality=90)
    result_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    if prefix:
        result_base64 = prefix + result_base64
    
    return {
        "imageBase64": result_base64,
        "width": cropped.width,
        "height": cropped.height,
    }
