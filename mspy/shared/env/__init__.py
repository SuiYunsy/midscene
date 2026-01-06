"""
环境配置模块

从 packages/shared/src/env/ 迁移
"""

from mspy.shared.env.types import (
    # 常量
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_BASE_URL,
    MIDSCENE_MODEL_SOCKS_PROXY,
    MIDSCENE_MODEL_HTTP_PROXY,
    MIDSCENE_MODEL_MAX_TOKENS,
    MIDSCENE_MODEL_TIMEOUT,
    MIDSCENE_MODEL_TEMPERATURE,
    MIDSCENE_MODEL_FAMILY,
    MIDSCENE_MODEL_INIT_CONFIG_JSON,
    MIDSCENE_DEBUG_MODE,
    MIDSCENE_RUN_DIR,
    MIDSCENE_CACHE,
    MIDSCENE_FORCE_DEEP_THINK,
    MIDSCENE_PREFERRED_LANGUAGE,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
    # 类型
    VLModeType,
    ModelIntent,
    ModelConfig,
)
from mspy.shared.env.config_manager import (
    GlobalConfigManager,
    ModelConfigManager,
    global_config_manager,
    global_model_config_manager,
    override_ai_config,
    get_preferred_language,
)

__all__ = [
    # 常量
    "MIDSCENE_MODEL_NAME",
    "MIDSCENE_MODEL_API_KEY",
    "MIDSCENE_MODEL_BASE_URL",
    "MIDSCENE_MODEL_SOCKS_PROXY",
    "MIDSCENE_MODEL_HTTP_PROXY",
    "MIDSCENE_MODEL_MAX_TOKENS",
    "MIDSCENE_MODEL_TIMEOUT",
    "MIDSCENE_MODEL_TEMPERATURE",
    "MIDSCENE_MODEL_FAMILY",
    "MIDSCENE_MODEL_INIT_CONFIG_JSON",
    "MIDSCENE_DEBUG_MODE",
    "MIDSCENE_RUN_DIR",
    "MIDSCENE_CACHE",
    "MIDSCENE_FORCE_DEEP_THINK",
    "MIDSCENE_PREFERRED_LANGUAGE",
    "MIDSCENE_REPLANNING_CYCLE_LIMIT",
    # 类型
    "VLModeType",
    "ModelIntent",
    "ModelConfig",
    # 管理器
    "GlobalConfigManager",
    "ModelConfigManager",
    "global_config_manager",
    "global_model_config_manager",
    "override_ai_config",
    "get_preferred_language",
]
