"""
Config - 配置管理模块
提供环境变量和模型配置管理
"""

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from .types import IModelConfig, TIntent
from .logger import get_debug


# 环境变量键
MIDSCENE_MODEL_NAME = "MIDSCENE_MODEL_NAME"
MIDSCENE_MODEL_API_KEY = "MIDSCENE_MODEL_API_KEY"
MIDSCENE_MODEL_BASE_URL = "MIDSCENE_MODEL_BASE_URL"
MIDSCENE_MODEL_HTTP_PROXY = "MIDSCENE_MODEL_HTTP_PROXY"
MIDSCENE_MODEL_SOCKS_PROXY = "MIDSCENE_MODEL_SOCKS_PROXY"
MIDSCENE_MODEL_TIMEOUT = "MIDSCENE_MODEL_TIMEOUT"
MIDSCENE_MODEL_TEMPERATURE = "MIDSCENE_MODEL_TEMPERATURE"
MIDSCENE_MODEL_FAMILY = "MIDSCENE_MODEL_FAMILY"
MIDSCENE_MODEL_INIT_CONFIG_JSON = "MIDSCENE_MODEL_INIT_CONFIG_JSON"
MIDSCENE_MODEL_MAX_TOKENS = "MIDSCENE_MODEL_MAX_TOKENS"

MIDSCENE_DEBUG_MODE = "MIDSCENE_DEBUG_MODE"
MIDSCENE_REPLANNING_CYCLE_LIMIT = "MIDSCENE_REPLANNING_CYCLE_LIMIT"
MIDSCENE_RUN_DIR = "MIDSCENE_RUN_DIR"

# Insight 模型配置
MIDSCENE_INSIGHT_MODEL_NAME = "MIDSCENE_INSIGHT_MODEL_NAME"
MIDSCENE_INSIGHT_MODEL_BASE_URL = "MIDSCENE_INSIGHT_MODEL_BASE_URL"
MIDSCENE_INSIGHT_MODEL_API_KEY = "MIDSCENE_INSIGHT_MODEL_API_KEY"
MIDSCENE_INSIGHT_MODEL_HTTP_PROXY = "MIDSCENE_INSIGHT_MODEL_HTTP_PROXY"
MIDSCENE_INSIGHT_MODEL_SOCKS_PROXY = "MIDSCENE_INSIGHT_MODEL_SOCKS_PROXY"
MIDSCENE_INSIGHT_MODEL_TIMEOUT = "MIDSCENE_INSIGHT_MODEL_TIMEOUT"
MIDSCENE_INSIGHT_MODEL_TEMPERATURE = "MIDSCENE_INSIGHT_MODEL_TEMPERATURE"
MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON = "MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON"

# Planning 模型配置
MIDSCENE_PLANNING_MODEL_NAME = "MIDSCENE_PLANNING_MODEL_NAME"
MIDSCENE_PLANNING_MODEL_BASE_URL = "MIDSCENE_PLANNING_MODEL_BASE_URL"
MIDSCENE_PLANNING_MODEL_API_KEY = "MIDSCENE_PLANNING_MODEL_API_KEY"
MIDSCENE_PLANNING_MODEL_HTTP_PROXY = "MIDSCENE_PLANNING_MODEL_HTTP_PROXY"
MIDSCENE_PLANNING_MODEL_SOCKS_PROXY = "MIDSCENE_PLANNING_MODEL_SOCKS_PROXY"
MIDSCENE_PLANNING_MODEL_TIMEOUT = "MIDSCENE_PLANNING_MODEL_TIMEOUT"
MIDSCENE_PLANNING_MODEL_TEMPERATURE = "MIDSCENE_PLANNING_MODEL_TEMPERATURE"
MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON = "MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON"


# VL 模式类型
VL_MODE_TYPES = ["qwen2.5-vl", "qwen3-vl", "doubao-vision", "gemini", "vlm-ui-tars"]


# 模型家族值（只保留 qwen3-vl 相关）
MODEL_FAMILY_VALUES = [
    "qwen2.5-vl",
    "qwen3-vl",
]


@dataclass
class DefaultModelConfigKeys:
    """默认模型配置键"""
    model_name: str = MIDSCENE_MODEL_NAME
    openai_api_key: str = MIDSCENE_MODEL_API_KEY
    openai_base_url: str = MIDSCENE_MODEL_BASE_URL
    http_proxy: str = MIDSCENE_MODEL_HTTP_PROXY
    socks_proxy: str = MIDSCENE_MODEL_SOCKS_PROXY
    timeout: str = MIDSCENE_MODEL_TIMEOUT
    temperature: str = MIDSCENE_MODEL_TEMPERATURE
    model_family: str = MIDSCENE_MODEL_FAMILY
    openai_extra_config: str = MIDSCENE_MODEL_INIT_CONFIG_JSON


@dataclass
class InsightModelConfigKeys:
    """Insight 模型配置键"""
    model_name: str = MIDSCENE_INSIGHT_MODEL_NAME
    openai_api_key: str = MIDSCENE_INSIGHT_MODEL_API_KEY
    openai_base_url: str = MIDSCENE_INSIGHT_MODEL_BASE_URL
    http_proxy: str = MIDSCENE_INSIGHT_MODEL_HTTP_PROXY
    socks_proxy: str = MIDSCENE_INSIGHT_MODEL_SOCKS_PROXY
    timeout: str = MIDSCENE_INSIGHT_MODEL_TIMEOUT
    temperature: str = MIDSCENE_INSIGHT_MODEL_TEMPERATURE
    model_family: str = MIDSCENE_MODEL_FAMILY
    openai_extra_config: str = MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON


@dataclass
class PlanningModelConfigKeys:
    """Planning 模型配置键"""
    model_name: str = MIDSCENE_PLANNING_MODEL_NAME
    openai_api_key: str = MIDSCENE_PLANNING_MODEL_API_KEY
    openai_base_url: str = MIDSCENE_PLANNING_MODEL_BASE_URL
    http_proxy: str = MIDSCENE_PLANNING_MODEL_HTTP_PROXY
    socks_proxy: str = MIDSCENE_PLANNING_MODEL_SOCKS_PROXY
    timeout: str = MIDSCENE_PLANNING_MODEL_TIMEOUT
    temperature: str = MIDSCENE_PLANNING_MODEL_TEMPERATURE
    model_family: str = MIDSCENE_MODEL_FAMILY
    openai_extra_config: str = MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON


def model_family_to_vl_config(model_family: Optional[str]) -> Dict[str, Optional[str]]:
    """
    将模型家族转换为 VL 配置
    
    Args:
        model_family: 模型家族值
        
    Returns:
        包含 vl_mode 的字典
    """
    if not model_family:
        return {"vl_mode": None}
    
    # 验证模型家族值（只支持 qwen3-vl 家族）
    if model_family not in MODEL_FAMILY_VALUES:
        supported_values = ", ".join(MODEL_FAMILY_VALUES)
        raise ValueError(f"Invalid MIDSCENE_MODEL_FAMILY value: {model_family}. Supported values: {supported_values}")
    
    return {"vl_mode": model_family}


def parse_json_config(key: str, value: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    解析 JSON 配置
    
    Args:
        key: 配置键名
        value: JSON 字符串
        
    Returns:
        解析后的字典
    """
    if not value:
        return None
    
    import json
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse {key} as JSON: {e}")


def parse_openai_sdk_config(
    keys: Union[DefaultModelConfigKeys, InsightModelConfigKeys, PlanningModelConfigKeys],
    provider: Dict[str, Optional[str]],
) -> IModelConfig:
    """
    解析 OpenAI SDK 配置
    
    Args:
        keys: 配置键定义
        provider: 环境变量提供者
        
    Returns:
        模型配置
    """
    debug_log = get_debug("ai:config")
    debug_log("enter parse_openai_sdk_config with keys:", keys)
    
    model_family_raw = provider.get(keys.model_family)
    openai_api_key = provider.get(keys.openai_api_key)
    openai_base_url = provider.get(keys.openai_base_url)
    socks_proxy = provider.get(keys.socks_proxy)
    http_proxy = provider.get(keys.http_proxy)
    model_name = provider.get(keys.model_name)
    openai_extra_config_str = provider.get(keys.openai_extra_config)
    openai_extra_config = parse_json_config(keys.openai_extra_config, openai_extra_config_str)
    
    timeout_str = provider.get(keys.timeout)
    timeout = int(timeout_str) if timeout_str else None
    
    temperature_str = provider.get(keys.temperature)
    temperature = float(temperature_str) if temperature_str else 0.0
    
    vl_config = model_family_to_vl_config(model_family_raw)
    vl_mode = vl_config.get("vl_mode")
    
    model_description = f"{vl_mode} mode" if vl_mode else ""
    
    return IModelConfig(
        socks_proxy=socks_proxy,
        http_proxy=http_proxy,
        vl_mode_raw=vl_mode,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        openai_extra_config=openai_extra_config,
        vl_mode=vl_mode,
        model_name=model_name or "",
        model_description=model_description,
        intent="default",
        timeout=timeout,
        temperature=temperature,
    )


def decide_model_config_from_intent(
    intent: str,
    config_map: Dict[str, Optional[str]],
) -> Optional[IModelConfig]:
    """
    根据意图决定模型配置
    
    Args:
        intent: 意图类型 ('default', 'insight', 'planning')
        config_map: 配置映射
        
    Returns:
        模型配置，如果未找到则返回 None
    """
    debug_log = get_debug("ai:config")
    debug_log("will decide model config for intent:", intent)
    
    keys_map = {
        "insight": InsightModelConfigKeys(),
        "planning": PlanningModelConfigKeys(),
        "default": DefaultModelConfigKeys(),
    }
    
    keys = keys_map.get(intent, DefaultModelConfigKeys())
    model_name = config_map.get(keys.model_name)
    
    if not model_name:
        debug_log("no model_name found for intent", intent)
        return None
    
    result = parse_openai_sdk_config(keys, config_map)
    result.intent = intent
    
    if not result.openai_base_url:
        raise ValueError(f"Failed to get base URL of model (intent={intent}). Please set {keys.openai_base_url}")
    
    return result


class GlobalConfigManager:
    """全局配置管理器"""
    
    _instance: Optional["GlobalConfigManager"] = None
    _env_config: Dict[str, Optional[str]] = {}
    
    def __new__(cls) -> "GlobalConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_env_config()
        return cls._instance
    
    def _load_env_config(self) -> None:
        """从环境变量加载配置"""
        self._env_config = {
            key: os.environ.get(key)
            for key in [
                MIDSCENE_MODEL_NAME,
                MIDSCENE_MODEL_API_KEY,
                MIDSCENE_MODEL_BASE_URL,
                MIDSCENE_MODEL_HTTP_PROXY,
                MIDSCENE_MODEL_SOCKS_PROXY,
                MIDSCENE_MODEL_TIMEOUT,
                MIDSCENE_MODEL_TEMPERATURE,
                MIDSCENE_MODEL_FAMILY,
                MIDSCENE_MODEL_INIT_CONFIG_JSON,
                MIDSCENE_MODEL_MAX_TOKENS,
                MIDSCENE_DEBUG_MODE,
                MIDSCENE_REPLANNING_CYCLE_LIMIT,
                MIDSCENE_RUN_DIR,
                MIDSCENE_INSIGHT_MODEL_NAME,
                MIDSCENE_INSIGHT_MODEL_BASE_URL,
                MIDSCENE_INSIGHT_MODEL_API_KEY,
                MIDSCENE_INSIGHT_MODEL_HTTP_PROXY,
                MIDSCENE_INSIGHT_MODEL_SOCKS_PROXY,
                MIDSCENE_INSIGHT_MODEL_TIMEOUT,
                MIDSCENE_INSIGHT_MODEL_TEMPERATURE,
                MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON,
                MIDSCENE_PLANNING_MODEL_NAME,
                MIDSCENE_PLANNING_MODEL_BASE_URL,
                MIDSCENE_PLANNING_MODEL_API_KEY,
                MIDSCENE_PLANNING_MODEL_HTTP_PROXY,
                MIDSCENE_PLANNING_MODEL_SOCKS_PROXY,
                MIDSCENE_PLANNING_MODEL_TIMEOUT,
                MIDSCENE_PLANNING_MODEL_TEMPERATURE,
                MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON,
            ]
        }
    
    def get_all_env_config(self) -> Dict[str, Optional[str]]:
        """获取所有环境配置"""
        return self._env_config.copy()
    
    def get_env_config_value(self, key: str) -> Optional[str]:
        """获取指定配置值"""
        return self._env_config.get(key) or os.environ.get(key)
    
    def get_env_config_in_boolean(self, key: str) -> bool:
        """获取布尔类型配置值"""
        value = self.get_env_config_value(key)
        return value is not None and value.lower() in ("1", "true", "yes")
    
    def override_config(self, config: Dict[str, Optional[str]]) -> None:
        """覆盖配置"""
        self._env_config.update(config)


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(
        self,
        model_config: Optional[Dict[str, Union[str, int]]] = None,
        create_openai_client: Optional[Callable[..., Any]] = None,
    ):
        self._model_config = model_config
        self._create_openai_client = create_openai_client
        self._model_config_map: Optional[Dict[str, IModelConfig]] = None
        self._is_initialized = False
        self._isolated_mode = False
        self._global_config_manager: Optional[GlobalConfigManager] = None
    
    def _normalize_model_config(
        self, config: Dict[str, Union[str, int]]
    ) -> Dict[str, Optional[str]]:
        """规范化模型配置"""
        return {
            key: str(value) if value is not None else None
            for key, value in config.items()
        }
    
    def _initialize(self) -> None:
        """初始化配置"""
        if self._is_initialized:
            return
        
        if self._model_config:
            self._isolated_mode = True
            config_map = self._normalize_model_config(self._model_config)
        else:
            global_manager = self._global_config_manager or GlobalConfigManager()
            config_map = global_manager.get_all_env_config()
        
        default_config = decide_model_config_from_intent("default", config_map)
        if not default_config:
            raise ValueError("Default model config is not found. Please check your environment variables.")
        
        insight_config = decide_model_config_from_intent("insight", config_map)
        planning_config = decide_model_config_from_intent("planning", config_map)
        
        # 设置 createOpenAIClient
        if self._create_openai_client:
            default_config.create_openai_client = self._create_openai_client
            if insight_config:
                insight_config.create_openai_client = self._create_openai_client
            if planning_config:
                planning_config.create_openai_client = self._create_openai_client
        
        self._model_config_map = {
            "default": default_config,
            "insight": insight_config or default_config,
            "planning": planning_config or default_config,
        }
        
        self._is_initialized = True
    
    def get_model_config(self, intent: str) -> IModelConfig:
        """
        获取模型配置
        
        Args:
            intent: 意图类型
            
        Returns:
            模型配置
        """
        if not self._is_initialized:
            self._initialize()
        
        if not self._model_config_map:
            raise RuntimeError("Model config map is not initialized")
        
        return self._model_config_map[intent]
    
    def get_upload_test_server_url(self) -> Optional[str]:
        """获取上传测试服务器 URL"""
        config = self.get_model_config("default")
        if config.openai_extra_config:
            return config.openai_extra_config.get("REPORT_SERVER_URL")
        return None
    
    def register_global_config_manager(self, manager: GlobalConfigManager) -> None:
        """注册全局配置管理器"""
        self._global_config_manager = manager
    
    def throw_error_if_non_vl_model(self) -> None:
        """如果不是 VL 模型则抛出错误"""
        config = self.get_model_config("default")
        if not config.vl_mode:
            raise ValueError(
                "MIDSCENE_MODEL_FAMILY is not set to a visual language model (VL model). "
                "Only qwen2.5-vl and qwen3-vl are supported. "
                "Please check your model configuration."
            )


# 全局实例
global_config_manager = GlobalConfigManager()
global_model_config_manager = ModelConfigManager()
global_model_config_manager.register_global_config_manager(global_config_manager)


def override_ai_config(config: Dict[str, Optional[str]]) -> None:
    """
    覆盖 AI 配置
    
    Args:
        config: 配置字典
    """
    global_config_manager.override_config(config)
