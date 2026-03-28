# -*- coding: utf-8 -*-
"""
Midscene Logger Module
日志模块，提供统一的日志记录功能
"""

import logging
import sys
from datetime import datetime
from typing import Optional


# 日志格式化器，带上库自己的名称
class MidsceneFormatter(logging.Formatter):
    """自定义格式化器，格式为: [时间] midscene:topic - LEVEL - 消息"""
    
    def __init__(self, topic: str = ""):
        self.topic = topic
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        topic_str = f"midscene:{self.topic}" if self.topic else "midscene"
        message = record.getMessage()
        return f"[{timestamp}] {topic_str} - {level} - {message}"


# 缓存已创建的logger
_loggers: dict = {}


def get_logger(topic: str = "") -> logging.Logger:
    """
    获取一个带有midscene前缀的logger
    
    Args:
        topic: 日志主题，如 "agent", "service" 等
    
    Returns:
        配置好的Logger实例
    """
    logger_name = f"midscene.{topic}" if topic else "midscene"
    
    if logger_name in _loggers:
        return _loggers[logger_name]
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # 不传播到根日志，避免重复输出
    logger.propagate = False
    
    # 检查是否已经有handler，避免重复添加
    if not logger.handlers:
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(MidsceneFormatter(topic))
        logger.addHandler(console_handler)
    
    _loggers[logger_name] = logger
    return logger


def get_debug(topic: str = "") -> callable:
    """
    获取一个debug日志函数，类似于TypeScript中的getDebug
    
    Args:
        topic: 日志主题
    
    Returns:
        一个可调用的debug日志函数
    """
    logger = get_logger(topic)
    
    def debug_fn(*args):
        message = " ".join(str(arg) for arg in args)
        logger.debug(message)
    
    return debug_fn


def set_log_level(level: int) -> None:
    """
    设置所有midscene logger的日志级别
    
    Args:
        level: 日志级别，如 logging.DEBUG, logging.INFO 等
    """
    for logger in _loggers.values():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
