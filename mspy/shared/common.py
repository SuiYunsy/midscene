"""
通用工具模块 - 提供跨模块使用的通用功能

对应TypeScript源码: packages/shared/src/common.ts
"""

import os
from pathlib import Path
from typing import Optional


def get_midscene_run_dir() -> str:
    """获取Midscene运行目录
    
    优先使用MIDSCENE_RUN_DIR环境变量，否则使用当前工作目录下的midscene_run
    
    Returns:
        运行目录路径
    """
    env_dir = os.environ.get('MIDSCENE_RUN_DIR')
    if env_dir:
        return env_dir
    
    return os.path.join(os.getcwd(), 'midscene_run')


def get_midscene_run_sub_dir(sub_dir: str) -> str:
    """获取Midscene运行子目录
    
    Args:
        sub_dir: 子目录名称
        
    Returns:
        子目录完整路径
    """
    base_dir = get_midscene_run_dir()
    full_path = os.path.join(base_dir, sub_dir)
    
    # 确保目录存在
    os.makedirs(full_path, exist_ok=True)
    
    return full_path


def get_report_dir() -> str:
    """获取报告目录
    
    Returns:
        报告目录路径
    """
    return get_midscene_run_sub_dir('report')


def get_cache_dir() -> str:
    """获取缓存目录
    
    Returns:
        缓存目录路径
    """
    return get_midscene_run_sub_dir('cache')


def get_output_dir() -> str:
    """获取输出目录
    
    Returns:
        输出目录路径
    """
    return get_midscene_run_sub_dir('output')


def ensure_dir_exists(path: str) -> str:
    """确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        目录路径
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_version() -> str:
    """获取当前版本号
    
    Returns:
        版本号字符串
    """
    return "0.1.0"


# 文件扩展名常量
GROUPED_ACTION_DUMP_FILE_EXT = ".web-dump.json"
REPORT_FILE_EXT = ".html"


def get_report_file_name(base_name: str) -> str:
    """生成报告文件名
    
    Args:
        base_name: 基础文件名
        
    Returns:
        完整文件名（不含路径）
    """
    import time
    timestamp = int(time.time() * 1000)
    return f"{base_name}-{timestamp}"
