"""
日志模块 - 提供带有库名称前缀的日志功能
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class MidsceneFormatter(logging.Formatter):
    """自定义日志格式化器，带有库名称前缀"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 格式: [2025-12-31 16:42:22] midscene:topic - LEVEL - message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        topic = getattr(record, 'topic', record.name.replace('midscene.', ''))
        return f"[{timestamp}] midscene:{topic} - {record.levelname} - {record.getMessage()}"


class MidsceneLogger:
    """Midscene日志器，不传播到根日志"""
    
    _instances: Dict[str, 'MidsceneLogger'] = {}
    _handler: Optional[logging.StreamHandler] = None
    
    def __init__(self, topic: str):
        self.topic = topic
        self.logger = logging.getLogger(f"midscene.{topic}")
        # 防止日志传播到根日志器（避免重复输出）
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)
        
        # 确保只添加一个处理器
        if not self.logger.handlers:
            if MidsceneLogger._handler is None:
                MidsceneLogger._handler = logging.StreamHandler(sys.stdout)
                MidsceneLogger._handler.setFormatter(MidsceneFormatter())
                MidsceneLogger._handler.setLevel(logging.DEBUG)
            self.logger.addHandler(MidsceneLogger._handler)
    
    def debug(self, *args: Any) -> None:
        """Debug level log"""
        message = " ".join(str(arg) for arg in args)
        self.logger.debug(message, extra={'topic': self.topic})
    
    def info(self, *args: Any) -> None:
        """Info level log"""
        message = " ".join(str(arg) for arg in args)
        self.logger.info(message, extra={'topic': self.topic})
    
    def warning(self, *args: Any) -> None:
        """Warning level log"""
        message = " ".join(str(arg) for arg in args)
        self.logger.warning(message, extra={'topic': self.topic})
    
    def error(self, *args: Any) -> None:
        """Error level log"""
        message = " ".join(str(arg) for arg in args)
        self.logger.error(message, extra={'topic': self.topic})
    
    def __call__(self, *args: Any) -> None:
        """Allow logger to be called directly like a function (debug level)"""
        self.debug(*args)


def get_debug(topic: str) -> MidsceneLogger:
    """
    获取指定topic的日志器
    
    Args:
        topic: 日志主题，例如 'agent', 'service', 'planning'
    
    Returns:
        MidsceneLogger实例
    """
    if topic not in MidsceneLogger._instances:
        MidsceneLogger._instances[topic] = MidsceneLogger(topic)
    return MidsceneLogger._instances[topic]


def set_log_level(level: int) -> None:
    """
    设置所有Midscene日志器的日志级别
    
    Args:
        level: 日志级别，例如 logging.DEBUG, logging.INFO
    """
    for logger_instance in MidsceneLogger._instances.values():
        logger_instance.logger.setLevel(level)
    if MidsceneLogger._handler:
        MidsceneLogger._handler.setLevel(level)
