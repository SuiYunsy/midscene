# -*- coding: utf-8 -*-
"""
环境配置模块
提供环境变量和模型配置管理功能。
"""

import os
from typing import Optional

from .constants import (
    MIDSCENE_PREFERRED_LANGUAGE,
    ALL_ENV_KEYS,
    BASIC_ENV_KEYS,
    BOOLEAN_ENV_KEYS,
    NUMBER_ENV_KEYS,
    STRING_ENV_KEYS,
    GLOBAL_ENV_KEYS,
    MODEL_ENV_KEYS,
)
from .types import (
    IModelConfig,
    TModelConfig,
    TVlModeTypes,
    CreateOpenAIClientFn,
)
from .global_config_manager import GlobalConfigManager, global_config_manager
from .model_config_manager import ModelConfigManager, global_model_config_manager

# 注册相互引用
global_config_manager.register_model_config_manager(global_model_config_manager)
global_model_config_manager.register_global_config_manager(global_config_manager)


def get_preferred_language() -> str:
    """
    获取首选语言设置
    
    Returns:
        首选语言字符串，默认为 "English"
    """
    return os.environ.get(MIDSCENE_PREFERRED_LANGUAGE, "English")


__all__ = [
    # 配置管理器
    "GlobalConfigManager",
    "ModelConfigManager",
    "global_config_manager",
    "global_model_config_manager",
    # 类型
    "IModelConfig",
    "TModelConfig",
    "TVlModeTypes",
    "CreateOpenAIClientFn",
    # 常量
    "ALL_ENV_KEYS",
    "BASIC_ENV_KEYS",
    "BOOLEAN_ENV_KEYS",
    "NUMBER_ENV_KEYS",
    "STRING_ENV_KEYS",
    "GLOBAL_ENV_KEYS",
    "MODEL_ENV_KEYS",
    # 函数
    "get_preferred_language",
]
