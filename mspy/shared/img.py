"""
图像处理模块
Image processing utilities for Midscene Python SDK
"""
import base64
import io
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

try:
    from PIL import Image
except ImportError:
    Image = None


@dataclass
class ImageInfo:
    """图像信息"""
    width: int
    height: int
    format: Optional[str] = None


def image_info_of_base64(base64_str: str) -> ImageInfo:
    """
    从base64字符串获取图像信息
    
    Args:
        base64_str: base64编码的图像字符串
        
    Returns:
        ImageInfo对象，包含宽度、高度和格式
    """
    if Image is None:
        raise ImportError("Pillow is required for image processing. Install with: pip install Pillow")
    
    # 移除data URI前缀（如果有）
    if base64_str.startswith('data:'):
        base64_str = base64_str.split(',', 1)[1]
    
    # 解码base64
    image_data = base64.b64decode(base64_str)
    
    # 使用PIL读取图像
    with io.BytesIO(image_data) as bio:
        img = Image.open(bio)
        return ImageInfo(
            width=img.width,
            height=img.height,
            format=img.format
        )


def resize_img_base64(
    base64_str: str, 
    size: Dict[str, int]
) -> str:
    """
    调整base64图像的大小
    
    Args:
        base64_str: base64编码的图像字符串
        size: 目标尺寸字典 {'width': int, 'height': int}
        
    Returns:
        调整大小后的base64字符串
    """
    if Image is None:
        raise ImportError("Pillow is required for image processing. Install with: pip install Pillow")
    
    # 确定图像格式和获取纯base64数据
    original_format = "JPEG"
    prefix = ""
    
    if base64_str.startswith('data:'):
        # 解析data URI
        parts = base64_str.split(',', 1)
        prefix_part = parts[0]
        base64_data = parts[1]
        
        # 提取格式
        if 'png' in prefix_part.lower():
            original_format = "PNG"
            prefix = "data:image/png;base64,"
        elif 'jpeg' in prefix_part.lower() or 'jpg' in prefix_part.lower():
            original_format = "JPEG"
            prefix = "data:image/jpeg;base64,"
        else:
            prefix = prefix_part + ","
    else:
        base64_data = base64_str
        prefix = "data:image/jpeg;base64,"
    
    # 解码base64
    image_data = base64.b64decode(base64_data)
    
    # 使用PIL调整大小
    with io.BytesIO(image_data) as bio:
        img = Image.open(bio)
        
        # 调整大小
        target_width = size.get('width', img.width)
        target_height = size.get('height', img.height)
        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 编码回base64
        output_buffer = io.BytesIO()
        
        # 如果是PNG格式，保持PNG格式
        if original_format == "PNG":
            resized_img.save(output_buffer, format="PNG")
        else:
            # 如果有alpha通道，转换为RGB
            if resized_img.mode in ('RGBA', 'LA', 'P'):
                resized_img = resized_img.convert('RGB')
            resized_img.save(output_buffer, format="JPEG", quality=90)
        
        output_buffer.seek(0)
        result_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        return prefix + result_base64


def create_img_base64_by_format(img_type: str, data: str) -> str:
    """
    根据格式创建带前缀的base64图像字符串
    
    Args:
        img_type: 图像类型 ('jpeg', 'png', 等)
        data: base64数据
        
    Returns:
        带data URI前缀的base64字符串
    """
    if data.startswith('data:'):
        return data
    return f"data:image/{img_type};base64,{data}"


def crop_by_rect(
    base64_str: str, 
    rect: Dict[str, int],
    add_padding: bool = False
) -> Dict[str, Any]:
    """
    按矩形裁剪图像
    
    Args:
        base64_str: base64编码的图像
        rect: 裁剪区域 {'left': int, 'top': int, 'width': int, 'height': int}
        add_padding: 是否添加填充
        
    Returns:
        包含裁剪后图像和尺寸的字典
    """
    if Image is None:
        raise ImportError("Pillow is required for image processing. Install with: pip install Pillow")
    
    # 确定格式
    prefix = "data:image/jpeg;base64,"
    if base64_str.startswith('data:'):
        parts = base64_str.split(',', 1)
        prefix = parts[0] + ","
        base64_data = parts[1]
    else:
        base64_data = base64_str
    
    # 解码
    image_data = base64.b64decode(base64_data)
    
    with io.BytesIO(image_data) as bio:
        img = Image.open(bio)
        
        # 计算裁剪区域
        left = max(0, rect.get('left', 0))
        top = max(0, rect.get('top', 0))
        right = min(img.width, left + rect.get('width', img.width))
        bottom = min(img.height, top + rect.get('height', img.height))
        
        # 裁剪
        cropped = img.crop((left, top, right, bottom))
        
        # 编码回base64
        output_buffer = io.BytesIO()
        
        # 保持原格式或使用JPEG
        if img.format and img.format.upper() == 'PNG':
            cropped.save(output_buffer, format="PNG")
        else:
            if cropped.mode in ('RGBA', 'LA', 'P'):
                cropped = cropped.convert('RGB')
            cropped.save(output_buffer, format="JPEG", quality=90)
        
        output_buffer.seek(0)
        result_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        return {
            'imageBase64': prefix + result_base64,
            'width': cropped.width,
            'height': cropped.height
        }


def composite_element_info_img(
    input_img_base64: str,
    size: Dict[str, int],
    elements_position_info: list,
    border_thickness: int = 2
) -> str:
    """
    在图像上绘制元素边框
    
    Args:
        input_img_base64: 输入图像的base64字符串
        size: 图像尺寸
        elements_position_info: 元素位置信息列表
        border_thickness: 边框厚度
        
    Returns:
        处理后的base64图像字符串
    """
    if Image is None:
        raise ImportError("Pillow is required for image processing. Install with: pip install Pillow")
    
    try:
        from PIL import ImageDraw
    except ImportError:
        raise ImportError("Pillow is required for image processing. Install with: pip install Pillow")
    
    # 解析base64
    prefix = "data:image/jpeg;base64,"
    if input_img_base64.startswith('data:'):
        parts = input_img_base64.split(',', 1)
        prefix = parts[0] + ","
        base64_data = parts[1]
    else:
        base64_data = input_img_base64
    
    # 解码
    image_data = base64.b64decode(base64_data)
    
    with io.BytesIO(image_data) as bio:
        img = Image.open(bio)
        
        # 转换为RGB如果需要
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # 绘制边框
        for element_info in elements_position_info:
            rect = element_info.get('rect', {})
            left = rect.get('left', 0)
            top = rect.get('top', 0)
            width = rect.get('width', 0)
            height = rect.get('height', 0)
            
            # 绘制红色边框
            for i in range(border_thickness):
                draw.rectangle(
                    [left + i, top + i, left + width - i, top + height - i],
                    outline=(255, 0, 0)
                )
        
        # 编码回base64
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG", quality=90)
        output_buffer.seek(0)
        result_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        return prefix + result_base64
