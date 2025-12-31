"""
图像处理模块
"""

import base64
import io
from typing import Optional, Tuple
from PIL import Image, ImageDraw

from .logger import get_debug

debug = get_debug('img')


def parse_base64(full_base64_string: str) -> Tuple[str, str]:
    """
    解析base64字符串，提取MIME类型和内容
    
    Args:
        full_base64_string: 完整的base64字符串 (data:image/xxx;base64,...)
    
    Returns:
        (mime_type, body) 元组
    """
    try:
        separator = ';base64,'
        index = full_base64_string.find(separator)
        if index == -1:
            raise ValueError('Invalid base64 string: missing separator')
        
        # 5 means 'data:'
        mime_type = full_base64_string[5:index]
        body = full_base64_string[index + len(separator):]
        return mime_type, body
    except Exception as e:
        raise ValueError(
            f"parseBase64 fail because input is not a valid base64 string: "
            f"{full_base64_string[:50]}..."
        ) from e


def create_img_base64_by_format(format_type: str, body: str) -> str:
    """
    根据格式创建base64图像字符串
    
    Args:
        format_type: 图像格式 (jpeg, png等)
        body: base64内容
    
    Returns:
        完整的base64字符串
    """
    return f"data:image/{format_type};base64,{body}"


def base64_to_pil_image(base64_string: str) -> Image.Image:
    """
    将base64字符串转换为PIL Image
    
    Args:
        base64_string: base64图像字符串
    
    Returns:
        PIL Image对象
    """
    _, body = parse_base64(base64_string)
    image_data = base64.b64decode(body)
    return Image.open(io.BytesIO(image_data))


def pil_image_to_base64(image: Image.Image, format_type: str = "jpeg", quality: int = 90) -> str:
    """
    将PIL Image转换为base64字符串
    
    Args:
        image: PIL Image对象
        format_type: 输出格式
        quality: 质量 (用于JPEG)
    
    Returns:
        base64字符串
    """
    buffer = io.BytesIO()
    
    if format_type.lower() in ['jpg', 'jpeg']:
        # 确保图像是RGB模式（JPEG不支持RGBA）
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(buffer, format='JPEG', quality=quality)
    else:
        image.save(buffer, format=format_type.upper())
    
    body = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return create_img_base64_by_format(format_type, body)


def get_image_info(base64_string: str) -> Tuple[int, int]:
    """
    获取base64图像的尺寸信息
    
    Args:
        base64_string: base64图像字符串
    
    Returns:
        (width, height) 元组
    """
    image = base64_to_pil_image(base64_string)
    return image.size


async def image_info_of_base64(base64_string: str) -> dict:
    """
    异步获取base64图像信息
    
    Args:
        base64_string: base64图像字符串
    
    Returns:
        包含width, height的字典
    """
    width, height = get_image_info(base64_string)
    return {'width': width, 'height': height}


def resize_image(
    base64_string: str, 
    new_width: int, 
    new_height: int
) -> str:
    """
    调整图像大小
    
    Args:
        base64_string: 原始base64图像
        new_width: 新宽度
        new_height: 新高度
    
    Returns:
        调整后的base64图像
    """
    debug(f"resizeImg start, target size: {new_width}x{new_height}")
    
    image = base64_to_pil_image(base64_string)
    original_width, original_height = image.size
    
    # 如果尺寸相同，直接返回
    if new_width == original_width and new_height == original_height:
        return base64_string
    
    # 调整大小
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    result = pil_image_to_base64(resized, 'jpeg', 90)
    debug(f"resizeImg done, target size: {new_width}x{new_height}")
    
    return result


async def resize_img_base64(
    base64_string: str, 
    new_size: dict
) -> str:
    """
    异步调整图像大小
    
    Args:
        base64_string: 原始base64图像
        new_size: {'width': int, 'height': int}
    
    Returns:
        调整后的base64图像
    """
    return resize_image(base64_string, new_size['width'], new_size['height'])


def padding_to_match_block(
    base64_string: str, 
    block_size: int = 28
) -> Tuple[int, int, str]:
    """
    对图像进行填充以匹配块大小（用于qwen模型）
    
    Args:
        base64_string: base64图像字符串
        block_size: 块大小
    
    Returns:
        (new_width, new_height, new_base64_string) 元组
    """
    image = base64_to_pil_image(base64_string)
    width, height = image.size
    
    target_width = ((width + block_size - 1) // block_size) * block_size
    target_height = ((height + block_size - 1) // block_size) * block_size
    
    if target_width == width and target_height == height:
        return width, height, base64_string
    
    # 创建白色背景的新图像
    padded = Image.new('RGB', (target_width, target_height), (255, 255, 255))
    padded.paste(image, (0, 0))
    
    result = pil_image_to_base64(padded, 'jpeg', 90)
    return target_width, target_height, result


async def padding_to_match_block_by_base64(
    base64_string: str,
    block_size: int = 28
) -> dict:
    """
    异步对图像进行填充以匹配块大小
    
    Args:
        base64_string: base64图像字符串
        block_size: 块大小
    
    Returns:
        {'width': int, 'height': int, 'imageBase64': str}
    """
    width, height, image_base64 = padding_to_match_block(base64_string, block_size)
    return {
        'width': width,
        'height': height,
        'imageBase64': image_base64
    }


def crop_by_rect(
    base64_string: str,
    left: int,
    top: int,
    width: int,
    height: int,
    padding_image: bool = False
) -> Tuple[int, int, str]:
    """
    按矩形裁剪图像
    
    Args:
        base64_string: base64图像字符串
        left: 左边界
        top: 上边界
        width: 宽度
        height: 高度
        padding_image: 是否填充
    
    Returns:
        (new_width, new_height, new_base64_string) 元组
    """
    image = base64_to_pil_image(base64_string)
    
    # 裁剪
    cropped = image.crop((left, top, left + width, top + height))
    
    if padding_image:
        return padding_to_match_block(pil_image_to_base64(cropped))
    
    result = pil_image_to_base64(cropped, 'jpeg', 90)
    return cropped.size[0], cropped.size[1], result


def composite_element_info_img(
    input_img_base64: str,
    size: dict,
    elements_position_info: list,
    border_thickness: int = 2
) -> str:
    """
    在图像上绘制元素边框
    
    Args:
        input_img_base64: 输入图像的base64字符串
        size: 尺寸信息
        elements_position_info: 元素位置信息列表
        border_thickness: 边框粗细
    
    Returns:
        处理后的base64图像
    """
    image = base64_to_pil_image(input_img_base64)
    draw = ImageDraw.Draw(image)
    
    for element in elements_position_info:
        rect = element.get('rect')
        if rect:
            left = rect.get('left', 0)
            top = rect.get('top', 0)
            width = rect.get('width', 0)
            height = rect.get('height', 0)
            
            # 绘制矩形边框
            draw.rectangle(
                [(left, top), (left + width, top + height)],
                outline='red',
                width=border_thickness
            )
    
    return pil_image_to_base64(image, 'jpeg', 90)
