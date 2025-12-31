"""对话历史记录，保持行为与 TS 版本一致。"""

from __future__ import annotations

from typing import List, Optional


class ConversationHistory:
    def __init__(self, initial_messages: Optional[List[dict]] = None) -> None:
        self.messages: List[dict] = []
        if initial_messages:
            self.seed(initial_messages)
        self.pending_feedback_message = ""

    def reset_pending_feedback_message_if_exists(self) -> None:
        if self.pending_feedback_message:
            self.pending_feedback_message = ""

    def append(self, message: dict) -> None:
        self.messages.append(message)

    def seed(self, messages: List[dict]) -> None:
        self.reset()
        for msg in messages:
            self.append(msg)

    def reset(self) -> None:
        self.messages.clear()

    def snapshot(self, max_images: Optional[int] = None) -> List[dict]:
        if max_images is None:
            return list(self.messages)

        cloned = [msg.copy() for msg in self.messages]
        image_count = 0
        for message in reversed(cloned):
            content = message.get("content")
            if isinstance(content, list):
                for idx, item in enumerate(content):
                    if item.get("type") == "image_url":
                        image_count += 1
                        if image_count > max_images:
                            content[idx] = {
                                "type": "text",
                                "text": "(image ignored due to size optimization)",
                            }
        return cloned

    def __len__(self) -> int:
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)

    def to_json(self) -> List[dict]:
        return self.snapshot()
