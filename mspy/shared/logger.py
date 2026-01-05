"""日志模块 - 带时间戳和库名前缀"""
import logging
import sys
from datetime import datetime
from typing import Optional

_LIBRARY_NAME = "mspy"
_loggers: dict[str, logging.Logger] = {}

class MspyFormatter(logging.Formatter):
    """自定义格式化器 - 添加时间戳和库名"""
    def format(self, record: logging.LogRecord) -> str:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S") + f".{now.microsecond // 1000:03d}"
        tz_offset = now.astimezone().strftime("%z")
        tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}" if len(tz_offset) == 5 else tz_offset
        return f"[{timestamp}{tz_formatted}] [{_LIBRARY_NAME}:{record.name}] {record.getMessage()}"

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """获取日志记录器，带库名前缀"""
    full_name = f"{_LIBRARY_NAME}.{name}"
    if full_name in _loggers:
        return _loggers[full_name]
    logger = logging.getLogger(full_name)
    logger.propagate = False  # 不传播到根日志
    if level is None:
        level = logging.INFO
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(MspyFormatter())
        logger.addHandler(handler)
    _loggers[full_name] = logger
    return logger
