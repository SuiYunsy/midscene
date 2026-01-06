"""
环境变量配置模块
Environment configuration module
"""
import os
from typing import Optional, Dict, Any, List

# 核心配置键
MIDSCENE_MODEL_NAME = "MIDSCENE_MODEL_NAME"
MIDSCENE_MODEL_API_KEY = "MIDSCENE_MODEL_API_KEY"
MIDSCENE_MODEL_BASE_URL = "MIDSCENE_MODEL_BASE_URL"
MIDSCENE_MODEL_FAMILY = "MIDSCENE_MODEL_FAMILY"
MIDSCENE_MODEL_MAX_TOKENS = "MIDSCENE_MODEL_MAX_TOKENS"
MIDSCENE_MODEL_TIMEOUT = "MIDSCENE_MODEL_TIMEOUT"
MIDSCENE_MODEL_TEMPERATURE = "MIDSCENE_MODEL_TEMPERATURE"

# 代理配置
MIDSCENE_MODEL_SOCKS_PROXY = "MIDSCENE_MODEL_SOCKS_PROXY"
MIDSCENE_MODEL_HTTP_PROXY = "MIDSCENE_MODEL_HTTP_PROXY"

# 调试和基础配置
MIDSCENE_DEBUG_MODE = "MIDSCENE_DEBUG_MODE"
MIDSCENE_RUN_DIR = "MIDSCENE_RUN_DIR"
MIDSCENE_FORCE_DEEP_THINK = "MIDSCENE_FORCE_DEEP_THINK"

# 重规划限制
MIDSCENE_REPLANNING_CYCLE_LIMIT = "MIDSCENE_REPLANNING_CYCLE_LIMIT"

# INSIGHT 配置
MIDSCENE_INSIGHT_MODEL_NAME = "MIDSCENE_INSIGHT_MODEL_NAME"
MIDSCENE_INSIGHT_MODEL_BASE_URL = "MIDSCENE_INSIGHT_MODEL_BASE_URL"
MIDSCENE_INSIGHT_MODEL_API_KEY = "MIDSCENE_INSIGHT_MODEL_API_KEY"
MIDSCENE_INSIGHT_MODEL_HTTP_PROXY = "MIDSCENE_INSIGHT_MODEL_HTTP_PROXY"
MIDSCENE_INSIGHT_MODEL_TIMEOUT = "MIDSCENE_INSIGHT_MODEL_TIMEOUT"
MIDSCENE_INSIGHT_MODEL_TEMPERATURE = "MIDSCENE_INSIGHT_MODEL_TEMPERATURE"

# PLANNING 配置
MIDSCENE_PLANNING_MODEL_NAME = "MIDSCENE_PLANNING_MODEL_NAME"
MIDSCENE_PLANNING_MODEL_BASE_URL = "MIDSCENE_PLANNING_MODEL_BASE_URL"
MIDSCENE_PLANNING_MODEL_API_KEY = "MIDSCENE_PLANNING_MODEL_API_KEY"
MIDSCENE_PLANNING_MODEL_HTTP_PROXY = "MIDSCENE_PLANNING_MODEL_HTTP_PROXY"
MIDSCENE_PLANNING_MODEL_TIMEOUT = "MIDSCENE_PLANNING_MODEL_TIMEOUT"
MIDSCENE_PLANNING_MODEL_TEMPERATURE = "MIDSCENE_PLANNING_MODEL_TEMPERATURE"

# VL 模式配置
VL_MODE_VALUES = [
    "qwen2.5-vl",
    "qwen3-vl",
    "doubao-vision",
    "gemini",
    "vlm-ui-tars",
]

# 模型意图类型
INTENT_DEFAULT = "default"
INTENT_INSIGHT = "insight"
INTENT_PLANNING = "planning"


class ModelConfig:
    """
    Model configuration class.
    模型配置类
    """
    
    def __init__(
        self,
        model_name: str,
        openai_base_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        http_proxy: Optional[str] = None,
        socks_proxy: Optional[str] = None,
        timeout: Optional[int] = None,
        temperature: float = 0.0,
        vl_mode: Optional[str] = None,
        intent: str = INTENT_DEFAULT,
        model_description: str = "",
    ):
        self.model_name = model_name
        self.openai_base_url = openai_base_url
        self.openai_api_key = openai_api_key
        self.http_proxy = http_proxy
        self.socks_proxy = socks_proxy
        self.timeout = timeout
        self.temperature = temperature
        self.vl_mode = vl_mode
        self.intent = intent
        self.model_description = model_description


def get_env_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable value.
    获取环境变量值
    """
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get environment variable as boolean.
    获取布尔类型的环境变量
    """
    value = os.environ.get(key, "")
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    return default


def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """
    Get environment variable as integer.
    获取整数类型的环境变量
    """
    value = os.environ.get(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass
    return default


def model_family_to_vl_config(model_family: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Convert model family to VL configuration.
    将模型家族转换为VL配置
    """
    if not model_family:
        return {"vl_mode": None}
    
    if model_family in VL_MODE_VALUES:
        return {"vl_mode": model_family}
    
    return {"vl_mode": None}


class ModelConfigManager:
    """
    Model configuration manager.
    模型配置管理器
    """
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self._model_config = model_config or {}
        self._config_map: Optional[Dict[str, ModelConfig]] = None
        self._initialized = False
    
    def _get_config_value(self, key: str) -> Optional[str]:
        """Get config value from model_config or environment."""
        if key in self._model_config:
            value = self._model_config[key]
            return str(value) if value is not None else None
        return get_env_value(key)
    
    def _initialize(self) -> None:
        """Initialize model configurations."""
        if self._initialized:
            return
        
        # 获取默认配置
        default_config = self._build_config(INTENT_DEFAULT)
        if not default_config:
            raise ValueError(
                "Default model config not found. "
                "Please set MIDSCENE_MODEL_NAME and MIDSCENE_MODEL_BASE_URL."
            )
        
        # 获取 insight 配置
        insight_config = self._build_config(INTENT_INSIGHT) or default_config
        
        # 获取 planning 配置
        planning_config = self._build_config(INTENT_PLANNING) or default_config
        
        self._config_map = {
            INTENT_DEFAULT: default_config,
            INTENT_INSIGHT: insight_config,
            INTENT_PLANNING: planning_config,
        }
        
        self._initialized = True
    
    def _build_config(self, intent: str) -> Optional[ModelConfig]:
        """Build model config for specific intent."""
        if intent == INTENT_DEFAULT:
            name_key = MIDSCENE_MODEL_NAME
            base_url_key = MIDSCENE_MODEL_BASE_URL
            api_key_key = MIDSCENE_MODEL_API_KEY
            http_proxy_key = MIDSCENE_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_MODEL_TIMEOUT
            temperature_key = MIDSCENE_MODEL_TEMPERATURE
            family_key = MIDSCENE_MODEL_FAMILY
        elif intent == INTENT_INSIGHT:
            name_key = MIDSCENE_INSIGHT_MODEL_NAME
            base_url_key = MIDSCENE_INSIGHT_MODEL_BASE_URL
            api_key_key = MIDSCENE_INSIGHT_MODEL_API_KEY
            http_proxy_key = MIDSCENE_INSIGHT_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_INSIGHT_MODEL_TIMEOUT
            temperature_key = MIDSCENE_INSIGHT_MODEL_TEMPERATURE
            family_key = MIDSCENE_MODEL_FAMILY
        elif intent == INTENT_PLANNING:
            name_key = MIDSCENE_PLANNING_MODEL_NAME
            base_url_key = MIDSCENE_PLANNING_MODEL_BASE_URL
            api_key_key = MIDSCENE_PLANNING_MODEL_API_KEY
            http_proxy_key = MIDSCENE_PLANNING_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_PLANNING_MODEL_TIMEOUT
            temperature_key = MIDSCENE_PLANNING_MODEL_TEMPERATURE
            family_key = MIDSCENE_MODEL_FAMILY
        else:
            return None
        
        model_name = self._get_config_value(name_key)
        if not model_name:
            return None
        
        base_url = self._get_config_value(base_url_key)
        api_key = self._get_config_value(api_key_key)
        http_proxy = self._get_config_value(http_proxy_key)
        
        timeout_str = self._get_config_value(timeout_key)
        timeout = int(timeout_str) if timeout_str else None
        
        temp_str = self._get_config_value(temperature_key)
        temperature = float(temp_str) if temp_str else 0.0
        
        model_family = self._get_config_value(family_key)
        vl_config = model_family_to_vl_config(model_family)
        
        return ModelConfig(
            model_name=model_name,
            openai_base_url=base_url,
            openai_api_key=api_key,
            http_proxy=http_proxy,
            timeout=timeout,
            temperature=temperature,
            vl_mode=vl_config.get("vl_mode"),
            intent=intent,
            model_description=f"{vl_config.get('vl_mode') or 'default'} mode",
        )
    
    def get_model_config(self, intent: str) -> ModelConfig:
        """
        Get model configuration for specific intent.
        获取特定意图的模型配置
        """
        if not self._initialized:
            self._initialize()
        
        if self._config_map is None:
            raise ValueError("Model config map not initialized")
        
        return self._config_map.get(intent, self._config_map[INTENT_DEFAULT])
    
    def throw_error_if_non_vl_model(self) -> None:
        """
        Throw error if model is not a VL model.
        如果模型不是VL模型则抛出错误
        """
        config = self.get_model_config(INTENT_DEFAULT)
        if not config.vl_mode:
            raise ValueError(
                "MIDSCENE_MODEL_FAMILY is not set to a visual language model. "
                "The element localization cannot be achieved. "
                "See https://midscenejs.com/model-strategy.html"
            )


# 全局配置管理器
_global_model_config_manager: Optional[ModelConfigManager] = None


def get_global_model_config_manager() -> ModelConfigManager:
    """Get global model config manager."""
    global _global_model_config_manager
    if _global_model_config_manager is None:
        _global_model_config_manager = ModelConfigManager()
    return _global_model_config_manager


def set_global_model_config_manager(manager: ModelConfigManager) -> None:
    """Set global model config manager."""
    global _global_model_config_manager
    _global_model_config_manager = manager
