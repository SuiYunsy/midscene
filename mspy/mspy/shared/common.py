"""
通用功能

提供运行目录管理等通用功能。
"""

import os
import tempfile
from pathlib import Path
from typing import Literal, Optional

from mspy.shared.env.basic import get_basic_env_value
from mspy.shared.env.types import MIDSCENE_RUN_DIR

# 默认运行目录名称
DEFAULT_RUN_DIR_NAME = "midscene_run"

# 错误代码
ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED = "NOT_IMPLEMENTED_AS_DESIGNED"


def get_midscene_run_dir() -> str:
    """
    获取Midscene运行目录名称
    
    Returns:
        运行目录名称
    """
    return get_basic_env_value(MIDSCENE_RUN_DIR) or DEFAULT_RUN_DIR_NAME


def get_midscene_run_base_dir() -> str:
    """
    获取Midscene运行基础目录路径
    
    会自动创建目录（如果不存在）。
    
    Returns:
        基础目录的绝对路径
    """
    base_path = Path.cwd() / get_midscene_run_dir()
    
    try:
        base_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        # 如果创建失败，使用临时目录
        base_path = Path(tempfile.gettempdir()) / DEFAULT_RUN_DIR_NAME
        base_path.mkdir(parents=True, exist_ok=True)
    
    return str(base_path)


SubDirType = Literal["dump", "cache", "report", "tmp", "log", "output"]


def get_midscene_run_sub_dir(subdir: SubDirType) -> str:
    """
    获取Midscene运行子目录路径
    
    会自动创建目录（如果不存在）。
    
    Args:
        subdir: 子目录类型
        
    Returns:
        子目录的绝对路径
    """
    base_path = Path(get_midscene_run_base_dir())
    sub_path = base_path / subdir
    
    sub_path.mkdir(parents=True, exist_ok=True)
    
    return str(sub_path)
