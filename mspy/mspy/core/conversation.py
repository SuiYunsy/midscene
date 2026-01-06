"""
对话记录管理。
"""

from __future__ import annotations

from typing import Dict, List


class ConversationHistory:
    """轻量对话历史，保存最近消息。"""

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self._messages: List[Dict[str, str]] = []

    def append(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})
        # 保持长度
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

    def snapshot(self) -> List[Dict[str, str]]:
        return list(self._messages)
