"""Image processing utilities."""

import base64
import io
from typing import Dict, Optional, Tuple

from PIL import Image


def load_image_from_base64(base64_str: str) -> Image.Image:
    """
    Load an image from a base64 string.
    
    Args:
        base64_str: Base64 encoded image data
        
    Returns:
        PIL Image object
    """
    # Remove data URL prefix if present
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    
    image_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_data))


def save_image_to_base64(
    image: Image.Image, 
    format: str = "PNG"
) -> str:
    """
    Save an image to a base64 string.
    
    Args:
        image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
        
    Returns:
        Base64 encoded string
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


async def image_info_of_base64(base64_str: str) -> Dict[str, int]:
    """
    Get image dimensions from base64 string.
    
    Args:
        base64_str: Base64 encoded image
        
    Returns:
        Dict with width and height
    """
    image = load_image_from_base64(base64_str)
    return {
        "width": image.width,
        "height": image.height,
    }


async def resize_image_base64(
    base64_str: str,
    size: Dict[str, int],
    format: str = "PNG"
) -> str:
    """
    Resize an image from base64 string.
    
    Args:
        base64_str: Base64 encoded image
        size: Dict with width and height
        format: Output format
        
    Returns:
        Base64 encoded resized image
    """
    image = load_image_from_base64(base64_str)
    
    width = size.get("width", image.width)
    height = size.get("height", image.height)
    
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    return save_image_to_base64(resized, format)
