"""
动作规划逻辑。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mspy.core.prompts import system_prompt_to_task_planning
from mspy.shared.logger import get_logger

logger = get_logger("mspy.planner")


def build_planning_messages(
    instruction: str,
    screenshot_base64: Optional[str],
    history: List[Dict[str, str]],
    include_bbox: bool,
) -> List[Dict[str, Any]]:
    """构造聊天消息。"""
    system_prompt = system_prompt_to_task_planning(include_bbox)
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.append({"role": "user", "content": f"<user_instruction>{instruction}</user_instruction>"})
    if screenshot_base64:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "this is the latest screenshot"},
                    {"type": "image_url", "image_url": {"url": screenshot_base64, "detail": "high"}},
                ],
            }
        )
    messages.extend(history)
    return messages


def plan_next_action(
    ai_client,
    instruction: str,
    screenshot_base64: Optional[str],
    history: List[Dict[str, str]],
    include_bbox: bool = True,
) -> Dict[str, Any]:
    """调用大模型进行动作规划。"""
    logger.info("Planning next action...")
    messages = build_planning_messages(instruction, screenshot_base64, history, include_bbox)
    result = ai_client.chat_json(messages)

    # 记录完整内容便于调试
    logger.debug("Planning result: %s", json.dumps(result, ensure_ascii=False))
    return result
