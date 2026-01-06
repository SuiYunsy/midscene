"""
Logger - 日志模块
提供统一的日志记录功能
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Callable


# 日志流字典
_log_handlers: Dict[str, logging.Handler] = {}
_loggers: Dict[str, logging.Logger] = {}

# 默认日志目录
_log_dir: Optional[Path] = None


def setup_logger(log_dir: Optional[str] = None) -> None:
    """
    设置日志配置
    
    Args:
        log_dir: 日志目录路径，默认为 midscene_run/log
    """
    global _log_dir
    
    if log_dir:
        _log_dir = Path(log_dir)
    else:
        _log_dir = Path.cwd() / "midscene_run" / "log"
    
    _log_dir.mkdir(parents=True, exist_ok=True)


def get_log_stream(topic: str) -> logging.Handler:
    """
    获取或创建日志处理器
    
    Args:
        topic: 日志主题
        
    Returns:
        日志处理器
    """
    global _log_dir, _log_handlers
    
    topic_filename = topic.replace(":", "-")
    
    if topic_filename not in _log_handlers:
        if _log_dir is None:
            setup_logger()
        
        log_file = _log_dir / f"{topic_filename}.log"
        handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        _log_handlers[topic_filename] = handler
    
    return _log_handlers[topic_filename]


def get_debug(topic: str) -> Callable[..., None]:
    """
    获取调试日志函数
    
    Args:
        topic: 日志主题
        
    Returns:
        日志函数
    """
    global _loggers
    
    full_topic = f"midscene:{topic}"
    
    if full_topic not in _loggers:
        logger = logging.getLogger(full_topic)
        logger.setLevel(logging.DEBUG)
        
        # 添加文件处理器
        handler = get_log_stream(topic)
        logger.addHandler(handler)
        
        # 添加控制台处理器（如果设置了 DEBUG 环境变量）
        if os.environ.get("MIDSCENE_DEBUG_MODE"):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(console_handler)
        
        _loggers[full_topic] = logger
    
    logger = _loggers[full_topic]
    
    def log_func(*args) -> None:
        """Log message with formatted arguments"""
        message = " ".join(str(arg) for arg in args)
        logger.debug(message)
    
    return log_func


def cleanup_log_streams() -> None:
    """清理所有日志流"""
    global _log_handlers, _loggers
    
    for handler in _log_handlers.values():
        handler.close()
    
    _log_handlers.clear()
    _loggers.clear()
