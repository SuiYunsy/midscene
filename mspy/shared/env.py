# -*- coding: utf-8 -*-
"""
Midscene Environment Configuration Module
环境配置模块，管理环境变量和模型配置
"""

import os
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass, field

# ==================== Environment Variable Keys ====================

# 模型配置 - 主要变量
MIDSCENE_MODEL_NAME = "MIDSCENE_MODEL_NAME"
MIDSCENE_MODEL_BASE_URL = "MIDSCENE_MODEL_BASE_URL"
MIDSCENE_MODEL_API_KEY = "MIDSCENE_MODEL_API_KEY"
MIDSCENE_MODEL_HTTP_PROXY = "MIDSCENE_MODEL_HTTP_PROXY"
MIDSCENE_MODEL_TIMEOUT = "MIDSCENE_MODEL_TIMEOUT"
MIDSCENE_MODEL_TEMPERATURE = "MIDSCENE_MODEL_TEMPERATURE"
MIDSCENE_MODEL_MAX_TOKENS = "MIDSCENE_MODEL_MAX_TOKENS"
MIDSCENE_MODEL_FAMILY = "MIDSCENE_MODEL_FAMILY"
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION = "MIDSCENE_MODEL_SKIP_CERT_VERIFICATION"

# 全局配置
MIDSCENE_REPLANNING_CYCLE_LIMIT = "MIDSCENE_REPLANNING_CYCLE_LIMIT"
MIDSCENE_FORCE_DEEP_THINK = "MIDSCENE_FORCE_DEEP_THINK"
MIDSCENE_DEBUG_MODE = "MIDSCENE_DEBUG_MODE"

# Insight模型配置
MIDSCENE_INSIGHT_MODEL_NAME = "MIDSCENE_INSIGHT_MODEL_NAME"
MIDSCENE_INSIGHT_MODEL_BASE_URL = "MIDSCENE_INSIGHT_MODEL_BASE_URL"
MIDSCENE_INSIGHT_MODEL_API_KEY = "MIDSCENE_INSIGHT_MODEL_API_KEY"
MIDSCENE_INSIGHT_MODEL_HTTP_PROXY = "MIDSCENE_INSIGHT_MODEL_HTTP_PROXY"
MIDSCENE_INSIGHT_MODEL_TIMEOUT = "MIDSCENE_INSIGHT_MODEL_TIMEOUT"
MIDSCENE_INSIGHT_MODEL_TEMPERATURE = "MIDSCENE_INSIGHT_MODEL_TEMPERATURE"

# Planning模型配置
MIDSCENE_PLANNING_MODEL_NAME = "MIDSCENE_PLANNING_MODEL_NAME"
MIDSCENE_PLANNING_MODEL_BASE_URL = "MIDSCENE_PLANNING_MODEL_BASE_URL"
MIDSCENE_PLANNING_MODEL_API_KEY = "MIDSCENE_PLANNING_MODEL_API_KEY"
MIDSCENE_PLANNING_MODEL_HTTP_PROXY = "MIDSCENE_PLANNING_MODEL_HTTP_PROXY"
MIDSCENE_PLANNING_MODEL_TIMEOUT = "MIDSCENE_PLANNING_MODEL_TIMEOUT"
MIDSCENE_PLANNING_MODEL_TEMPERATURE = "MIDSCENE_PLANNING_MODEL_TEMPERATURE"


# ==================== VL Mode Types ====================

# 支持的VL模式类型 - 目前只支持qwen3-vl
VLModeType = Literal["qwen3-vl"]


# ==================== Model Intent ====================

IntentType = Literal["insight", "planning", "default"]


# ==================== Model Configuration ====================

@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    openai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    http_proxy: Optional[str] = None
    timeout: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    vl_mode: Optional[VLModeType] = None
    skip_cert_verification: bool = False
    intent: IntentType = "default"
    model_description: str = ""
    extra_config: Dict[str, Any] = field(default_factory=dict)


def get_env_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    获取环境变量值
    
    Args:
        key: 环境变量名
        default: 默认值
    
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    获取布尔类型环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
    
    Returns:
        布尔值
    """
    value = get_env_config(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    获取整数类型环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
    
    Returns:
        整数值或默认值
    """
    value = get_env_config(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(key: str, default: Optional[float] = None) -> Optional[float]:
    """
    获取浮点数类型环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
    
    Returns:
        浮点数值或默认值
    """
    value = get_env_config(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _determine_vl_mode(family: Optional[str]) -> Optional[VLModeType]:
    """
    根据模型家族确定VL模式
    目前只支持qwen3-vl
    """
    if family == "qwen3-vl":
        return "qwen3-vl"
    return None


def get_model_config(intent: IntentType = "default") -> ModelConfig:
    """
    获取模型配置
    
    Args:
        intent: 模型意图，可选 "insight", "planning", "default"
    
    Returns:
        ModelConfig实例
    """
    # 根据intent获取对应的环境变量前缀
    if intent == "insight":
        name_key = MIDSCENE_INSIGHT_MODEL_NAME
        url_key = MIDSCENE_INSIGHT_MODEL_BASE_URL
        key_key = MIDSCENE_INSIGHT_MODEL_API_KEY
        proxy_key = MIDSCENE_INSIGHT_MODEL_HTTP_PROXY
        timeout_key = MIDSCENE_INSIGHT_MODEL_TIMEOUT
        temp_key = MIDSCENE_INSIGHT_MODEL_TEMPERATURE
    elif intent == "planning":
        name_key = MIDSCENE_PLANNING_MODEL_NAME
        url_key = MIDSCENE_PLANNING_MODEL_BASE_URL
        key_key = MIDSCENE_PLANNING_MODEL_API_KEY
        proxy_key = MIDSCENE_PLANNING_MODEL_HTTP_PROXY
        timeout_key = MIDSCENE_PLANNING_MODEL_TIMEOUT
        temp_key = MIDSCENE_PLANNING_MODEL_TEMPERATURE
    else:
        name_key = MIDSCENE_MODEL_NAME
        url_key = MIDSCENE_MODEL_BASE_URL
        key_key = MIDSCENE_MODEL_API_KEY
        proxy_key = MIDSCENE_MODEL_HTTP_PROXY
        timeout_key = MIDSCENE_MODEL_TIMEOUT
        temp_key = MIDSCENE_MODEL_TEMPERATURE
    
    # 获取配置值，如果特定intent没有配置则回退到默认配置
    model_name = get_env_config(name_key) or get_env_config(MIDSCENE_MODEL_NAME) or ""
    base_url = get_env_config(url_key) or get_env_config(MIDSCENE_MODEL_BASE_URL)
    api_key = get_env_config(key_key) or get_env_config(MIDSCENE_MODEL_API_KEY)
    http_proxy = get_env_config(proxy_key) or get_env_config(MIDSCENE_MODEL_HTTP_PROXY)
    timeout = get_env_int(timeout_key) or get_env_int(MIDSCENE_MODEL_TIMEOUT)
    temperature = get_env_float(temp_key) or get_env_float(MIDSCENE_MODEL_TEMPERATURE)
    max_tokens = get_env_int(MIDSCENE_MODEL_MAX_TOKENS)
    skip_cert = get_env_bool(MIDSCENE_MODEL_SKIP_CERT_VERIFICATION, False)
    
    # 获取模型家族
    family = get_env_config(MIDSCENE_MODEL_FAMILY)
    vl_mode = _determine_vl_mode(family)
    
    # 构建模型描述
    model_desc = f"{model_name}"
    if base_url:
        model_desc = f"{model_name} @ {base_url}"
    
    return ModelConfig(
        model_name=model_name,
        openai_base_url=base_url,
        openai_api_key=api_key,
        http_proxy=http_proxy,
        timeout=timeout,
        temperature=temperature,
        max_tokens=max_tokens,
        vl_mode=vl_mode,
        skip_cert_verification=skip_cert,
        intent=intent,
        model_description=model_desc,
    )


class GlobalConfigManager:
    """全局配置管理器"""
    
    _instance: Optional["GlobalConfigManager"] = None
    _config_override: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_env_value(self, key: str) -> Optional[str]:
        """获取环境变量值，优先使用覆盖配置"""
        if key in self._config_override:
            return self._config_override[key]
        return os.environ.get(key)
    
    def get_env_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型环境变量"""
        value = self.get_env_value(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    def override_config(self, config: Dict[str, str]) -> None:
        """覆盖配置"""
        self._config_override.update(config)
    
    def reset_override(self) -> None:
        """重置覆盖配置"""
        self._config_override.clear()


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(
        self,
        model_config: Optional[Dict[str, str]] = None,
    ):
        self._model_config = model_config or {}
    
    def get_model_config(self, intent: IntentType = "default") -> ModelConfig:
        """获取指定意图的模型配置"""
        # 先获取环境变量配置
        config = get_model_config(intent)
        
        # 用传入的配置覆盖
        if self._model_config:
            if MIDSCENE_MODEL_NAME in self._model_config:
                config.model_name = self._model_config[MIDSCENE_MODEL_NAME]
            if MIDSCENE_MODEL_BASE_URL in self._model_config:
                config.openai_base_url = self._model_config[MIDSCENE_MODEL_BASE_URL]
            if MIDSCENE_MODEL_API_KEY in self._model_config:
                config.openai_api_key = self._model_config[MIDSCENE_MODEL_API_KEY]
            if MIDSCENE_MODEL_HTTP_PROXY in self._model_config:
                config.http_proxy = self._model_config[MIDSCENE_MODEL_HTTP_PROXY]
        
        return config


# 全局配置管理器实例
global_config_manager = GlobalConfigManager()
global_model_config_manager = ModelConfigManager()
