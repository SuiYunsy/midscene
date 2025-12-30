"""
YAML构建器工具

对应TypeScript源码: packages/core/src/yaml/builder.ts
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from mspy.core.service import DetailedLocateParam


def build_detailed_locate_param(
    prompt: str,
    opts: Optional[Dict[str, Any]] = None
) -> DetailedLocateParam:
    """构建详细定位参数
    
    Args:
        prompt: 定位提示
        opts: 选项
        
    Returns:
        DetailedLocateParam对象
    """
    deep_think = False
    if opts:
        deep_think = opts.get('deep_think', False) or opts.get('deepThink', False)
    
    return DetailedLocateParam(
        prompt=prompt,
        deep_think=deep_think,
    )
