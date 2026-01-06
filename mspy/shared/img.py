"""
图像处理模块
Image processing module
"""
import base64
import io
from typing import Optional, Tuple, Dict, Any

from .types import Size


def base64_to_bytes(base64_str: str) -> bytes:
    """
    Convert base64 string to bytes.
    将base64字符串转换为字节
    """
    # 移除可能的数据URL前缀
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    return base64.b64decode(base64_str)


def bytes_to_base64(data: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Convert bytes to base64 data URL.
    将字节转换为base64数据URL
    """
    b64_str = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{b64_str}"


def parse_base64(base64_str: str) -> Tuple[str, bytes]:
    """
    Parse base64 string and return mime type and data.
    解析base64字符串，返回MIME类型和数据
    """
    if base64_str.startswith("data:"):
        # 格式: data:image/png;base64,xxxxx
        parts = base64_str.split(";base64,")
        if len(parts) == 2:
            mime_type = parts[0].replace("data:", "")
            data = base64.b64decode(parts[1])
            return mime_type, data
    
    # 没有数据URL前缀，假设是JPEG
    data = base64.b64decode(base64_str)
    return "image/jpeg", data


def image_info_of_base64(base64_str: str) -> Dict[str, Any]:
    """
    Get image info from base64 string.
    从base64字符串获取图像信息
    
    Returns:
        Dict with width, height, and other info
    """
    try:
        from PIL import Image
        
        _, data = parse_base64(base64_str)
        img = Image.open(io.BytesIO(data))
        width, height = img.size
        
        return {
            "width": width,
            "height": height,
            "format": img.format,
        }
    except ImportError:
        # 如果没有PIL，返回默认值
        return {"width": 0, "height": 0, "format": "unknown"}
    except Exception:
        return {"width": 0, "height": 0, "format": "unknown"}


def resize_img_base64(
    base64_str: str,
    target_size: Dict[str, int],
) -> str:
    """
    Resize image from base64 string.
    调整base64图像大小
    
    Args:
        base64_str: Base64 encoded image
        target_size: Dict with width and height
        
    Returns:
        Resized base64 encoded image
    """
    try:
        from PIL import Image
        
        mime_type, data = parse_base64(base64_str)
        img = Image.open(io.BytesIO(data))
        
        target_width = target_size.get("width", img.width)
        target_height = target_size.get("height", img.height)
        
        # 调整大小
        resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 转换回base64
        buffer = io.BytesIO()
        img_format = "JPEG" if "jpeg" in mime_type.lower() else "PNG"
        resized_img.save(buffer, format=img_format, quality=90)
        
        return bytes_to_base64(buffer.getvalue(), mime_type)
    except ImportError:
        # 如果没有PIL，返回原图
        return base64_str
    except Exception:
        return base64_str


def create_img_base64_by_format(img_format: str, base64_str: str) -> str:
    """
    Create base64 image with proper data URL format.
    创建带有正确数据URL格式的base64图像
    """
    if base64_str.startswith("data:"):
        return base64_str
    
    mime_type = "image/jpeg" if img_format.lower() in ("jpeg", "jpg") else "image/png"
    return f"data:{mime_type};base64,{base64_str}"


def padding_to_match_block_by_base64(base64_str: str) -> Dict[str, Any]:
    """
    Padding image to match block size.
    填充图像以匹配块大小
    """
    try:
        from PIL import Image
        
        mime_type, data = parse_base64(base64_str)
        img = Image.open(io.BytesIO(data))
        width, height = img.size
        
        # 计算需要填充的大小（例如Qwen需要28的倍数）
        block_size = 28
        new_width = ((width + block_size - 1) // block_size) * block_size
        new_height = ((height + block_size - 1) // block_size) * block_size
        
        if new_width != width or new_height != height:
            new_img = Image.new(img.mode, (new_width, new_height), (255, 255, 255))
            new_img.paste(img, (0, 0))
            
            buffer = io.BytesIO()
            img_format = "JPEG" if "jpeg" in mime_type.lower() else "PNG"
            new_img.save(buffer, format=img_format, quality=90)
            
            return {
                "width": new_width,
                "height": new_height,
                "image_base64": bytes_to_base64(buffer.getvalue(), mime_type),
            }
        
        return {
            "width": width,
            "height": height,
            "image_base64": base64_str,
        }
    except ImportError:
        # 如果没有PIL，返回原图信息
        info = image_info_of_base64(base64_str)
        return {
            "width": info.get("width", 0),
            "height": info.get("height", 0),
            "image_base64": base64_str,
        }
    except Exception:
        return {
            "width": 0,
            "height": 0,
            "image_base64": base64_str,
        }


def crop_by_rect(
    base64_str: str,
    rect: Dict[str, int],
    pad_to_block: bool = False,
) -> Dict[str, Any]:
    """
    Crop image by rectangle.
    按矩形裁剪图像
    """
    try:
        from PIL import Image
        
        mime_type, data = parse_base64(base64_str)
        img = Image.open(io.BytesIO(data))
        
        left = rect.get("left", 0)
        top = rect.get("top", 0)
        width = rect.get("width", img.width - left)
        height = rect.get("height", img.height - top)
        
        cropped = img.crop((left, top, left + width, top + height))
        
        buffer = io.BytesIO()
        img_format = "JPEG" if "jpeg" in mime_type.lower() else "PNG"
        cropped.save(buffer, format=img_format, quality=90)
        
        result_base64 = bytes_to_base64(buffer.getvalue(), mime_type)
        
        if pad_to_block:
            return padding_to_match_block_by_base64(result_base64)
        
        return {
            "width": width,
            "height": height,
            "image_base64": result_base64,
        }
    except ImportError:
        return {
            "width": 0,
            "height": 0,
            "image_base64": base64_str,
        }
    except Exception:
        return {
            "width": 0,
            "height": 0,
            "image_base64": base64_str,
        }
