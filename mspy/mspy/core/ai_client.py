"""
OpenAI 客户端封装，支持 JSON 输出。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from mspy.shared.env import ModelConfig
from mspy.shared.logger import get_logger

logger = get_logger("mspy.ai")


class AIClient:
    """简单的 Chat Completions 调用封装。"""

    def __init__(self, api_key: str, config: ModelConfig):
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self.config = config

    def chat_json(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用模型并解析 JSON 响应。"""
        logger.info("Calling model %s with %d message(s)", self.config.model, len(messages))
        response = self.client.responses.create(
            model=self.config.model,
            input=messages,
            response_format={"type": "json_object"},
            temperature=self.config.temperature,
        )
        content = response.output_text
        logger.debug("Raw model response: %s", content)
        return json.loads(content)

    def chat_text(self, messages: List[Dict[str, Any]]) -> str:
        logger.info("Calling model %s for text output", self.config.model)
        response = self.client.responses.create(
            model=self.config.model,
            input=messages,
            temperature=self.config.temperature,
        )
        return response.output_text
