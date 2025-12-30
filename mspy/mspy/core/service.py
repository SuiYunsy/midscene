"""
核心服务入口。
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from mspy.core.ai_client import AIClient
from mspy.core.conversation import ConversationHistory
from mspy.core.locator import locate_element
from mspy.core.planner import plan_next_action
from mspy.shared.env import EnvConfig
from mspy.shared.logger import get_logger
from mspy.web.playwright_runner import PlaywrightRunner

logger = get_logger("mspy.service")


class MidsceneService:
    """Python 版 Midscene 服务。"""

    def __init__(self, env: EnvConfig):
        self.env = env
        self.ai_client = AIClient(env.openai_api_key, env.model_config)
        self.conversation = ConversationHistory()
        self.runner = PlaywrightRunner(headless=env.playwright_headless)

    def describe_page(self, url: str) -> str:
        """获取页面描述。"""
        with self.runner as runner:
            page = runner.open(url)
            screenshot = runner.screenshot_base64(page)
            logger.info("Requesting page description via model")
            messages = [
                {
                    "role": "system",
                    "content": "You are an assistant that concisely describes web pages.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the current page"},
                        {"type": "image_url", "image_url": {"url": screenshot, "detail": "high"}},
                    ],
                },
            ]
            return self.ai_client.chat_text(messages)

    def plan_and_run(self, url: str, instruction: str, max_steps: int = 3) -> List[Dict[str, Any]]:
        """规划并执行动作。"""
        results: List[Dict[str, Any]] = []
        with self.runner as runner:
            page = runner.open(url)
            for step in range(max_steps):
                screenshot = runner.screenshot_base64(page)
                plan = plan_next_action(
                    self.ai_client,
                    instruction,
                    screenshot,
                    self.conversation.snapshot(),
                    include_bbox=True,
                )
                results.append(plan)
                self.conversation.append("assistant", str(plan))

                action = plan.get("action")
                if not action:
                    logger.info("No action returned, stop loop.")
                    break

                log_text = plan.get("log") or "Executing action"
                logger.info("Step %s: %s", step + 1, log_text)

                runner.apply_action(page, action)

                sleep_ms = plan.get("sleep")
                if isinstance(sleep_ms, (int, float)) and sleep_ms > 0:
                    logger.info("Sleeping %sms", sleep_ms)
                    time.sleep(sleep_ms / 1000)

                if not plan.get("more_actions_needed_by_instruction"):
                    logger.info("Instruction satisfied according to planner.")
                    break
        return results

    def locate(self, url: str, target: str) -> Dict[str, Any]:
        """单独暴露定位能力。"""
        with self.runner as runner:
            page = runner.open(url)
            screenshot = runner.screenshot_base64(page)
            return locate_element(self.ai_client, target, screenshot)
