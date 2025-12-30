"""
动作空间定义（精简版）。
"""

from __future__ import annotations

from typing import Dict, List

from mspy.shared.types import DeviceAction

# 仅保留最新逻辑需要的动作，不包含废弃的 aiAction 等历史字段
DEFAULT_ACTION_SPACE: List[DeviceAction] = [
    DeviceAction(
        name="Tap",
        description="Tap the element",
        param_schema={
            "locate": "bbox + natural language prompt",
        },
    ),
    DeviceAction(
        name="DoubleClick",
        description="Double click the element",
        param_schema={
            "locate": "bbox + natural language prompt",
        },
    ),
    DeviceAction(
        name="Hover",
        description="Move the pointer to the element",
        param_schema={
            "locate": "bbox + natural language prompt",
        },
    ),
    DeviceAction(
        name="Input",
        description="Input value into an element",
        param_schema={
            "value": "string",
            "mode": "replace|append|clear",
            "locate": "optional bbox + natural language prompt",
        },
    ),
    DeviceAction(
        name="Scroll",
        description="Scroll to reveal content",
        param_schema={
            "direction": "up|down",
            "amount": "pixel distance",
        },
    ),
    DeviceAction(
        name="AssertText",
        description="Assert the target text exists on screen",
        param_schema={"text": "string"},
    ),
]


def summarize_action_space() -> str:
    """将动作空间转为字符串，供提示词拼接。"""
    lines: List[str] = []
    for action in DEFAULT_ACTION_SPACE:
        param_desc = ", ".join(f"{k}: {v}" for k, v in action.param_schema.items())
        lines.append(f"- {action.name}: {action.description}\n  params: {param_desc}")
    return "\n".join(lines)
