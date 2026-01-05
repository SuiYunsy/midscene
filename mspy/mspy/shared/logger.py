"""
日志系统

提供基于logging的日志功能。
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from mspy.shared.common import get_midscene_run_sub_dir

# 日志前缀
TOPIC_PREFIX = "midscene"

# 文件流缓存
_log_streams: dict[str, logging.FileHandler] = {}

# 调试实例缓存
_debug_instances: dict[str, Callable[..., None]] = {}


def _get_log_file_handler(topic: str) -> logging.FileHandler:
    """
    获取或创建日志文件处理器
    
    Args:
        topic: 日志主题
        
    Returns:
        文件处理器
    """
    topic_filename = topic.replace(":", "-")
    
    if topic_filename not in _log_streams:
        log_dir = get_midscene_run_sub_dir("log")
        log_file = Path(log_dir) / f"{topic_filename}.log"
        
        handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
        )
        _log_streams[topic_filename] = handler
    
    return _log_streams[topic_filename]


def get_debug(topic: str) -> Callable[..., None]:
    """
    获取调试日志函数
    
    Args:
        topic: 日志主题
        
    Returns:
        日志函数
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    if full_topic not in _debug_instances:
        # 创建专用logger
        logger = logging.getLogger(full_topic)
        logger.setLevel(logging.DEBUG)
        
        # 添加文件处理器
        try:
            file_handler = _get_log_file_handler(topic)
            logger.addHandler(file_handler)
        except Exception:
            pass  # 忽略文件写入错误
        
        # 检查是否启用控制台输出
        debug_env = os.environ.get("DEBUG", "")
        should_log_to_console = (
            f"{TOPIC_PREFIX}:*" in debug_env or
            full_topic in debug_env or
            debug_env == "*"
        )
        
        if should_log_to_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(
                logging.Formatter(f"  {full_topic} %(message)s")
            )
            logger.addHandler(console_handler)
        
        def debug_wrapper(*args: object) -> None:
            message = " ".join(str(arg) for arg in args)
            logger.debug(message)
        
        _debug_instances[full_topic] = debug_wrapper
    
    return _debug_instances[full_topic]


def enable_debug(topic: str) -> None:
    """
    启用指定主题的调试输出
    
    Args:
        topic: 日志主题
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    # 获取或创建logger
    logger = logging.getLogger(full_topic)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(
        logging.Formatter(f"  {full_topic} %(message)s")
    )
    logger.addHandler(console_handler)


def cleanup_log_streams() -> None:
    """
    清理所有日志流
    """
    for handler in _log_streams.values():
        handler.close()
    _log_streams.clear()
    _debug_instances.clear()
