"""
日志模块
Logger module for Midscene Python SDK
"""
import logging
import sys
import re
from typing import Optional
from functools import lru_cache

# Midscene日志前缀
LOG_PREFIX = "midscene"

# 创建自定义日志格式化器
class MidsceneFormatter(logging.Formatter):
    """Midscene日志格式化器，支持隐藏敏感信息"""
    
    # 匹配base64图片数据的正则
    BASE64_PATTERN = re.compile(
        r'"url"\s*:\s*"data:image/[^;]+;base64,[^"]*"',
        re.IGNORECASE
    )
    
    def format(self, record: logging.LogRecord) -> str:
        # 获取原始消息
        message = super().format(record)
        
        # 隐藏base64图片数据
        message = self.BASE64_PATTERN.sub(
            '"url": "data:image/...;base64,[masked]"',
            message
        )
        
        return message


class MidsceneLogFilter(logging.Filter):
    """Midscene日志过滤器，用于处理敏感内容"""
    
    # 匹配base64图片URL的正则
    BASE64_URL_PATTERN = re.compile(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+')
    
    def filter(self, record: logging.LogRecord) -> bool:
        # 处理消息内容
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # 隐藏base64内容
            record.msg = self.BASE64_URL_PATTERN.sub(
                'data:image/...;base64,[masked]',
                record.msg
            )
        
        # 处理系统提示词，只保留前50个字符
        if hasattr(record, 'args') and record.args:
            args = list(record.args)
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    # 隐藏base64内容
                    args[i] = self.BASE64_URL_PATTERN.sub(
                        'data:image/...;base64,[masked]',
                        arg
                    )
            record.args = tuple(args)
        
        return True


@lru_cache(maxsize=32)
def get_logger(topic: str) -> logging.Logger:
    """
    获取指定主题的日志记录器
    
    Args:
        topic: 日志主题
        
    Returns:
        配置好的日志记录器
    """
    logger_name = f"{LOG_PREFIX}:{topic}"
    logger = logging.getLogger(logger_name)
    
    # 避免重复添加handler
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        formatter = MidsceneFormatter(
            fmt='[%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 添加过滤器
        console_handler.addFilter(MidsceneLogFilter())
        
        logger.addHandler(console_handler)
        
        # 不传播到根日志，避免重复输出
        logger.propagate = False
    
    return logger


def get_debug(topic: str):
    """
    获取调试函数，类似于TypeScript中的debug库
    
    Args:
        topic: 调试主题
        
    Returns:
        调试函数
    """
    logger = get_logger(topic)
    
    def debug_fn(*args, **kwargs):
        if args:
            message = " ".join(str(arg) for arg in args)
            logger.debug(message)
    
    return debug_fn


def log_request_response(
    role: str, 
    content: str, 
    logger: Optional[logging.Logger] = None
):
    """
    记录请求/响应日志，处理敏感信息
    
    Args:
        role: 角色 ('system', 'user', 'assistant')
        content: 内容
        logger: 日志记录器
    """
    if logger is None:
        logger = get_logger("ai:call")
    
    # 隐藏base64内容
    base64_pattern = re.compile(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+')
    cleaned_content = base64_pattern.sub('data:image/...;base64,[masked]', content)
    
    # 对于system消息，只打印前50个字符
    if role == "system":
        if len(cleaned_content) > 50:
            cleaned_content = cleaned_content[:50] + "..."
    
    logger.debug(f"[{role}] {cleaned_content}")
