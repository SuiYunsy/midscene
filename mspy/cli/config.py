"""
配置工厂

对应TypeScript源码: packages/cli/src/config-factory.ts
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from mspy.cli.batch_runner import BatchRunnerConfig
from mspy.core.yaml.parser import MidsceneYamlScriptWebEnv


async def create_config(
    config_file: str,
    options: Optional[Dict[str, Any]] = None
) -> BatchRunnerConfig:
    """从配置文件创建执行器配置
    
    Args:
        config_file: 配置文件路径
        options: 命令行选项
        
    Returns:
        BatchRunnerConfig实例
    """
    options = options or {}
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    if not config_data:
        config_data = {}
    
    # 获取文件列表
    files = config_data.get('files', [])
    if isinstance(files, str):
        files = [files]
    
    # 解析相对路径
    config_dir = Path(config_file).parent
    resolved_files = []
    for file_pattern in files:
        file_path = config_dir / file_pattern
        if file_path.is_file():
            resolved_files.append(str(file_path))
        elif file_path.is_dir():
            for ext in ('*.yaml', '*.yml'):
                resolved_files.extend(str(f) for f in file_path.glob(ext))
        else:
            # 尝试glob模式
            resolved_files.extend(str(f) for f in config_dir.glob(file_pattern))
    
    # 构建全局配置
    global_config = {}
    if 'web' in config_data:
        global_config['web'] = config_data['web']
    if 'target' in config_data:
        global_config['web'] = config_data['target']
    if 'android' in config_data:
        global_config['android'] = config_data['android']
    if 'ios' in config_data:
        global_config['ios'] = config_data['ios']
    
    return BatchRunnerConfig(
        files=resolved_files,
        concurrent=options.get('concurrent', config_data.get('concurrent', 1)),
        continue_on_error=options.get('continue_on_error', config_data.get('continueOnError', False)),
        summary=options.get('summary', config_data.get('summary', 'summary.json')),
        share_browser_context=options.get('share_browser_context', config_data.get('shareBrowserContext', False)),
        global_config=global_config if global_config else None,
        headed=options.get('headed', config_data.get('headed', False)),
        keep_window=options.get('keep_window', config_data.get('keepWindow', False)),
        dotenv_override=options.get('dotenv_override', False),
        dotenv_debug=options.get('dotenv_debug', False),
    )


async def create_files_config(
    files: List[str],
    options: Optional[Dict[str, Any]] = None
) -> BatchRunnerConfig:
    """从文件列表创建执行器配置
    
    Args:
        files: 文件列表
        options: 命令行选项
        
    Returns:
        BatchRunnerConfig实例
    """
    options = options or {}
    
    # 解析文件路径
    resolved_files = []
    for file_path in files:
        path = Path(file_path)
        if path.is_file():
            resolved_files.append(str(path))
        elif path.is_dir():
            for ext in ('*.yaml', '*.yml'):
                resolved_files.extend(str(f) for f in path.glob(ext))
    
    # 构建全局配置
    global_config = {}
    
    # 从选项中提取web配置
    if options.get('web'):
        global_config['web'] = {}
    
    return BatchRunnerConfig(
        files=resolved_files,
        concurrent=options.get('concurrent', 1),
        continue_on_error=options.get('continue_on_error', False),
        summary=options.get('summary', 'summary.json'),
        share_browser_context=options.get('share_browser_context', False),
        global_config=global_config if global_config else None,
        headed=options.get('headed', False),
        keep_window=options.get('keep_window', False),
        dotenv_override=options.get('dotenv_override', False),
        dotenv_debug=options.get('dotenv_debug', False),
    )
