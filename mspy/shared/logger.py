"""
日志模块
Logging module for midscene
"""
import logging
import os
import sys
from typing import Optional
from datetime import datetime

# 顶级前缀
TOPIC_PREFIX = "midscene"

# 日志实例缓存
_loggers: dict = {}


def setup_console_handler(logger: logging.Logger) -> None:
    """设置控制台处理器，确保实时输出"""
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)


def get_debug(topic: str) -> logging.Logger:
    """
    Get a debug logger for a specific topic.
    获取指定主题的调试日志器
    
    Args:
        topic: The topic name for the logger
        
    Returns:
        A logger instance for the topic
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    if full_topic not in _loggers:
        logger = logging.getLogger(full_topic)
        setup_console_handler(logger)
        _loggers[full_topic] = logger
    
    return _loggers[full_topic]


def enable_debug(topic: str) -> None:
    """
    Enable debug logging for a specific topic.
    启用特定主题的调试日志
    """
    logger = get_debug(topic)
    logger.setLevel(logging.DEBUG)


def disable_debug(topic: str) -> None:
    """
    Disable debug logging for a specific topic.
    禁用特定主题的调试日志
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    if full_topic in _loggers:
        _loggers[full_topic].setLevel(logging.WARNING)


def cleanup_log_streams() -> None:
    """
    Cleanup all log streams.
    清理所有日志流
    """
    for logger in _loggers.values():
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    _loggers.clear()


# 配置根日志器，确保所有日志都能输出到控制台
def configure_root_logger() -> None:
    """Configure root logger for console output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 检查是否已有处理器
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


# 初始化时配置根日志器
configure_root_logger()
