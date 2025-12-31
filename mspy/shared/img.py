"""基础图片处理：尺寸获取、缩放、裁剪与标注。"""

from __future__ import annotations

import io
import base64
from dataclasses import dataclass
from typing import Iterable, List, Tuple

from PIL import Image, ImageDraw

from .logger import get_logger
from .utils import bytes_to_data_url

logger = get_logger("img")
DEFAULT_NORMALIZE_SIZE = 1000  # 模型常用的归一化尺寸


@dataclass
class ImgSize:
    width: int
    height: int


def _load_image_from_base64(data_url: str) -> Image.Image:
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    raw = base64.b64decode(data_url)
    return Image.open(io.BytesIO(raw)).convert("RGB")


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return bytes_to_data_url(buf.getvalue())


def image_info_of_base64(data_url: str) -> ImgSize:
    """获取图片尺寸。"""
    img = _load_image_from_base64(data_url)
    width, height = img.size
    return ImgSize(width=width, height=height)


def resize_img_base64(data_url: str, size: ImgSize) -> str:
    """缩放图片到指定尺寸。"""
    img = _load_image_from_base64(data_url)
    resized = img.resize((int(size.width), int(size.height)))
    logger.info("Resized image to %sx%s", size.width, size.height)
    return _image_to_base64(resized)


def crop_by_rect(
    data_url: str, rect: Tuple[int, int, int, int], normalize_1000: bool = False
) -> str:
    """按矩形裁剪，rect 为 (x1, y1, x2, y2)。"""
    img = _load_image_from_base64(data_url)
    x1, y1, x2, y2 = rect
    cropped = img.crop((x1, y1, x2, y2))
    if normalize_1000:
        cropped = cropped.resize((DEFAULT_NORMALIZE_SIZE, DEFAULT_NORMALIZE_SIZE))
    logger.info("Cropped image with rect=%s", rect)
    return _image_to_base64(cropped)


def composite_element_info_img(
    input_img_base64: str,
    elements: Iterable[Tuple[int, int, int, int]],
    color: str = "red",
    thickness: int = 3,
) -> str:
    """在图片上标注多个矩形并返回新的 base64。"""
    img = _load_image_from_base64(input_img_base64)
    draw = ImageDraw.Draw(img)
    rects: List[Tuple[int, int, int, int]] = list(elements)
    for rect in rects:
        x1, y1, x2, y2 = rect
        for offset in range(thickness):
            draw.rectangle(
                (x1 - offset, y1 - offset, x2 + offset, y2 + offset),
                outline=color,
                width=1,
            )
    logger.info("Composite %s boxes on image", len(rects))
    return _image_to_base64(img)
