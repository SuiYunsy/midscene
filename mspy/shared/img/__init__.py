"""
图像处理模块

从 packages/shared/src/img/ 迁移
使用Pillow替代Jimp/Sharp
"""

from mspy.shared.img.info import (
    image_info,
    image_info_of_base64,
    buffer_from_base64,
    is_valid_png_buffer,
    ImageInfo,
)
from mspy.shared.img.transform import (
    save_base64_image,
    resize_img_base64,
    crop_by_rect,
    local_img_to_base64,
    parse_base64,
    create_img_base64_by_format,
)
from mspy.shared.img.draw import (
    draw_box_on_image,
    save_position_img,
)

__all__ = [
    # info
    "image_info",
    "image_info_of_base64",
    "buffer_from_base64",
    "is_valid_png_buffer",
    "ImageInfo",
    # transform
    "save_base64_image",
    "resize_img_base64",
    "crop_by_rect",
    "local_img_to_base64",
    "parse_base64",
    "create_img_base64_by_format",
    # draw
    "draw_box_on_image",
    "save_position_img",
]
