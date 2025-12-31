"""
图像变换

提供图像缩放、裁剪、格式转换等功能。
"""

import base64
import io
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image

from mspy.shared.img.info import buffer_from_base64


def parse_base64(base64_str: str) -> Tuple[str, str]:
    """
    解析Base64字符串，分离MIME类型和数据
    
    Args:
        base64_str: Base64编码的字符串
        
    Returns:
        (mime_type, data)元组
    """
    if base64_str.startswith("data:"):
        # 格式：data:image/png;base64,xxxxx
        prefix, data = base64_str.split(",", 1)
        mime_type = prefix.split(":")[1].split(";")[0]
        return mime_type, data
    else:
        # 假设是PNG
        return "image/png", base64_str


def _image_to_base64(img: Image.Image, format: str = "PNG") -> str:
    """
    将PIL图像转换为Base64字符串
    
    Args:
        img: PIL图像
        format: 输出格式
        
    Returns:
        Base64编码的字符串
    """
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    
    base64_data = base64.b64encode(buffer.read()).decode("utf-8")
    mime_type = f"image/{format.lower()}"
    
    return f"data:{mime_type};base64,{base64_data}"


async def resize_img_base64(
    base64_str: str,
    size: dict[str, int],
) -> str:
    """
    缩放Base64编码的图像
    
    Args:
        base64_str: Base64编码的图像
        size: 目标尺寸 {"width": int, "height": int}
        
    Returns:
        缩放后的Base64编码图像
    """
    buffer = buffer_from_base64(base64_str)
    
    with Image.open(io.BytesIO(buffer)) as img:
        resized = img.resize((size["width"], size["height"]), Image.Resampling.LANCZOS)
        return _image_to_base64(resized, img.format or "PNG")


def save_base64_image(base64_str: str, path: Union[str, Path]) -> None:
    """
    保存Base64编码的图像到文件
    
    Args:
        base64_str: Base64编码的图像
        path: 保存路径
    """
    buffer = buffer_from_base64(base64_str)
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "wb") as f:
        f.write(buffer)


def crop_by_rect(
    base64_str: str,
    rect: dict[str, float],
) -> str:
    """
    按矩形区域裁剪图像
    
    Args:
        base64_str: Base64编码的图像
        rect: 裁剪区域 {"left": float, "top": float, "width": float, "height": float}
        
    Returns:
        裁剪后的Base64编码图像
    """
    buffer = buffer_from_base64(base64_str)
    
    with Image.open(io.BytesIO(buffer)) as img:
        left = int(rect["left"])
        top = int(rect["top"])
        right = int(rect["left"] + rect["width"])
        bottom = int(rect["top"] + rect["height"])
        
        cropped = img.crop((left, top, right, bottom))
        return _image_to_base64(cropped, img.format or "PNG")


def local_img_to_base64(path: Union[str, Path]) -> str:
    """
    将本地图像文件转换为Base64编码
    
    Args:
        path: 图像文件路径
        
    Returns:
        Base64编码的图像
    """
    path = Path(path)
    
    with Image.open(path) as img:
        return _image_to_base64(img, img.format or "PNG")
