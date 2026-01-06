"""
日志模块 - 提供调试日志功能

对应TypeScript源码: packages/shared/src/logger.ts
"""

import logging
import os
from typing import Callable, Optional

# 配置基础日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_debug(namespace: str) -> Callable[..., None]:
    """获取调试日志函数
    
    类似于TypeScript中的debug包，根据MIDSCENE_DEBUG_MODE环境变量
    控制是否输出调试信息
    
    Args:
        namespace: 命名空间，用于区分不同模块的日志
        
    Returns:
        调试日志函数
    
    Example:
        >>> debug = get_debug('agent')
        >>> debug('Processing task', task_id=123)
    """
    logger = logging.getLogger(f"midscene:{namespace}")
    
    # 检查是否启用调试模式
    debug_mode = os.environ.get('MIDSCENE_DEBUG_MODE', '').lower()
    is_debug = debug_mode in ('true', '1', 'yes')
    
    if is_debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    
    def debug_fn(*args, **kwargs):
        """调试日志输出函数"""
        if not is_debug:
            return
            
        msg_parts = [str(arg) for arg in args]
        if kwargs:
            msg_parts.extend([f"{k}={v}" for k, v in kwargs.items()])
        
        message = ' '.join(msg_parts)
        logger.debug(message)
    
    return debug_fn


def get_logger(name: str) -> logging.Logger:
    """获取标准日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger实例
    """
    return logging.getLogger(f"midscene:{name}")


class Logger:
    """日志类，提供不同级别的日志方法"""
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(f"midscene:{name}")
        
        # 检查调试模式
        debug_mode = os.environ.get('MIDSCENE_DEBUG_MODE', '').lower()
        if debug_mode in ('true', '1', 'yes'):
            self._logger.setLevel(logging.DEBUG)
    
    def debug(self, message: str, *args, **kwargs):
        """输出调试日志"""
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """输出信息日志"""
        self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """输出警告日志"""
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """输出错误日志"""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """输出严重错误日志"""
        self._logger.critical(message, *args, **kwargs)
