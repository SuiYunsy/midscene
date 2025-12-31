"""
图像变换处理

从 packages/shared/src/img/transform.ts 迁移
"""

import base64
import re
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image

from mspy.shared.logger import get_debug
from mspy.shared.types import Rect


_debug = get_debug("img")


def parse_base64(base64_data: str) -> Tuple[str, str]:
    """
    解析Base64数据，提取格式和内容
    
    Args:
        base64_data: Base64编码的图像数据
    
    Returns:
        (format, body) 元组，format如 'png', 'jpeg'，body为纯Base64内容
    """
    # 匹配 data:image/xxx;base64,xxx 格式
    match = re.match(r"^data:image/(\w+);base64,(.+)$", base64_data)
    if match:
        return match.group(1), match.group(2)
    
    # 没有前缀，假设是PNG
    return "png", base64_data


def create_img_base64_by_format(buffer: bytes, format: str = "png") -> str:
    """
    将字节数据转换为带格式前缀的Base64字符串
    
    Args:
        buffer: 图像字节数据
        format: 图像格式（png, jpeg等）
    
    Returns:
        带data URI前缀的Base64字符串
    """
    b64_body = base64.b64encode(buffer).decode("utf-8")
    mime_type = f"image/{format}"
    if format == "jpg":
        mime_type = "image/jpeg"
    return f"data:{mime_type};base64,{b64_body}"


async def save_base64_image(base64_data: str, output_path: Union[str, Path]) -> None:
    """
    将Base64编码的图像保存到文件
    
    Args:
        base64_data: Base64编码的图像数据
        output_path: 输出文件路径
    """
    _, body = parse_base64(base64_data)
    image_buffer = base64.b64decode(body)
    
    image = Image.open(BytesIO(image_buffer))
    image.save(output_path)


async def resize_img_base64(
    input_base64: str,
    new_size: dict,
    quality: int = 90
) -> str:
    """
    调整Base64图像的尺寸
    
    Args:
        input_base64: 输入的Base64图像
        new_size: 新尺寸 {"width": int, "height": int}
        quality: JPEG质量（1-100）
    
    Returns:
        调整后的Base64图像
    """
    width = new_size.get("width", 0)
    height = new_size.get("height", 0)
    
    if width <= 0 or height <= 0:
        raise ValueError("newSize must have positive width and height")
    
    _, body = parse_base64(input_base64)
    image_buffer = base64.b64decode(body)
    
    image = Image.open(BytesIO(image_buffer))
    original_width, original_height = image.size
    
    # 如果尺寸相同，直接返回
    if width == original_width and height == original_height:
        return input_base64
    
    _debug(f"resize_img start, target size: {width}x{height}")
    
    # 调整尺寸
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    
    # 转换为JPEG以压缩
    output_buffer = BytesIO()
    if resized.mode == "RGBA":
        # 如果有透明通道，转为RGB（JPEG不支持透明）
        rgb_image = Image.new("RGB", resized.size, (255, 255, 255))
        rgb_image.paste(resized, mask=resized.split()[3] if len(resized.split()) == 4 else None)
        rgb_image.save(output_buffer, format="JPEG", quality=quality)
    else:
        resized.save(output_buffer, format="JPEG", quality=quality)
    
    _debug(f"resize_img done, target size: {width}x{height}")
    
    return create_img_base64_by_format(output_buffer.getvalue(), "jpeg")


async def crop_by_rect(
    input_base64: str,
    rect: Rect,
    use_padding: bool = False
) -> dict:
    """
    根据矩形区域裁剪图像
    
    Args:
        input_base64: 输入的Base64图像
        rect: 裁剪区域
        use_padding: 是否使用填充（当rect超出图像边界时）
    
    Returns:
        {"imageBase64": str, "rect": Rect}
    """
    _, body = parse_base64(input_base64)
    image_buffer = base64.b64decode(body)
    
    image = Image.open(BytesIO(image_buffer))
    img_width, img_height = image.size
    
    # 计算裁剪区域
    left = max(0, rect.left)
    top = max(0, rect.top)
    right = min(img_width, rect.left + rect.width)
    bottom = min(img_height, rect.top + rect.height)
    
    # 裁剪
    cropped = image.crop((left, top, right, bottom))
    
    # 保存
    output_buffer = BytesIO()
    cropped.save(output_buffer, format="PNG")
    
    result_base64 = create_img_base64_by_format(output_buffer.getvalue(), "png")
    
    return {
        "imageBase64": result_base64,
        "rect": Rect(
            left=left,
            top=top,
            width=right - left,
            height=bottom - top
        )
    }


def local_img_to_base64(file_path: Union[str, Path]) -> str:
    """
    将本地图像文件转换为Base64
    
    Args:
        file_path: 图像文件路径
    
    Returns:
        Base64编码的图像
    """
    path = Path(file_path)
    
    with open(path, "rb") as f:
        image_data = f.read()
    
    # 检测格式
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        format = "jpeg"
    elif suffix == ".png":
        format = "png"
    elif suffix == ".gif":
        format = "gif"
    elif suffix == ".webp":
        format = "webp"
    else:
        format = "png"  # 默认
    
    return create_img_base64_by_format(image_data, format)
