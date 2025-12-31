"""
环境变量和配置管理模块
Environment variables and configuration management
"""
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

# 配置键常量
MIDSCENE_MODEL_NAME = "MIDSCENE_MODEL_NAME"
MIDSCENE_MODEL_API_KEY = "MIDSCENE_MODEL_API_KEY"
MIDSCENE_MODEL_BASE_URL = "MIDSCENE_MODEL_BASE_URL"
MIDSCENE_MODEL_HTTP_PROXY = "MIDSCENE_MODEL_HTTP_PROXY"
MIDSCENE_MODEL_TIMEOUT = "MIDSCENE_MODEL_TIMEOUT"
MIDSCENE_MODEL_TEMPERATURE = "MIDSCENE_MODEL_TEMPERATURE"
MIDSCENE_MODEL_FAMILY = "MIDSCENE_MODEL_FAMILY"
MIDSCENE_MODEL_INIT_CONFIG_JSON = "MIDSCENE_MODEL_INIT_CONFIG_JSON"
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION = "MIDSCENE_MODEL_SKIP_CERT_VERIFICATION"
MIDSCENE_MODEL_MAX_TOKENS = "MIDSCENE_MODEL_MAX_TOKENS"

# Planning 模型配置
MIDSCENE_PLANNING_MODEL_NAME = "MIDSCENE_PLANNING_MODEL_NAME"
MIDSCENE_PLANNING_MODEL_API_KEY = "MIDSCENE_PLANNING_MODEL_API_KEY"
MIDSCENE_PLANNING_MODEL_BASE_URL = "MIDSCENE_PLANNING_MODEL_BASE_URL"
MIDSCENE_PLANNING_MODEL_HTTP_PROXY = "MIDSCENE_PLANNING_MODEL_HTTP_PROXY"
MIDSCENE_PLANNING_MODEL_TIMEOUT = "MIDSCENE_PLANNING_MODEL_TIMEOUT"
MIDSCENE_PLANNING_MODEL_TEMPERATURE = "MIDSCENE_PLANNING_MODEL_TEMPERATURE"
MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON = "MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON"

# Insight 模型配置
MIDSCENE_INSIGHT_MODEL_NAME = "MIDSCENE_INSIGHT_MODEL_NAME"
MIDSCENE_INSIGHT_MODEL_API_KEY = "MIDSCENE_INSIGHT_MODEL_API_KEY"
MIDSCENE_INSIGHT_MODEL_BASE_URL = "MIDSCENE_INSIGHT_MODEL_BASE_URL"
MIDSCENE_INSIGHT_MODEL_HTTP_PROXY = "MIDSCENE_INSIGHT_MODEL_HTTP_PROXY"
MIDSCENE_INSIGHT_MODEL_TIMEOUT = "MIDSCENE_INSIGHT_MODEL_TIMEOUT"
MIDSCENE_INSIGHT_MODEL_TEMPERATURE = "MIDSCENE_INSIGHT_MODEL_TEMPERATURE"
MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON = "MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON"

# 其他配置
MIDSCENE_DEBUG_MODE = "MIDSCENE_DEBUG_MODE"
MIDSCENE_FORCE_DEEP_THINK = "MIDSCENE_FORCE_DEEP_THINK"
MIDSCENE_REPLANNING_CYCLE_LIMIT = "MIDSCENE_REPLANNING_CYCLE_LIMIT"
MIDSCENE_RUN_DIR = "MIDSCENE_RUN_DIR"
MIDSCENE_CACHE = "MIDSCENE_CACHE"

# VL模式有效值
VL_MODE_VALID_VALUES = [
    "qwen2.5-vl",
    "qwen3-vl",
    "doubao-vision",
    "gemini",
    "vlm-ui-tars",
]

# 模型家族有效值（目前只支持qwen3-vl）
MODEL_FAMILY_VALUES = ["qwen3-vl"]


def _parse_bool(value: Optional[str]) -> bool:
    """解析布尔值"""
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


def _parse_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    """解析整数"""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: Optional[str], default: Optional[float] = None) -> Optional[float]:
    """解析浮点数"""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


class GlobalConfigManager:
    """全局配置管理器"""
    
    def __init__(self):
        self._env_config: Dict[str, Optional[str]] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        keys = [
            MIDSCENE_MODEL_NAME,
            MIDSCENE_MODEL_API_KEY,
            MIDSCENE_MODEL_BASE_URL,
            MIDSCENE_MODEL_HTTP_PROXY,
            MIDSCENE_MODEL_TIMEOUT,
            MIDSCENE_MODEL_TEMPERATURE,
            MIDSCENE_MODEL_FAMILY,
            MIDSCENE_MODEL_INIT_CONFIG_JSON,
            MIDSCENE_MODEL_SKIP_CERT_VERIFICATION,
            MIDSCENE_MODEL_MAX_TOKENS,
            MIDSCENE_PLANNING_MODEL_NAME,
            MIDSCENE_PLANNING_MODEL_API_KEY,
            MIDSCENE_PLANNING_MODEL_BASE_URL,
            MIDSCENE_PLANNING_MODEL_HTTP_PROXY,
            MIDSCENE_PLANNING_MODEL_TIMEOUT,
            MIDSCENE_PLANNING_MODEL_TEMPERATURE,
            MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON,
            MIDSCENE_INSIGHT_MODEL_NAME,
            MIDSCENE_INSIGHT_MODEL_API_KEY,
            MIDSCENE_INSIGHT_MODEL_BASE_URL,
            MIDSCENE_INSIGHT_MODEL_HTTP_PROXY,
            MIDSCENE_INSIGHT_MODEL_TIMEOUT,
            MIDSCENE_INSIGHT_MODEL_TEMPERATURE,
            MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON,
            MIDSCENE_DEBUG_MODE,
            MIDSCENE_FORCE_DEEP_THINK,
            MIDSCENE_REPLANNING_CYCLE_LIMIT,
            MIDSCENE_RUN_DIR,
            MIDSCENE_CACHE,
        ]
        for key in keys:
            self._env_config[key] = os.environ.get(key)
    
    def get_env_config_value(self, key: str) -> Optional[str]:
        """获取环境配置值"""
        return self._env_config.get(key) or os.environ.get(key)
    
    def get_env_config_in_boolean(self, key: str) -> bool:
        """获取布尔类型的环境配置"""
        return _parse_bool(self.get_env_config_value(key))
    
    def get_all_env_config(self) -> Dict[str, Optional[str]]:
        """获取所有环境配置"""
        return self._env_config.copy()
    
    def reload(self):
        """重新加载配置"""
        self._load_from_env()


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(
        self, 
        model_config: Optional[Dict[str, Any]] = None
    ):
        self._model_config = model_config or {}
        self._global_config_manager = GlobalConfigManager()
        self._config_cache: Dict[str, Any] = {}
    
    def _get_config_value(self, key: str) -> Optional[str]:
        """获取配置值，优先使用model_config，否则使用环境变量"""
        if key in self._model_config:
            value = self._model_config[key]
            return str(value) if value is not None else None
        return self._global_config_manager.get_env_config_value(key)
    
    def _determine_vl_mode(self, model_family: Optional[str]) -> Optional[str]:
        """确定VL模式"""
        if model_family and model_family in VL_MODE_VALID_VALUES:
            return model_family
        return None
    
    def get_model_config(self, intent: str = "default") -> dict:
        """
        获取模型配置
        
        Args:
            intent: 意图类型 ('default', 'planning', 'insight')
        
        Returns:
            模型配置字典
        """
        from .types import IModelConfig
        
        # 根据意图选择配置键
        if intent == "planning":
            name_key = MIDSCENE_PLANNING_MODEL_NAME
            api_key_key = MIDSCENE_PLANNING_MODEL_API_KEY
            base_url_key = MIDSCENE_PLANNING_MODEL_BASE_URL
            http_proxy_key = MIDSCENE_PLANNING_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_PLANNING_MODEL_TIMEOUT
            temperature_key = MIDSCENE_PLANNING_MODEL_TEMPERATURE
        elif intent == "insight":
            name_key = MIDSCENE_INSIGHT_MODEL_NAME
            api_key_key = MIDSCENE_INSIGHT_MODEL_API_KEY
            base_url_key = MIDSCENE_INSIGHT_MODEL_BASE_URL
            http_proxy_key = MIDSCENE_INSIGHT_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_INSIGHT_MODEL_TIMEOUT
            temperature_key = MIDSCENE_INSIGHT_MODEL_TEMPERATURE
        else:
            name_key = MIDSCENE_MODEL_NAME
            api_key_key = MIDSCENE_MODEL_API_KEY
            base_url_key = MIDSCENE_MODEL_BASE_URL
            http_proxy_key = MIDSCENE_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_MODEL_TIMEOUT
            temperature_key = MIDSCENE_MODEL_TEMPERATURE
        
        # 获取配置值，回退到默认配置
        model_name = (
            self._get_config_value(name_key) or 
            self._get_config_value(MIDSCENE_MODEL_NAME) or
            ""
        )
        api_key = (
            self._get_config_value(api_key_key) or 
            self._get_config_value(MIDSCENE_MODEL_API_KEY) or
            ""
        )
        base_url = (
            self._get_config_value(base_url_key) or 
            self._get_config_value(MIDSCENE_MODEL_BASE_URL) or
            ""
        )
        http_proxy = (
            self._get_config_value(http_proxy_key) or 
            self._get_config_value(MIDSCENE_MODEL_HTTP_PROXY)
        )
        timeout = _parse_int(
            self._get_config_value(timeout_key) or 
            self._get_config_value(MIDSCENE_MODEL_TIMEOUT)
        )
        temperature = _parse_float(
            self._get_config_value(temperature_key) or 
            self._get_config_value(MIDSCENE_MODEL_TEMPERATURE)
        )
        
        # 获取模型家族
        model_family = self._get_config_value(MIDSCENE_MODEL_FAMILY)
        vl_mode = self._determine_vl_mode(model_family)
        
        # 获取是否跳过证书验证
        skip_cert = _parse_bool(
            self._get_config_value(MIDSCENE_MODEL_SKIP_CERT_VERIFICATION)
        )
        
        return IModelConfig(
            model_name=model_name,
            model_description=f"{intent} model",
            intent=intent,
            openai_base_url=base_url,
            openai_api_key=api_key,
            http_proxy=http_proxy,
            timeout=timeout,
            temperature=temperature,
            vl_mode_raw=model_family,
            vl_mode=vl_mode,
            skip_cert_verification=skip_cert,
        )
    
    def throw_error_if_non_vl_model(self):
        """如果不是VL模型则抛出错误"""
        config = self.get_model_config("default")
        if not config.vl_mode:
            supported_modes = ", ".join(f"'{m}'" for m in VL_MODE_VALID_VALUES)
            raise ValueError(
                "MIDSCENE_MODEL_FAMILY is not set to a visual language model (VL model). "
                "The element localization cannot be achieved. "
                f"Please set MIDSCENE_MODEL_FAMILY to one of: {supported_modes}."
            )


# 全局配置管理器实例
global_config_manager = GlobalConfigManager()
global_model_config_manager = ModelConfigManager()
