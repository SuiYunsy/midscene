"""
元素定位逻辑。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from mspy.core.prompts import system_prompt_to_locate_element
from mspy.shared.logger import get_logger

logger = get_logger("mspy.locator")


def locate_element(ai_client, target: str, screenshot_base64: str) -> Dict[str, Any]:
    """调用大模型定位元素。"""
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt_to_locate_element()},
        {
          "role": "user",
          "content": [
            {"type": "text", "text": f"Find: {target}"},
            {"type": "image_url", "image_url": {"url": screenshot_base64, "detail": "high"}},
          ],
        },
    ]
    logger.info("Locating element for target: %s", target)
    result = ai_client.chat_json(messages)
    logger.debug("Locator result: %s", json.dumps(result, ensure_ascii=False))
    return result
