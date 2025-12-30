"""
AI模型类型定义
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

# AI动作类型
class AIActionType(Enum):
    """AI动作类型枚举"""
    LOCATE_ELEMENT = "locate_element"
    EXTRACT_DATA = "extract_data"
    DESCRIBE_ELEMENT = "describe_element"
    ASSERT = "assert"
    PLAN = "plan"


# AI参数类型 - 消息列表
AIArgs = List[Dict[str, Any]]
