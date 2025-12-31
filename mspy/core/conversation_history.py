# -*- coding: utf-8 -*-
"""
Midscene Conversation History Module
对话历史管理模块，用于管理多轮对话
"""

from typing import List, Dict, Any, Optional
import copy


class ConversationHistory:
    """对话历史管理器"""
    
    def __init__(self, initial_messages: Optional[List[Dict[str, Any]]] = None):
        self._messages: List[Dict[str, Any]] = []
        self.pending_feedback_message: str = ""
        
        if initial_messages:
            self.seed(initial_messages)
    
    def reset_pending_feedback_message_if_exists(self) -> None:
        """重置待处理的反馈消息"""
        if self.pending_feedback_message:
            self.pending_feedback_message = ""
    
    def append(self, message: Dict[str, Any]) -> None:
        """添加一条消息"""
        self._messages.append(message)
    
    def seed(self, messages: List[Dict[str, Any]]) -> None:
        """用给定的消息初始化历史"""
        self.reset()
        for message in messages:
            self.append(message)
    
    def reset(self) -> None:
        """重置历史"""
        self._messages.clear()
    
    def snapshot(self, max_images: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史的快照
        如果max_images指定，则超出限制的图像会被替换为文本
        
        Args:
            max_images: 最大图像数量，None表示不限制
        
        Returns:
            消息列表的副本
        """
        if max_images is None:
            return list(self._messages)
        
        cloned_messages = copy.deepcopy(self._messages)
        image_count = 0
        
        # 从后向前遍历，保留最新的图像
        for i in range(len(cloned_messages) - 1, -1, -1):
            message = cloned_messages[i]
            content = message.get("content")
            
            if isinstance(content, list):
                for j in range(len(content)):
                    item = content[j]
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        image_count += 1
                        if image_count > max_images:
                            content[j] = {
                                "type": "text",
                                "text": "(image ignored due to size optimization)"
                            }
        
        return cloned_messages
    
    @property
    def length(self) -> int:
        """获取消息数量"""
        return len(self._messages)
    
    def __iter__(self):
        return iter(self._messages)
    
    def to_json(self) -> List[Dict[str, Any]]:
        """转换为JSON格式"""
        return self.snapshot()
