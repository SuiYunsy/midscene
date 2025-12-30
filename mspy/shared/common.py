# -*- coding: utf-8 -*-
"""
通用工具模块
提供目录和路径相关的工具函数。
"""

import os
import tempfile
from pathlib import Path
from typing import Literal

from .env.constants import MIDSCENE_RUN_DIR

# 默认运行目录名
DEFAULT_RUN_DIR_NAME = "midscene_run"

# 运行目录类型
RunDirType = Literal["dump", "cache", "report", "tmp", "log", "output"]


def _get_basic_env_value(key: str) -> str | None:
    """从环境变量获取基础配置值"""
    return os.environ.get(key)


def get_midscene_run_dir() -> str:
    """
    获取 Midscene 运行目录名称
    
    Returns:
        运行目录名称
    """
    return _get_basic_env_value(MIDSCENE_RUN_DIR) or DEFAULT_RUN_DIR_NAME


def get_midscene_run_base_dir() -> str:
    """
    获取 Midscene 运行基础目录的绝对路径
    
    Returns:
        基础目录的绝对路径
    """
    base_path = Path.cwd() / get_midscene_run_dir()
    
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except OSError:
        # 如果创建失败，使用临时目录
        base_path = Path(tempfile.gettempdir()) / DEFAULT_RUN_DIR_NAME
        base_path.mkdir(parents=True, exist_ok=True)
    
    return str(base_path)


def get_midscene_run_sub_dir(subdir: RunDirType) -> str:
    """
    获取 Midscene 运行子目录的路径，如果不存在则创建
    
    Args:
        subdir: 子目录类型 ('dump', 'cache', 'report', 'tmp', 'log', 'output')
        
    Returns:
        子目录的绝对路径
    """
    base_path = get_midscene_run_base_dir()
    sub_path = Path(base_path) / subdir
    
    sub_path.mkdir(parents=True, exist_ok=True)
    
    return str(sub_path)


# 错误代码
ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED = "NOT_IMPLEMENTED_AS_DESIGNED"
