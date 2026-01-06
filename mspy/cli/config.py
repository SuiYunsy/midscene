"""
配置工厂

从 packages/cli/src/config-factory.ts 和 cli-utils.ts 迁移
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class BatchRunnerConfig:
    """批量运行器配置"""
    files: List[str] = field(default_factory=list)
    concurrent: int = 1
    continue_on_error: bool = False
    summary: str = "summary.json"
    headed: bool = False
    keep_window: bool = False
    dotenv_override: bool = False
    dotenv_debug: bool = False
    
    # Web配置
    web: Optional[Dict[str, Any]] = None


# 默认配置
DEFAULT_CONFIG = BatchRunnerConfig()


def match_yaml_files(file_glob: str) -> List[str]:
    """
    匹配YAML文件
    
    Args:
        file_glob: 文件路径或glob模式
    
    Returns:
        匹配的文件列表
    """
    from glob import glob
    
    path = Path(file_glob)
    
    if path.exists() and path.is_dir():
        file_glob = str(path / "**/*.yaml")
        files1 = glob(file_glob, recursive=True)
        file_glob = str(path / "**/*.yml")
        files2 = glob(file_glob, recursive=True)
        files = files1 + files2
    else:
        files = glob(file_glob, recursive=True)
    
    # 过滤并排序
    yaml_files = [
        f for f in files
        if f.endswith(".yml") or f.endswith(".yaml")
    ]
    yaml_files.sort()
    
    return yaml_files


def create_config(
    config_file: str,
    options: Dict[str, Any]
) -> BatchRunnerConfig:
    """
    从配置文件创建配置
    
    Args:
        config_file: 配置文件路径
        options: 命令行选项
    
    Returns:
        BatchRunnerConfig实例
    """
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}
    
    # 获取文件列表
    files = config_data.get("files", [])
    if isinstance(files, str):
        files = [files]
    
    # 处理相对路径
    config_dir = Path(config_file).parent
    resolved_files = []
    for file_pattern in files:
        if not Path(file_pattern).is_absolute():
            file_pattern = str(config_dir / file_pattern)
        matched = match_yaml_files(file_pattern)
        resolved_files.extend(matched)
    
    # 合并配置
    config = BatchRunnerConfig(
        files=resolved_files,
        concurrent=options.get("concurrent", config_data.get("concurrent", 1)),
        continue_on_error=options.get("continue_on_error", config_data.get("continueOnError", False)),
        summary=options.get("summary", config_data.get("summary", "summary.json")),
        headed=options.get("headed", config_data.get("headed", False)),
        keep_window=options.get("keep_window", config_data.get("keepWindow", False)),
        dotenv_override=options.get("dotenv_override", config_data.get("dotenvOverride", False)),
        dotenv_debug=options.get("dotenv_debug", config_data.get("dotenvDebug", False)),
        web=config_data.get("web"),
    )
    
    # keep_window自动启用headed
    if config.keep_window:
        config.headed = True
    
    return config


def create_files_config(
    files: List[str],
    options: Dict[str, Any]
) -> BatchRunnerConfig:
    """
    从文件列表创建配置
    
    Args:
        files: YAML文件列表
        options: 命令行选项
    
    Returns:
        BatchRunnerConfig实例
    """
    config = BatchRunnerConfig(
        files=files,
        concurrent=options.get("concurrent", 1),
        continue_on_error=options.get("continue_on_error", False),
        summary=options.get("summary", "summary.json"),
        headed=options.get("headed", False),
        keep_window=options.get("keep_window", False),
        dotenv_override=options.get("dotenv_override", False),
        dotenv_debug=options.get("dotenv_debug", False),
    )
    
    # keep_window自动启用headed
    if config.keep_window:
        config.headed = True
    
    return config
