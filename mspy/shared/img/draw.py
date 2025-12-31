"""
图像绘制功能

从 packages/shared/src/img/draw-box.ts 迁移
"""

import base64
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

from mspy.shared.img.transform import create_img_base64_by_format, parse_base64
from mspy.shared.types import Rect


# 默认边框颜色
DEFAULT_BOX_COLOR = (255, 0, 0)  # 红色
DEFAULT_BOX_WIDTH = 2


def draw_box_on_image(
    input_base64: str,
    rects: List[Rect],
    color: Tuple[int, int, int] = DEFAULT_BOX_COLOR,
    width: int = DEFAULT_BOX_WIDTH,
    labels: Optional[List[str]] = None
) -> str:
    """
    在图像上绘制边框
    
    Args:
        input_base64: 输入的Base64图像
        rects: 要绘制的矩形列表
        color: 边框颜色 (R, G, B)
        width: 边框宽度
        labels: 可选的标签列表
    
    Returns:
        绘制后的Base64图像
    """
    _, body = parse_base64(input_base64)
    image_buffer = base64.b64decode(body)
    
    image = Image.open(BytesIO(image_buffer))
    
    # 转换为RGBA以支持透明
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    
    draw = ImageDraw.Draw(image)
    
    for i, rect in enumerate(rects):
        # 绘制矩形边框
        left = rect.left
        top = rect.top
        right = rect.left + rect.width
        bottom = rect.top + rect.height
        
        draw.rectangle(
            [(left, top), (right, bottom)],
            outline=color,
            width=width
        )
        
        # 绘制标签（如果提供）
        if labels and i < len(labels):
            label = labels[i]
            # 尝试使用跨平台字体
            font = None
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            ]
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, 12)
                    break
                except Exception:
                    continue
            if font is None:
                font = ImageFont.load_default()
            
            # 绘制标签背景
            text_bbox = draw.textbbox((left, top - 15), label, font=font)
            draw.rectangle(text_bbox, fill=color)
            draw.text((left, top - 15), label, fill=(255, 255, 255), font=font)
    
    # 保存
    output_buffer = BytesIO()
    image.save(output_buffer, format="PNG")
    
    return create_img_base64_by_format(output_buffer.getvalue(), "png")


def save_position_img(
    input_base64: str,
    output_path: Union[str, Path],
    rects: List[Rect],
    color: Tuple[int, int, int] = DEFAULT_BOX_COLOR,
    width: int = DEFAULT_BOX_WIDTH
) -> None:
    """
    在图像上绘制位置框并保存到文件
    
    Args:
        input_base64: 输入的Base64图像
        output_path: 输出文件路径
        rects: 要绘制的矩形列表
        color: 边框颜色
        width: 边框宽度
    """
    result_base64 = draw_box_on_image(input_base64, rects, color, width)
    
    _, body = parse_base64(result_base64)
    image_buffer = base64.b64decode(body)
    
    image = Image.open(BytesIO(image_buffer))
    image.save(output_path)
