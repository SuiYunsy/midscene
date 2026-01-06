# -*- coding: utf-8 -*-
"""
日志模块
提供调试日志功能。
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .common import get_midscene_run_sub_dir

# 日志主题前缀
TOPIC_PREFIX = "midscene"

# 存储日志处理器的映射
_log_handlers: Dict[str, logging.FileHandler] = {}
# 存储调试函数的映射
_debug_instances: Dict[str, Callable] = {}


def _get_log_file_path(topic: str) -> Path:
    """获取日志文件路径"""
    topic_file_name = topic.replace(":", "-")
    log_dir = get_midscene_run_sub_dir("log")
    return Path(log_dir) / f"{topic_file_name}.log"


def _write_log_to_file(topic: str, message: str) -> None:
    """将日志写入文件"""
    log_file = _get_log_file_path(topic)
    
    # 确保目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成 ISO 格式时间戳
    now = datetime.now()
    # 计算时区偏移
    utc_offset = now.astimezone().strftime('%z')
    # 格式化为 +HH:mm 格式
    if len(utc_offset) == 5:
        utc_offset = f"{utc_offset[:3]}:{utc_offset[3:]}"
    
    timestamp = now.strftime(f"%Y-%m-%dT%H:%M:%S.{now.microsecond // 1000:03d}{utc_offset}")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


def get_debug(topic: str) -> Callable[..., None]:
    """
    获取调试日志函数
    
    Args:
        topic: 日志主题
        
    Returns:
        调试日志函数
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    if full_topic not in _debug_instances:
        # 检查是否启用了调试模式
        debug_env = os.environ.get('DEBUG', '')
        debug_enabled = (
            debug_env == '*' or 
            TOPIC_PREFIX in debug_env or 
            topic in debug_env or
            full_topic in debug_env
        )
        
        def debug_fn(*args: Any) -> None:
            # 格式化消息
            message = ' '.join(str(arg) for arg in args)
            
            # 写入日志文件
            _write_log_to_file(topic, message)
            
            # 如果启用了调试模式，也输出到控制台
            if debug_enabled:
                print(f"[{full_topic}] {message}")
        
        _debug_instances[full_topic] = debug_fn
    
    return _debug_instances[full_topic]


def enable_debug(topic: str) -> None:
    """
    启用指定主题的调试输出
    
    Args:
        topic: 日志主题
    """
    # 在 Python 中通过设置环境变量来启用
    current = os.environ.get('DEBUG', '')
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    if full_topic not in current:
        if current:
            os.environ['DEBUG'] = f"{current},{full_topic}"
        else:
            os.environ['DEBUG'] = full_topic


def cleanup_log_streams() -> None:
    """清理所有日志流"""
    global _log_handlers, _debug_instances
    
    for handler in _log_handlers.values():
        handler.close()
    
    _log_handlers.clear()
    _debug_instances.clear()
