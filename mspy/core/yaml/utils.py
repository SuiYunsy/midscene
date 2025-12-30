# -*- coding: utf-8 -*-
"""
YAML 脚本解析和播放模块
提供 YAML 脚本的解析和执行功能。
"""

import os
import re
from typing import Any, Dict, List, Optional, Union

import yaml

from mspy.shared.types import (
    MidsceneYamlScript,
    MidsceneYamlTask,
    MidsceneYamlFlowItem,
    DetailedLocateParam,
)
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition


debug = get_debug("yaml:utils")


def interpolate_env_vars(content: str) -> str:
    """
    插值环境变量
    处理 ${VAR_NAME} 格式的环境变量引用
    
    Args:
        content: YAML 内容
        
    Returns:
        替换环境变量后的内容
    """
    lines = content.split('\n')
    processed_lines = []
    
    for line in lines:
        # 跳过注释行
        trimmed_line = line.lstrip()
        if trimmed_line.startswith('#'):
            processed_lines.append(line)
            continue
        
        # 处理环境变量
        def replace_env(match):
            env_var = match.group(1).strip()
            value = os.environ.get(env_var)
            if value is None:
                raise ValueError(f'Environment variable "{env_var}" is not defined')
            return value
        
        processed_line = re.sub(r'\$\{([^}]+)\}', replace_env, line)
        processed_lines.append(processed_line)
    
    return '\n'.join(processed_lines)


def parse_yaml_script(content: str, file_path: Optional[str] = None) -> MidsceneYamlScript:
    """
    解析 YAML 脚本
    
    Args:
        content: YAML 内容
        file_path: 文件路径（用于错误提示）
        
    Returns:
        解析后的脚本对象
    """
    processed_content = content
    
    # 处理 Android deviceId（确保为字符串格式）
    if 'android' in content:
        device_id_match = re.search(r'deviceId:\s*(\d+)', content)
        if device_id_match:
            matched_id = device_id_match.group(1)
            processed_content = re.sub(
                r'deviceId:\s*(\d+)',
                lambda m: f"deviceId: '{m.group(1)}'",
                content
            )
            print(f'Warning: please use string-style deviceId in yaml script, for example: deviceId: "{matched_id}"')
    
    # 插值环境变量
    interpolated_content = interpolate_env_vars(processed_content)
    
    # 解析 YAML
    obj = yaml.safe_load(interpolated_content)
    
    path_tip = f", failed to load {file_path}" if file_path else ""
    
    assert_condition(
        obj.get('tasks'),
        f'property "tasks" is required in yaml script{path_tip}'
    )
    assert_condition(
        isinstance(obj.get('tasks'), list),
        f'property "tasks" must be an array in yaml script, but got {obj.get("tasks")}'
    )
    
    # 构建脚本对象
    tasks = []
    for task_data in obj.get('tasks', []):
        flow = []
        for flow_item in task_data.get('flow', []):
            flow.append(MidsceneYamlFlowItem(data=flow_item))
        
        task = MidsceneYamlTask(
            name=task_data.get('name', 'Unnamed Task'),
            flow=flow,
            continue_on_error=task_data.get('continueOnError', False),
        )
        tasks.append(task)
    
    return MidsceneYamlScript(
        tasks=tasks,
        target=obj.get('target'),
        web=obj.get('web'),
        android=obj.get('android'),
        ios=obj.get('ios'),
        agent=obj.get('agent'),
    )


def build_detailed_locate_param(
    locate_prompt: Union[str, Dict[str, Any]],
    opt: Optional[Dict[str, Any]] = None
) -> Optional[DetailedLocateParam]:
    """
    构建详细定位参数
    
    Args:
        locate_prompt: 定位提示
        opt: 额外选项
        
    Returns:
        详细定位参数或 None
    """
    debug(f"will call build_detailed_locate_param {locate_prompt} {opt}")
    
    # 获取 prompt
    if isinstance(locate_prompt, str):
        prompt = locate_prompt
    elif isinstance(locate_prompt, dict):
        prompt = locate_prompt.get('prompt', '')
    else:
        prompt = ""
    
    # 从选项中获取
    if not prompt and opt:
        prompt = opt.get('prompt') or opt.get('locate', '')
    
    deep_think = False
    cacheable = True
    xpath = None
    
    if opt and isinstance(opt, dict):
        deep_think = opt.get('deepThink', opt.get('deep_think', False))
        cacheable = opt.get('cacheable', True)
        xpath = opt.get('xpath')
        
        # 检查冲突的 prompt
        if prompt and opt.get('prompt') and prompt != opt.get('prompt'):
            print(f"Warning: conflict prompt for item {locate_prompt} {opt}, maybe you put the prompt in the wrong place")
        
        prompt = prompt or opt.get('prompt', '')
    
    if not prompt:
        debug(f"no prompt, will return None in build_detailed_locate_param {opt}")
        return None
    
    return DetailedLocateParam(
        prompt=prompt,
        deep_think=deep_think,
        cacheable=cacheable,
        xpath=xpath,
    )


def build_detailed_locate_param_and_rest_params(
    locate_prompt: Union[str, Dict[str, Any]],
    opt: Optional[Dict[str, Any]],
    exclude_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    构建详细定位参数并提取其他参数
    
    Args:
        locate_prompt: 定位提示
        opt: 额外选项
        exclude_keys: 要排除的键
        
    Returns:
        包含 locate_param 和 rest_params 的字典
    """
    exclude_keys = exclude_keys or []
    locate_param = build_detailed_locate_param(locate_prompt, opt)
    
    rest_params = {}
    
    if opt and isinstance(opt, dict):
        # 获取 locate_param 中的键
        locate_param_keys = []
        if locate_param:
            locate_param_keys = ['prompt', 'deepThink', 'deep_think', 'cacheable', 'xpath']
        
        # 提取其他键
        for key, value in opt.items():
            if key not in locate_param_keys and key not in exclude_keys and key != 'locate':
                rest_params[key] = value
    
    return {
        'locate_param': locate_param,
        'rest_params': rest_params,
    }
