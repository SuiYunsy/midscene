from __future__ import annotations

import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

_console = Console()
_handlers_cache: dict[str, logging.Logger] = {}


def get_logger(name: str = "mspy", level: int = logging.INFO) -> logging.Logger:
    """
    获取带有 Rich 样式的 logger。
    中文注释：统一日志入口，便于排查 CLI 与核心流程。
    """

    if name in _handlers_cache:
        return _handlers_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not any(isinstance(handler, RichHandler) for handler in logger.handlers):
        handler = RichHandler(console=_console, show_time=True, show_path=False, rich_tracebacks=True)
        handler.setLevel(level)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _handlers_cache[name] = logger
    return logger


def install_basic_logging(level: int = logging.INFO) -> None:
    """安装基础日志，便于在脚本中快速启用。"""
    logging.basicConfig(level=level)
    get_logger(level=level)
