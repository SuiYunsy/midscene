"""
环境配置模块 - 管理Midscene的环境变量和模型配置

对应TypeScript源码: packages/shared/src/env/
"""

from mspy.shared.env.types import (
    # 配置键常量
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_BASE_URL,
    MIDSCENE_MODEL_TIMEOUT,
    MIDSCENE_MODEL_TEMPERATURE,
    MIDSCENE_MODEL_FAMILY,
    MIDSCENE_DEBUG_MODE,
    MIDSCENE_CACHE,
    MIDSCENE_RUN_DIR,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
    # 类型
    TIntent,
    TModelConfig,
    IModelConfig,
    TVlModeTypes,
)
from mspy.shared.env.model_config_manager import ModelConfigManager
from mspy.shared.env.global_config_manager import GlobalConfigManager

# 全局配置管理器实例
global_config_manager = GlobalConfigManager()
global_model_config_manager = ModelConfigManager()

__all__ = [
    # 配置键
    "MIDSCENE_MODEL_NAME",
    "MIDSCENE_MODEL_API_KEY",
    "MIDSCENE_MODEL_BASE_URL",
    "MIDSCENE_MODEL_TIMEOUT",
    "MIDSCENE_MODEL_TEMPERATURE",
    "MIDSCENE_MODEL_FAMILY",
    "MIDSCENE_DEBUG_MODE",
    "MIDSCENE_CACHE",
    "MIDSCENE_RUN_DIR",
    "MIDSCENE_REPLANNING_CYCLE_LIMIT",
    # 类型
    "TIntent",
    "TModelConfig",
    "IModelConfig",
    "TVlModeTypes",
    # 管理器
    "ModelConfigManager",
    "GlobalConfigManager",
    "global_config_manager",
    "global_model_config_manager",
]
