"""
YAML工具函数
"""

from typing import Optional, Any, Dict
from mspy.core.types import DetailedLocateParam, LocateOption


def build_detailed_locate_param(
    prompt: Any,
    opt: Optional[LocateOption] = None,
) -> DetailedLocateParam:
    """
    构建详细定位参数
    
    Args:
        prompt: 用户提示（字符串或包含prompt属性的对象）
        opt: 定位选项
        
    Returns:
        详细定位参数
    """
    if isinstance(prompt, str):
        text_prompt = prompt
    elif hasattr(prompt, "prompt"):
        text_prompt = prompt.prompt
    else:
        text_prompt = str(prompt)
    
    return DetailedLocateParam(
        prompt=text_prompt,
        deep_think=opt.deep_think if opt else False,
        cacheable=opt.cacheable if opt else True,
    )


def build_detailed_locate_param_and_rest_params(
    prompt: str,
    source: Dict[str, Any],
    exclude_keys: list[str],
) -> tuple[Optional[DetailedLocateParam], Dict[str, Any]]:
    """
    构建详细定位参数并提取剩余参数
    
    Args:
        prompt: 提示字符串
        source: 源参数字典
        exclude_keys: 要排除的键列表
        
    Returns:
        (定位参数, 剩余参数)
    """
    # 提取定位相关参数
    deep_think = source.get("deepThink", source.get("deep_think", False))
    cacheable = source.get("cacheable", True)
    
    # 构建定位参数
    locate_param = None
    if prompt:
        locate_param = DetailedLocateParam(
            prompt=prompt,
            deep_think=deep_think,
            cacheable=cacheable,
        )
    
    # 提取剩余参数
    rest_params = {}
    for key, value in source.items():
        if key not in exclude_keys and key not in ("deepThink", "deep_think", "cacheable", "prompt"):
            rest_params[key] = value
    
    return locate_param, rest_params
