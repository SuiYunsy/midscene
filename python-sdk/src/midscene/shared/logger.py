"""Logging utilities for Midscene."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Topic prefix for all Midscene loggers
TOPIC_PREFIX = "midscene"

# Store log file handlers
_log_handlers: Dict[str, logging.FileHandler] = {}
_loggers: Dict[str, logging.Logger] = {}


def _get_log_dir() -> Optional[Path]:
    """Get the log directory path."""
    from midscene.shared.common import get_midscene_run_sub_dir
    
    log_dir = get_midscene_run_sub_dir("log")
    if log_dir:
        return Path(log_dir)
    return None


def _get_log_handler(topic: str) -> Optional[logging.FileHandler]:
    """Get or create a file handler for the given topic."""
    topic_filename = topic.replace(":", "-")
    
    if topic_filename not in _log_handlers:
        log_dir = _get_log_dir()
        if log_dir:
            log_file = log_dir / f"{topic_filename}.log"
            handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S"
                )
            )
            _log_handlers[topic_filename] = handler
    
    return _log_handlers.get(topic_filename)


def get_logger(topic: str) -> logging.Logger:
    """
    Get a logger for the given topic.
    
    Creates a logger with both console and file output.
    File logs are written to the midscene_run/log directory.
    
    Args:
        topic: The topic/module name for the logger
        
    Returns:
        A configured logger instance
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    
    if full_topic not in _loggers:
        logger = logging.getLogger(full_topic)
        logger.setLevel(logging.DEBUG)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        # Console handler (only when DEBUG env is set)
        if os.environ.get("DEBUG", "").startswith(TOPIC_PREFIX):
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(
                logging.Formatter(
                    "%(name)s %(message)s"
                )
            )
            logger.addHandler(console_handler)
        
        # File handler
        file_handler = _get_log_handler(topic)
        if file_handler:
            logger.addHandler(file_handler)
        
        _loggers[full_topic] = logger
    
    return _loggers[full_topic]


def enable_debug(topic: str) -> None:
    """
    Enable debug output for a topic.
    
    Args:
        topic: The topic to enable debug for
    """
    full_topic = f"{TOPIC_PREFIX}:{topic}"
    logger = _loggers.get(full_topic)
    
    if logger:
        # Add console handler if not already present
        has_console = any(
            isinstance(h, logging.StreamHandler) and h.stream == sys.stderr
            for h in logger.handlers
        )
        if not has_console:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(
                logging.Formatter("%(name)s %(message)s")
            )
            logger.addHandler(console_handler)


def cleanup_log_handlers() -> None:
    """Close all log file handlers and clear caches."""
    for handler in _log_handlers.values():
        handler.close()
    _log_handlers.clear()
    _loggers.clear()
