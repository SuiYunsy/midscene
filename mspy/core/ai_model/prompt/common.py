"""公共提示词工具。"""

from __future__ import annotations

from typing import Optional


def bbox_description(vl_mode: Optional[str]) -> str:
    if vl_mode == "gemini":
        return (
            "box_2d bounding box for the target element, should be "
            "[ymin, xmin, ymax, xmax] normalized to 0-1000."
        )
    return "2d bounding box as [xmin, ymin, xmax, ymax]"
