"""
图像绘制

提供在图像上绘制边框、标记等功能。
"""

import base64
import io
from pathlib import Path
from typing import Optional, Tuple, Union, List

from PIL import Image, ImageDraw, ImageFont

from mspy.shared.img.info import buffer_from_base64


def draw_box_on_image(
    base64_str: str,
    boxes: List[dict],
    color: str = "red",
    line_width: int = 2,
) -> str:
    """
    在图像上绘制边框
    
    Args:
        base64_str: Base64编码的图像
        boxes: 边框列表，每个元素为 {"left": float, "top": float, "width": float, "height": float}
        color: 边框颜色
        line_width: 边框线宽
        
    Returns:
        绘制后的Base64编码图像
    """
    buffer = buffer_from_base64(base64_str)
    
    with Image.open(io.BytesIO(buffer)) as img:
        # 转换为RGBA以支持透明度
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        draw = ImageDraw.Draw(img)
        
        for box in boxes:
            left = int(box["left"])
            top = int(box["top"])
            right = int(box["left"] + box["width"])
            bottom = int(box["top"] + box["height"])
            
            draw.rectangle(
                [left, top, right, bottom],
                outline=color,
                width=line_width,
            )
        
        # 转换回原格式输出
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        
        base64_data = base64.b64encode(output_buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{base64_data}"


def save_position_img(
    base64_str: str,
    positions: List[dict],
    save_path: Union[str, Path],
    color: str = "red",
    label_color: str = "white",
) -> None:
    """
    在图像上标记位置并保存
    
    Args:
        base64_str: Base64编码的图像
        positions: 位置列表，每个元素为 {"x": float, "y": float, "label": str}
        save_path: 保存路径
        color: 标记颜色
        label_color: 标签颜色
    """
    buffer = buffer_from_base64(base64_str)
    
    with Image.open(io.BytesIO(buffer)) as img:
        # 转换为RGBA以支持透明度
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except Exception:
            font = ImageFont.load_default()
        
        for pos in positions:
            x = int(pos["x"])
            y = int(pos["y"])
            label = pos.get("label", "")
            
            # 绘制圆点
            radius = 5
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color,
            )
            
            # 绘制标签
            if label:
                draw.text(
                    (x + radius + 2, y - 6),
                    label,
                    fill=label_color,
                    font=font,
                )
        
        # 保存
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path, format="PNG")
