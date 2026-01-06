"""
对话历史模块
Conversation history module
"""
from typing import Any, Dict, List, Optional
from copy import deepcopy


class ConversationHistory:
    """
    Conversation history for AI planning.
    AI规划的对话历史
    """
    
    def __init__(self, initial_messages: Optional[List[Dict[str, Any]]] = None):
        self._messages: List[Dict[str, Any]] = []
        self.pending_feedback_message: str = ""
        
        if initial_messages:
            self.seed(initial_messages)
    
    def reset_pending_feedback_message_if_exists(self) -> None:
        """Reset pending feedback message if it exists."""
        if self.pending_feedback_message:
            self.pending_feedback_message = ""
    
    def append(self, message: Dict[str, Any]) -> None:
        """Append a message to history."""
        self._messages.append(message)
    
    def seed(self, messages: List[Dict[str, Any]]) -> None:
        """Seed conversation with initial messages."""
        self.reset()
        for message in messages:
            self.append(message)
    
    def reset(self) -> None:
        """Reset conversation history."""
        self._messages.clear()
        self.pending_feedback_message = ""
    
    def snapshot(self, max_images: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Snapshot the conversation history.
        快照对话历史
        
        Args:
            max_images: Maximum number of images to include (from the end).
                       None means no limit.
        
        Returns:
            List of messages with images potentially replaced
        """
        if max_images is None:
            return list(self._messages)
        
        cloned_messages = deepcopy(self._messages)
        image_count = 0
        
        # Traverse from end to beginning
        for i in range(len(cloned_messages) - 1, -1, -1):
            message = cloned_messages[i]
            content = message.get("content")
            
            if isinstance(content, list):
                for j, item in enumerate(content):
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        image_count += 1
                        
                        # If exceeded limit, replace with text
                        if image_count > max_images:
                            content[j] = {
                                "type": "text",
                                "text": "(image ignored due to size optimization)",
                            }
        
        return cloned_messages
    
    def __len__(self) -> int:
        return len(self._messages)
    
    def __iter__(self):
        return iter(self._messages)
    
    def to_json(self) -> List[Dict[str, Any]]:
        """Convert to JSON-serializable format."""
        return self.snapshot()
