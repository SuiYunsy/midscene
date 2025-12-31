"""
日志系统

从 packages/shared/src/logger.ts 迁移
使用Python标准logging模块
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from mspy.shared.common import get_midscene_run_sub_dir


# 日志前缀
TOPIC_PREFIX = "midscene"

# 日志记录器缓存
_loggers: dict[str, logging.Logger] = {}


def _setup_file_handler(logger: logging.Logger, topic: str) -> None:
    """设置文件处理器"""
    log_dir = get_midscene_run_sub_dir("log")
    if not log_dir:
        return
    
    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建文件处理器
    topic_filename = topic.replace(":", "-")
    log_file = Path(log_dir) / f"{topic_filename}.log"
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # 设置格式
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)


def get_logger(topic: str) -> logging.Logger:
    """
    获取或创建指定主题的日志记录器
    
    Args:
        topic: 日志主题，如 "ai:call", "agent"
    
    Returns:
        配置好的Logger实例
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    if full_topic not in _loggers:
        logger = logging.getLogger(full_topic)
        logger.setLevel(logging.DEBUG)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "[%(name)s] %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 添加文件处理器
        _setup_file_handler(logger, topic)
        
        _loggers[full_topic] = logger
    
    return _loggers[full_topic]


def get_debug(topic: str):
    """
    获取debug函数 (兼容TypeScript版本的接口)
    
    Args:
        topic: 日志主题
    
    Returns:
        debug函数
    """
    logger = get_logger(topic)
    return logger.debug


def enable_debug(topic: str) -> None:
    """
    启用指定主题的调试输出
    
    Args:
        topic: 日志主题
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    if full_topic in _loggers:
        for handler in _loggers[full_topic].handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)


def cleanup_loggers() -> None:
    """清理所有日志记录器"""
    for logger in _loggers.values():
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    _loggers.clear()
