"""
Types - Core 模块类型定义
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum


@dataclass
class ServiceTaskInfo:
    """服务任务信息"""
    duration_ms: int = 0
    format_response: Optional[str] = None
    raw_response: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


@dataclass
class ServiceDump:
    """服务转储"""
    type: str  # 'locate' | 'extract' | 'assert'
    log_id: str
    log_time: int
    user_query: Dict[str, Any] = field(default_factory=dict)
    matched_element: List[Any] = field(default_factory=list)
    matched_rect: Optional[Dict[str, float]] = None
    deep_think: bool = False
    data: Any = None
    assertion_pass: Optional[bool] = None
    assertion_thought: Optional[str] = None
    task_info: Optional[ServiceTaskInfo] = None
    error: Optional[str] = None
    output: Any = None


@dataclass
class ExecutionRecorderItem:
    """执行记录项"""
    type: str  # 'screenshot'
    ts: int
    screenshot: Optional[str] = None
    timing: Optional[str] = None


class ExecutionTaskStatus(str, Enum):
    """执行任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionTask:
    """执行任务"""
    type: str  # 'Planning' | 'Insight' | 'Action Space' | 'Log'
    sub_type: Optional[str] = None
    sub_task: bool = False
    param: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None
    status: ExecutionTaskStatus = ExecutionTaskStatus.PENDING
    error: Optional[Exception] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    timing: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    output: Any = None
    log: Any = None
    recorder: List[ExecutionRecorderItem] = field(default_factory=list)


@dataclass
class ExecutionDump:
    """执行转储"""
    log_time: int
    name: str
    description: Optional[str] = None
    tasks: List[ExecutionTask] = field(default_factory=list)
    ai_act_context: Optional[str] = None


@dataclass
class GroupedActionDump:
    """分组动作转储"""
    sdk_version: str
    group_name: str
    group_description: Optional[str] = None
    model_briefs: List[str] = field(default_factory=list)
    executions: List[ExecutionDump] = field(default_factory=list)


@dataclass
class ConversationMessage:
    """对话消息"""
    role: str  # 'system' | 'user' | 'assistant'
    content: Union[str, List[Dict[str, Any]]]


class ConversationHistory:
    """对话历史管理"""
    
    def __init__(self):
        self._messages: List[ConversationMessage] = []
        self._pending_feedback_message: Optional[str] = None
    
    @property
    def pending_feedback_message(self) -> Optional[str]:
        return self._pending_feedback_message
    
    @pending_feedback_message.setter
    def pending_feedback_message(self, value: Optional[str]):
        self._pending_feedback_message = value
    
    def append(self, message: Union[ConversationMessage, Dict[str, Any]]) -> None:
        """添加消息"""
        if isinstance(message, dict):
            message = ConversationMessage(
                role=message["role"],
                content=message["content"]
            )
        self._messages.append(message)
    
    def reset_pending_feedback_message_if_exists(self) -> None:
        """重置待处理的反馈消息"""
        self._pending_feedback_message = None
    
    def snapshot(self, images_include_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话历史快照
        
        Args:
            images_include_count: 包含的图片数量限制
            
        Returns:
            消息列表
        """
        result = []
        image_count = 0
        
        # 从后往前遍历，限制图片数量
        for msg in reversed(self._messages):
            msg_dict = {"role": msg.role, "content": msg.content}
            
            if images_include_count is not None:
                if isinstance(msg.content, list):
                    has_image = any(
                        item.get("type") == "image_url"
                        for item in msg.content
                        if isinstance(item, dict)
                    )
                    if has_image:
                        if image_count >= images_include_count:
                            # 移除图片内容
                            msg_dict["content"] = [
                                item for item in msg.content
                                if not isinstance(item, dict) or item.get("type") != "image_url"
                            ]
                        else:
                            image_count += 1
            
            result.insert(0, msg_dict)
        
        return result
    
    def clear(self) -> None:
        """清空对话历史"""
        self._messages.clear()
        self._pending_feedback_message = None
