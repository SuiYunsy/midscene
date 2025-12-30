# -*- coding: utf-8 -*-
"""
模型配置管理器
管理不同意图（intent）的模型配置。
"""

import json
from typing import Any, Callable, Dict, Optional

from .types import IModelConfig, TIntent, TModelConfig, TVlModeTypes, UITarsModelVersion
from .constants import (
    MODEL_FAMILY_VALUES,
    MIDSCENE_USE_DOUBAO_VISION,
    MIDSCENE_USE_QWEN_VL,
    MIDSCENE_USE_QWEN3_VL,
    MIDSCENE_USE_VLM_UI_TARS,
    MIDSCENE_USE_GEMINI,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)
from .config_keys import (
    INTENT_KEYS_MAP,
    ModelConfigKeys,
)
from ..logger import get_debug


debug_log = get_debug("ai:config")


def model_family_to_vl_config(
    model_family: Optional[str]
) -> Dict[str, Any]:
    """
    将模型家族转换为 VL 配置
    
    Args:
        model_family: 模型家族值
        
    Returns:
        包含 vl_mode 和 ui_tars_version 的字典
    """
    if not model_family:
        return {"vl_mode": None, "ui_tars_version": None}
    
    # UI-TARS 变体处理
    if model_family == "vlm-ui-tars":
        return {"vl_mode": "vlm-ui-tars", "ui_tars_version": UITarsModelVersion.V1_0}
    
    if model_family in ("vlm-ui-tars-doubao", "vlm-ui-tars-doubao-1.5"):
        return {"vl_mode": "vlm-ui-tars", "ui_tars_version": UITarsModelVersion.DOUBAO_1_5_20B}
    
    # 检查模型家族是否有效
    if model_family not in MODEL_FAMILY_VALUES:
        raise ValueError(f"Invalid MIDSCENE_MODEL_FAMILY value: {model_family}")
    
    # 其他模型家族直接映射到 vl_mode
    return {"vl_mode": model_family, "ui_tars_version": None}


def legacy_config_to_model_family(
    provider: Dict[str, Optional[str]]
) -> Optional[str]:
    """
    将旧版环境变量转换为模型家族
    
    Args:
        provider: 环境变量提供者
        
    Returns:
        对应的模型家族值
    """
    is_doubao = provider.get(MIDSCENE_USE_DOUBAO_VISION)
    is_qwen = provider.get(MIDSCENE_USE_QWEN_VL)
    is_qwen3 = provider.get(MIDSCENE_USE_QWEN3_VL)
    is_ui_tars = provider.get(MIDSCENE_USE_VLM_UI_TARS)
    is_gemini = provider.get(MIDSCENE_USE_GEMINI)
    
    enabled_modes = [
        mode for mode in [
            is_doubao and MIDSCENE_USE_DOUBAO_VISION,
            is_qwen and MIDSCENE_USE_QWEN_VL,
            is_qwen3 and MIDSCENE_USE_QWEN3_VL,
            is_ui_tars and MIDSCENE_USE_VLM_UI_TARS,
            is_gemini and MIDSCENE_USE_GEMINI,
        ] if mode
    ]
    
    if len(enabled_modes) > 1:
        raise ValueError(
            f"Only one vision mode can be enabled at a time. "
            f"Currently enabled modes: {', '.join(enabled_modes)}. "
            f"Please disable all but one mode."
        )
    
    # 映射到模型家族
    if is_qwen3:
        return "qwen3-vl"
    if is_qwen:
        return "qwen2.5-vl"
    if is_doubao:
        return "doubao-vision"
    if is_gemini:
        return "gemini"
    
    if is_ui_tars:
        if is_ui_tars == "1":
            return "vlm-ui-tars"
        elif is_ui_tars in ("DOUBAO", "DOUBAO-1.5"):
            return "vlm-ui-tars-doubao-1.5"
        else:
            return "vlm-ui-tars-doubao"
    
    return None


def parse_json_config(key: str, value: Optional[str]) -> Optional[Dict[str, Any]]:
    """解析 JSON 格式的配置"""
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        debug_log(f"Failed to parse JSON config for key {key}: {value}")
        return None


def parse_openai_sdk_config(
    keys: ModelConfigKeys,
    provider: Dict[str, Optional[str]],
    use_legacy_logic: bool = False
) -> IModelConfig:
    """
    解析 OpenAI SDK 配置
    
    Args:
        keys: 模型配置键
        provider: 配置提供者（环境变量映射）
        use_legacy_logic: 是否使用旧版逻辑
        
    Returns:
        解析后的模型配置
    """
    debug_log(f"enter parse_openai_sdk_config with keys: {keys}")
    
    # 旧版逻辑兼容
    legacy_api_key = provider.get(OPENAI_API_KEY) if use_legacy_logic else None
    legacy_base_url = provider.get(OPENAI_BASE_URL) if use_legacy_logic else None
    legacy_model_family = legacy_config_to_model_family(provider) if use_legacy_logic else None
    
    model_family_raw = provider.get(keys.model_family) or legacy_model_family
    openai_api_key = provider.get(keys.openai_api_key) or legacy_api_key
    openai_base_url = provider.get(keys.openai_base_url) or legacy_base_url
    socks_proxy = provider.get(keys.socks_proxy)
    http_proxy = provider.get(keys.http_proxy)
    model_name = provider.get(keys.model_name)
    openai_extra_config_str = provider.get(keys.openai_extra_config)
    openai_extra_config = parse_json_config(keys.openai_extra_config, openai_extra_config_str)
    
    temperature_str = provider.get(keys.temperature)
    temperature = float(temperature_str) if temperature_str else 0.0
    
    timeout_str = provider.get(keys.timeout)
    timeout = int(timeout_str) if timeout_str else None
    
    vl_config = model_family_to_vl_config(model_family_raw)
    vl_mode = vl_config.get("vl_mode")
    ui_tars_version = vl_config.get("ui_tars_version")
    
    # 生成模型描述
    if vl_mode:
        if ui_tars_version:
            model_description = f"UI-TARS={ui_tars_version}"
        else:
            model_description = f"{vl_mode} mode"
    else:
        model_description = ""
    
    return IModelConfig(
        model_name=model_name or "",
        model_description=model_description,
        intent="default",  # 会在外部设置
        socks_proxy=socks_proxy,
        http_proxy=http_proxy,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        openai_extra_config=openai_extra_config,
        timeout=timeout,
        temperature=temperature,
        vl_mode_raw=vl_mode,
        vl_mode=vl_mode,
        ui_tars_model_version=ui_tars_version,
    )


def decide_model_config_from_intent_config(
    intent: TIntent,
    config_map: Dict[str, Optional[str]]
) -> Optional[IModelConfig]:
    """
    根据意图决定模型配置
    
    Args:
        intent: 意图类型
        config_map: 配置映射
        
    Returns:
        模型配置或 None
    """
    keys = INTENT_KEYS_MAP.get(intent)
    if not keys:
        debug_log(f"no keys found for intent {intent}")
        return None
    
    model_name = config_map.get(keys.model_name)
    
    if not model_name:
        debug_log(f"no modelName found for intent {intent}")
        return None
    
    result = parse_openai_sdk_config(
        keys=keys,
        provider=config_map,
        use_legacy_logic=(intent == "default")
    )
    result.intent = intent
    
    if not result.openai_base_url:
        raise ValueError(
            f"failed to get base URL of model (intent={intent}). "
            "See https://midscenejs.com/model-strategy"
        )
    
    if not result.model_name:
        print(
            f"Warning: modelName is not set for intent {intent}, "
            "this may cause unexpected behavior. "
            "See https://midscenejs.com/model-strategy"
        )
    
    return result


class ModelConfigManager:
    """
    模型配置管理器
    管理不同意图的模型配置
    """
    
    def __init__(
        self,
        model_config: Optional[TModelConfig] = None,
        create_openai_client_fn: Optional[Callable] = None
    ):
        self._model_config_map: Optional[Dict[TIntent, IModelConfig]] = None
        self._is_initialized = False
        self._isolated_mode = False
        self._global_config_manager = None
        self._model_config = model_config
        self._create_openai_client_fn = create_openai_client_fn
    
    def _initialize(self) -> None:
        """初始化模型配置"""
        if self._is_initialized:
            return
        
        if self._model_config:
            self._isolated_mode = True
            config_map = self._normalize_model_config(self._model_config)
        else:
            config_map = (
                self._global_config_manager.get_all_env_config()
                if self._global_config_manager
                else {}
            )
        
        default_config = decide_model_config_from_intent_config("default", config_map)
        if not default_config:
            raise RuntimeError(
                "default model config is not found, which should not happen"
            )
        
        insight_config = decide_model_config_from_intent_config("insight", config_map)
        planning_config = decide_model_config_from_intent_config("planning", config_map)
        
        # 为每个配置添加自定义客户端创建函数
        if self._create_openai_client_fn:
            default_config.create_openai_client = self._create_openai_client_fn
            if insight_config:
                insight_config.create_openai_client = self._create_openai_client_fn
            if planning_config:
                planning_config.create_openai_client = self._create_openai_client_fn
        
        self._model_config_map = {
            "default": default_config,
            "insight": insight_config or default_config,
            "planning": planning_config or default_config,
        }
        
        self._is_initialized = True
    
    def _normalize_model_config(
        self,
        config: TModelConfig
    ) -> Dict[str, Optional[str]]:
        """标准化模型配置"""
        return {
            key: str(value) if value is not None else None
            for key, value in config.items()
        }
    
    def clear_model_config_map(self) -> None:
        """清除模型配置映射（仅供 GlobalConfigManager 调用）"""
        if self._isolated_mode:
            raise RuntimeError(
                "ModelConfigManager work in isolated mode, "
                "so clear_model_config_map should not be called"
            )
        self._is_initialized = False
    
    def get_model_config(self, intent: TIntent) -> IModelConfig:
        """
        获取指定意图的模型配置
        
        Args:
            intent: 意图类型
            
        Returns:
            模型配置
        """
        if not self._is_initialized:
            self._initialize()
        
        if not self._model_config_map:
            raise RuntimeError(
                "modelConfigMap is not initialized, which should not happen"
            )
        
        return self._model_config_map[intent]
    
    def get_upload_test_server_url(self) -> Optional[str]:
        """获取测试服务器上传 URL"""
        config = self.get_model_config("default")
        if config.openai_extra_config:
            return config.openai_extra_config.get("REPORT_SERVER_URL")
        return None
    
    def register_global_config_manager(self, manager) -> None:
        """注册全局配置管理器"""
        self._global_config_manager = manager
    
    def throw_error_if_non_vl_model(self) -> None:
        """如果不是 VL 模型则抛出错误"""
        config = self.get_model_config("default")
        
        if not config.vl_mode:
            raise ValueError(
                "MIDSCENE_MODEL_FAMILY is not set to a visual language model (VL model), "
                "the element localization can not be achieved. "
                "Check your model configuration. "
                "See https://midscenejs.com/model-strategy.html"
            )


# 全局单例
global_model_config_manager = ModelConfigManager()
