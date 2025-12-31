"""
图像处理模块

提供图像信息获取、变换、绘制等功能。
"""

from mspy.shared.img.info import (
    image_info,
    image_info_of_base64,
    buffer_from_base64,
    is_valid_png_image_buffer,
)
from mspy.shared.img.transform import (
    resize_img_base64,
    save_base64_image,
    crop_by_rect,
    local_img_to_base64,
    parse_base64,
)
from mspy.shared.img.draw_box import (
    draw_box_on_image,
    save_position_img,
)

__all__ = [
    # info
    "image_info",
    "image_info_of_base64",
    "buffer_from_base64",
    "is_valid_png_image_buffer",
    # transform
    "resize_img_base64",
    "save_base64_image",
    "crop_by_rect",
    "local_img_to_base64",
    "parse_base64",
    # draw_box
    "draw_box_on_image",
    "save_position_img",
]
