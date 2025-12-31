"""
环境变量配置模块
"""

import os
from typing import Any, Dict, Optional, Union

# 主要的环境变量配置键
MIDSCENE_MODEL_NAME = 'MIDSCENE_MODEL_NAME'
MIDSCENE_MODEL_API_KEY = 'MIDSCENE_MODEL_API_KEY'
MIDSCENE_MODEL_BASE_URL = 'MIDSCENE_MODEL_BASE_URL'
MIDSCENE_MODEL_HTTP_PROXY = 'MIDSCENE_MODEL_HTTP_PROXY'
MIDSCENE_MODEL_MAX_TOKENS = 'MIDSCENE_MODEL_MAX_TOKENS'
MIDSCENE_MODEL_TIMEOUT = 'MIDSCENE_MODEL_TIMEOUT'
MIDSCENE_MODEL_TEMPERATURE = 'MIDSCENE_MODEL_TEMPERATURE'
MIDSCENE_MODEL_FAMILY = 'MIDSCENE_MODEL_FAMILY'
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION = 'MIDSCENE_MODEL_SKIP_CERT_VERIFICATION'

# Insight 模型配置
MIDSCENE_INSIGHT_MODEL_NAME = 'MIDSCENE_INSIGHT_MODEL_NAME'
MIDSCENE_INSIGHT_MODEL_HTTP_PROXY = 'MIDSCENE_INSIGHT_MODEL_HTTP_PROXY'
MIDSCENE_INSIGHT_MODEL_BASE_URL = 'MIDSCENE_INSIGHT_MODEL_BASE_URL'
MIDSCENE_INSIGHT_MODEL_API_KEY = 'MIDSCENE_INSIGHT_MODEL_API_KEY'
MIDSCENE_INSIGHT_MODEL_TIMEOUT = 'MIDSCENE_INSIGHT_MODEL_TIMEOUT'
MIDSCENE_INSIGHT_MODEL_TEMPERATURE = 'MIDSCENE_INSIGHT_MODEL_TEMPERATURE'

# Planning 模型配置
MIDSCENE_PLANNING_MODEL_NAME = 'MIDSCENE_PLANNING_MODEL_NAME'
MIDSCENE_PLANNING_MODEL_HTTP_PROXY = 'MIDSCENE_PLANNING_MODEL_HTTP_PROXY'
MIDSCENE_PLANNING_MODEL_BASE_URL = 'MIDSCENE_PLANNING_MODEL_BASE_URL'
MIDSCENE_PLANNING_MODEL_API_KEY = 'MIDSCENE_PLANNING_MODEL_API_KEY'
MIDSCENE_PLANNING_MODEL_TIMEOUT = 'MIDSCENE_PLANNING_MODEL_TIMEOUT'
MIDSCENE_PLANNING_MODEL_TEMPERATURE = 'MIDSCENE_PLANNING_MODEL_TEMPERATURE'

# 可观测性
MIDSCENE_DEBUG_MODE = 'MIDSCENE_DEBUG_MODE'

# 重规划限制
MIDSCENE_REPLANNING_CYCLE_LIMIT = 'MIDSCENE_REPLANNING_CYCLE_LIMIT'

# VL模式类型
VL_MODE_TYPES = ['qwen3-vl']  # 目前只支持qwen3-vl

# Model Family 值
MODEL_FAMILY_VALUES = ['qwen3-vl']


class IModelConfig:
    """模型配置接口"""
    
    def __init__(
        self,
        model_name: str,
        openai_base_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        http_proxy: Optional[str] = None,
        timeout: Optional[int] = None,
        temperature: float = 0.0,
        vl_mode: Optional[str] = None,
        model_description: str = "",
        intent: str = "default",
        skip_cert_verification: bool = False,
    ):
        self.model_name = model_name
        self.openai_base_url = openai_base_url
        self.openai_api_key = openai_api_key
        self.http_proxy = http_proxy
        self.timeout = timeout
        self.temperature = temperature
        self.vl_mode = vl_mode
        self.model_description = model_description
        self.intent = intent
        self.skip_cert_verification = skip_cert_verification
    
    def __repr__(self) -> str:
        return (f"IModelConfig(model_name={self.model_name!r}, "
                f"vl_mode={self.vl_mode!r}, intent={self.intent!r})")


def get_env_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量值"""
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔类型的环境变量"""
    value = os.environ.get(key, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    if value in ('false', '0', 'no', 'off'):
        return False
    return default


def get_env_int(key: str, default: Optional[int] = None) -> Optional[int]:
    """获取整数类型的环境变量"""
    value = os.environ.get(key)
    if value is not None:
        try:
            return int(value)
        except ValueError:
            pass
    return default


def get_env_float(key: str, default: Optional[float] = None) -> Optional[float]:
    """获取浮点数类型的环境变量"""
    value = os.environ.get(key)
    if value is not None:
        try:
            return float(value)
        except ValueError:
            pass
    return default


def model_family_to_vl_config(model_family: Optional[str]) -> Dict[str, Optional[str]]:
    """
    将 model family 转换为 VL 配置
    
    Args:
        model_family: 模型家族值
    
    Returns:
        包含 vl_mode 的字典
    """
    if not model_family:
        return {'vl_mode': None}
    
    if model_family == 'qwen3-vl':
        return {'vl_mode': 'qwen3-vl'}
    
    # 检查是否是有效的 model family
    if model_family not in MODEL_FAMILY_VALUES:
        raise ValueError(f"Invalid MIDSCENE_MODEL_FAMILY value: {model_family}")
    
    return {'vl_mode': model_family}


def parse_model_config_for_intent(
    intent: str,
    config_map: Optional[Dict[str, Any]] = None
) -> Optional[IModelConfig]:
    """
    根据 intent 解析模型配置
    
    Args:
        intent: 意图类型 ('default', 'insight', 'planning')
        config_map: 配置映射，如果为None则从环境变量读取
    
    Returns:
        IModelConfig 实例或 None
    """
    if config_map is None:
        config_map = dict(os.environ)
    
    # 根据 intent 确定配置键前缀
    if intent == 'insight':
        prefix = 'MIDSCENE_INSIGHT_MODEL_'
        model_name_key = MIDSCENE_INSIGHT_MODEL_NAME
        base_url_key = MIDSCENE_INSIGHT_MODEL_BASE_URL
        api_key_key = MIDSCENE_INSIGHT_MODEL_API_KEY
        http_proxy_key = MIDSCENE_INSIGHT_MODEL_HTTP_PROXY
        timeout_key = MIDSCENE_INSIGHT_MODEL_TIMEOUT
        temperature_key = MIDSCENE_INSIGHT_MODEL_TEMPERATURE
    elif intent == 'planning':
        prefix = 'MIDSCENE_PLANNING_MODEL_'
        model_name_key = MIDSCENE_PLANNING_MODEL_NAME
        base_url_key = MIDSCENE_PLANNING_MODEL_BASE_URL
        api_key_key = MIDSCENE_PLANNING_MODEL_API_KEY
        http_proxy_key = MIDSCENE_PLANNING_MODEL_HTTP_PROXY
        timeout_key = MIDSCENE_PLANNING_MODEL_TIMEOUT
        temperature_key = MIDSCENE_PLANNING_MODEL_TEMPERATURE
    else:  # default
        prefix = 'MIDSCENE_MODEL_'
        model_name_key = MIDSCENE_MODEL_NAME
        base_url_key = MIDSCENE_MODEL_BASE_URL
        api_key_key = MIDSCENE_MODEL_API_KEY
        http_proxy_key = MIDSCENE_MODEL_HTTP_PROXY
        timeout_key = MIDSCENE_MODEL_TIMEOUT
        temperature_key = MIDSCENE_MODEL_TEMPERATURE
    
    # 获取模型名称
    model_name = config_map.get(model_name_key)
    if not model_name:
        # 如果特定intent的模型名没有设置，回退到默认配置
        if intent != 'default':
            model_name = config_map.get(MIDSCENE_MODEL_NAME)
        if not model_name:
            return None
    
    # 获取其他配置，如果特定intent没有设置则使用默认值
    base_url = config_map.get(base_url_key) or config_map.get(MIDSCENE_MODEL_BASE_URL)
    api_key = config_map.get(api_key_key) or config_map.get(MIDSCENE_MODEL_API_KEY)
    http_proxy = config_map.get(http_proxy_key) or config_map.get(MIDSCENE_MODEL_HTTP_PROXY)
    
    timeout_str = config_map.get(timeout_key) or config_map.get(MIDSCENE_MODEL_TIMEOUT)
    timeout = int(timeout_str) if timeout_str else None
    
    temp_str = config_map.get(temperature_key) or config_map.get(MIDSCENE_MODEL_TEMPERATURE)
    temperature = float(temp_str) if temp_str else 0.0
    
    # 获取 model family 和 vl_mode
    model_family = config_map.get(MIDSCENE_MODEL_FAMILY)
    vl_config = model_family_to_vl_config(model_family)
    
    # 获取证书验证配置
    skip_cert_str = config_map.get(MIDSCENE_MODEL_SKIP_CERT_VERIFICATION, '').lower()
    skip_cert = skip_cert_str in ('true', '1', 'yes', 'on')
    
    # 生成模型描述
    model_description = f"{vl_config.get('vl_mode') or 'default'} mode"
    
    return IModelConfig(
        model_name=model_name,
        openai_base_url=base_url,
        openai_api_key=api_key,
        http_proxy=http_proxy,
        timeout=timeout,
        temperature=temperature,
        vl_mode=vl_config.get('vl_mode'),
        model_description=model_description,
        intent=intent,
        skip_cert_verification=skip_cert,
    )


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self._model_config = model_config
        self._model_config_map: Optional[Dict[str, IModelConfig]] = None
        self._is_initialized = False
    
    def _initialize(self) -> None:
        """初始化配置"""
        if self._is_initialized:
            return
        
        config_map = self._model_config if self._model_config else dict(os.environ)
        
        # 解析各 intent 的配置
        default_config = parse_model_config_for_intent('default', config_map)
        if not default_config:
            raise ValueError(
                "default model config is not found. Please set MIDSCENE_MODEL_NAME "
                "and MIDSCENE_MODEL_BASE_URL environment variables."
            )
        
        insight_config = parse_model_config_for_intent('insight', config_map)
        planning_config = parse_model_config_for_intent('planning', config_map)
        
        self._model_config_map = {
            'default': default_config,
            'insight': insight_config or default_config,
            'planning': planning_config or default_config,
        }
        
        self._is_initialized = True
    
    def get_model_config(self, intent: str = 'default') -> IModelConfig:
        """
        获取指定 intent 的模型配置
        
        Args:
            intent: 意图类型 ('default', 'insight', 'planning')
        
        Returns:
            IModelConfig 实例
        """
        if not self._is_initialized:
            self._initialize()
        
        if self._model_config_map is None:
            raise RuntimeError("Model config map is not initialized")
        
        config = self._model_config_map.get(intent)
        if not config:
            raise ValueError(f"No model config found for intent: {intent}")
        
        return config
    
    def clear_model_config_map(self) -> None:
        """清除配置缓存"""
        self._is_initialized = False
        self._model_config_map = None


# 全局配置管理器实例
global_model_config_manager = ModelConfigManager()
