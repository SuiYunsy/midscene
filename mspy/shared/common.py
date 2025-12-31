"""
通用功能

从 packages/shared/src/common.ts 迁移
"""

import os
import tempfile
from pathlib import Path
from typing import Literal, Optional


# 默认运行目录名称
DEFAULT_RUN_DIR_NAME = "midscene_run"


def get_midscene_run_dir() -> str:
    """获取Midscene运行目录名称"""
    return os.environ.get("MIDSCENE_RUN_DIR", DEFAULT_RUN_DIR_NAME)


def get_midscene_run_base_dir() -> str:
    """
    获取Midscene运行基础目录
    
    Returns:
        运行目录的绝对路径
    """
    run_dir = get_midscene_run_dir()
    base_path = Path.cwd() / run_dir
    
    # 创建目录
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
    获取Midscene运行子目录
    
    Args:
        subdir: 子目录类型
    
    Returns:
        子目录的绝对路径
    """
    base_path = Path(get_midscene_run_base_dir())
    sub_path = base_path / subdir
    
    # 创建子目录
    sub_path.mkdir(parents=True, exist_ok=True)
    
    return str(sub_path)


# 错误码
ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED = "NOT_IMPLEMENTED_AS_DESIGNED"
