"""
简单日志封装，统一英文输出。
"""

from __future__ import annotations

import logging
from typing import Optional


def get_logger(name: str, level: int = logging.INFO, handler: Optional[logging.Handler] = None) -> logging.Logger:
    """创建或获取 logger。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        fmt = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        stream_handler = handler or logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        logger.addHandler(stream_handler)
    return logger
