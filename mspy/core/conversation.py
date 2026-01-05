"""对话历史管理"""
from typing import List, Dict, Any, Optional
from copy import deepcopy
from ..shared.constants import DEFAULT_MAX_IMAGES_IN_HISTORY

class ConversationHistory:
    """对话历史管理器"""
    def __init__(self, max_images: int = DEFAULT_MAX_IMAGES_IN_HISTORY):
        self._messages: List[Dict[str, Any]] = []
        self._pending_feedback: str = ""
        self._max_images = max_images
    @property
    def pending_feedback_message(self) -> str:
        return self._pending_feedback
    @pending_feedback_message.setter
    def pending_feedback_message(self, value: str) -> None:
        self._pending_feedback = value
    def reset_pending_feedback(self) -> None:
        """重置待处理的反馈消息"""
        if self._pending_feedback:
            self._pending_feedback = ""
    def append(self, message: Dict[str, Any]) -> None:
        """添加消息到历史"""
        self._messages.append(message)
    def seed(self, messages: List[Dict[str, Any]]) -> None:
        """用初始消息重置历史"""
        self.reset()
        for msg in messages:
            self.append(msg)
    def reset(self) -> None:
        """清空历史"""
        self._messages.clear()
    def snapshot(self, max_images: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史快照，限制图片数量
        从最后往前保留max_images张图片，超出的替换为文本
        """
        limit = max_images if max_images is not None else self._max_images
        if limit is None:
            return list(self._messages)
        cloned = deepcopy(self._messages)
        image_count = 0
        # 从后往前遍历
        for i in range(len(cloned) - 1, -1, -1):
            msg = cloned[i]
            content = msg.get("content")
            if isinstance(content, list):
                for j, item in enumerate(content):
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        image_count += 1
                        if image_count > limit:
                            content[j] = {
                                "type": "text",
                                "text": "(image ignored due to size optimization)"
                            }
        return cloned
    def __len__(self) -> int:
        return len(self._messages)
    def __iter__(self):
        return iter(self._messages)
