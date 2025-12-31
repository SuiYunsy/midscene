"""
公共类型定义
"""

from typing import Union, Literal, Any, List
from pydantic import BaseModel


# 用户提示类型
TUserPrompt = Union[str, "MultimodalPrompt"]


class MultimodalPrompt(BaseModel):
    """多模态提示"""
    prompt: str
    images: List[str] = []  # Base64编码的图像列表


# AI操作类型
AIActionType = Literal[
    "locate",
    "extract", 
    "assert",
    "describe",
    "planning",
    "section_locator",
]
