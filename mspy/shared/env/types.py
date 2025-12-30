# -*- coding: utf-8 -*-
"""
类型定义
定义模型配置相关的类型。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Literal, Optional


# VL 模式类型
TVlModeTypes = Literal[
    "qwen2.5-vl",
    "qwen3-vl", 
    "doubao-vision",
    "gemini",
    "vlm-ui-tars"
]

# VL 模式原始值
TVlModeValues = Literal[
    "qwen2.5-vl",
    "qwen3-vl",
    "doubao-vision",
    "gemini",
    "vlm-ui-tars",
    "vlm-ui-tars-doubao",
    "vlm-ui-tars-doubao-1.5"
]

# 意图类型
TIntent = Literal["insight", "planning", "default"]

# UI-Tars 模型版本
class UITarsModelVersion:
    V1_0 = "1.0"
    V1_5 = "1.5"
    DOUBAO_1_5_15B = "doubao-1.5-15B"
    DOUBAO_1_5_20B = "doubao-1.5-20B"


# 模型配置类型（环境变量风格）
TModelConfig = Dict[str, str | int]


# OpenAI 客户端创建函数类型
CreateOpenAIClientFn = Callable[[Any, Dict[str, Any]], Any]


@dataclass
class IModelConfig:
    """模型配置接口"""
    # 模型名称
    model_name: str
    # 模型描述
    model_description: str
    # 意图
    intent: TIntent
    
    # 代理设置
    socks_proxy: Optional[str] = None
    http_proxy: Optional[str] = None
    
    # OpenAI 配置
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_extra_config: Optional[Dict[str, Any]] = None
    
    # 超时设置（毫秒）
    timeout: Optional[int] = None
    
    # 温度设置
    temperature: Optional[float] = None
    
    # VL 模式设置
    vl_mode_raw: Optional[str] = None
    vl_mode: Optional[TVlModeTypes] = None
    ui_tars_model_version: Optional[str] = None
    
    # 自定义 OpenAI 客户端工厂函数
    create_openai_client: Optional[CreateOpenAIClientFn] = None
