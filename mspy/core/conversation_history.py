"""
对话历史模块
Conversation history for Midscene Python SDK
"""
from typing import List, Dict, Any, Optional
from copy import deepcopy


class ConversationHistory:
    """对话历史管理类"""
    
    def __init__(self, initial_messages: Optional[List[Dict[str, Any]]] = None):
        """
        初始化对话历史
        
        Args:
            initial_messages: 初始消息列表
        """
        self._messages: List[Dict[str, Any]] = []
        self.pending_feedback_message: str = ""
        
        if initial_messages:
            self.seed(initial_messages)
    
    def reset_pending_feedback_message_if_exists(self):
        """重置待处理的反馈消息"""
        if self.pending_feedback_message:
            self.pending_feedback_message = ""
    
    def append(self, message: Dict[str, Any]):
        """
        添加消息到历史
        
        Args:
            message: 消息对象
        """
        self._messages.append(message)
    
    def seed(self, messages: List[Dict[str, Any]]):
        """
        用指定消息初始化历史
        
        Args:
            messages: 消息列表
        """
        self.reset()
        for message in messages:
            self.append(message)
    
    def reset(self):
        """重置消息历史"""
        self._messages.clear()
    
    def snapshot(self, max_images: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取消息历史快照，可选限制图片数量
        
        Args:
            max_images: 最大图片数量，None表示不限制
            
        Returns:
            消息历史的副本
        """
        if max_images is None:
            return list(self._messages)
        
        cloned_messages = deepcopy(self._messages)
        image_count = 0
        
        # 从后向前遍历
        for i in range(len(cloned_messages) - 1, -1, -1):
            message = cloned_messages[i]
            content = message.get('content')
            
            # 只处理数组类型的content
            if isinstance(content, list):
                for j, item in enumerate(content):
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        image_count += 1
                        
                        # 如果超过限制，替换为文本
                        if image_count > max_images:
                            content[j] = {
                                'type': 'text',
                                'text': '(image ignored due to size optimization)'
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
