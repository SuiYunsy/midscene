"""
配置管理器

从 packages/shared/src/env/global-config-manager.ts 和 model-config-manager.ts 迁移
"""

import json
import os
from typing import Any, Optional

from mspy.shared.env.types import (
    BASIC_ENV_KEYS,
    BOOLEAN_ENV_KEYS,
    GLOBAL_ENV_KEYS,
    MODEL_ENV_KEYS,
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_BASE_URL,
    MIDSCENE_MODEL_SOCKS_PROXY,
    MIDSCENE_MODEL_HTTP_PROXY,
    MIDSCENE_MODEL_TIMEOUT,
    MIDSCENE_MODEL_TEMPERATURE,
    MIDSCENE_MODEL_FAMILY,
    MIDSCENE_MODEL_INIT_CONFIG_JSON,
    MIDSCENE_PREFERRED_LANGUAGE,
    MIDSCENE_INSIGHT_MODEL_NAME,
    MIDSCENE_INSIGHT_MODEL_API_KEY,
    MIDSCENE_INSIGHT_MODEL_BASE_URL,
    MIDSCENE_INSIGHT_MODEL_SOCKS_PROXY,
    MIDSCENE_INSIGHT_MODEL_HTTP_PROXY,
    MIDSCENE_INSIGHT_MODEL_TIMEOUT,
    MIDSCENE_INSIGHT_MODEL_TEMPERATURE,
    MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON,
    MIDSCENE_PLANNING_MODEL_NAME,
    MIDSCENE_PLANNING_MODEL_API_KEY,
    MIDSCENE_PLANNING_MODEL_BASE_URL,
    MIDSCENE_PLANNING_MODEL_SOCKS_PROXY,
    MIDSCENE_PLANNING_MODEL_HTTP_PROXY,
    MIDSCENE_PLANNING_MODEL_TIMEOUT,
    MIDSCENE_PLANNING_MODEL_TEMPERATURE,
    MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON,
    MODEL_FAMILY_VALUES,
    ModelConfig,
    ModelIntent,
    VLModeType,
)


class GlobalConfigManager:
    """全局配置管理器"""
    
    def __init__(self):
        self._override_config: dict[str, str] = {}
        self._model_config_manager: Optional["ModelConfigManager"] = None
    
    def register_model_config_manager(self, manager: "ModelConfigManager") -> None:
        """注册模型配置管理器"""
        self._model_config_manager = manager
    
    def get_env_config_value(self, key: str) -> Optional[str]:
        """
        获取环境变量值
        
        优先级：覆盖配置 > 环境变量
        """
        if key in self._override_config:
            return self._override_config[key]
        return os.environ.get(key)
    
    def get_env_config_in_boolean(self, key: str) -> bool:
        """获取布尔类型的环境变量值"""
        value = self.get_env_config_value(key)
        if value is None:
            return False
        return value.lower() in ("true", "1", "yes")
    
    def get_env_config_in_number(self, key: str) -> Optional[int]:
        """获取数字类型的环境变量值"""
        value = self.get_env_config_value(key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None
    
    def get_all_env_config(self) -> dict[str, Optional[str]]:
        """获取所有环境配置"""
        result: dict[str, Optional[str]] = {}
        for key in BASIC_ENV_KEYS + GLOBAL_ENV_KEYS + MODEL_ENV_KEYS:
            result[key] = self.get_env_config_value(key)
        return result
    
    def override_ai_config(
        self,
        new_config: dict[str, str],
        extend_mode: bool = False
    ) -> None:
        """
        覆盖AI配置
        
        Args:
            new_config: 新配置
            extend_mode: 是否扩展模式（True=合并，False=覆盖）
        """
        if extend_mode:
            self._override_config.update(new_config)
        else:
            self._override_config = new_config.copy()
        
        # 同步到模型配置管理器
        if self._model_config_manager:
            self._model_config_manager.sync_from_global_config()


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(
        self,
        model_config: Optional[dict[str, Any]] = None,
        create_openai_client: Optional[Any] = None
    ):
        self._model_config = model_config or {}
        self._create_openai_client = create_openai_client
        self._global_config_manager: Optional[GlobalConfigManager] = None
    
    def register_global_config_manager(self, manager: GlobalConfigManager) -> None:
        """注册全局配置管理器"""
        self._global_config_manager = manager
    
    def sync_from_global_config(self) -> None:
        """从全局配置同步"""
        pass  # 在需要时实现
    
    def _get_config_value(self, key: str) -> Optional[str]:
        """获取配置值"""
        # 优先使用实例配置
        if key in self._model_config:
            value = self._model_config[key]
            return str(value) if value is not None else None
        
        # 然后使用全局配置
        if self._global_config_manager:
            return self._global_config_manager.get_env_config_value(key)
        
        # 最后使用环境变量
        return os.environ.get(key)
    
    def _resolve_vl_mode(self, model_family: Optional[str]) -> Optional[VLModeType]:
        """解析VL模式"""
        if not model_family:
            return None
        
        if model_family in MODEL_FAMILY_VALUES:
            # 直接映射已知值
            return model_family  # type: ignore
        
        return None
    
    def get_model_config(self, intent: ModelIntent = "default") -> ModelConfig:
        """
        获取指定意图的模型配置
        
        Args:
            intent: 模型意图 (insight, planning, default)
        
        Returns:
            ModelConfig实例
        """
        # 根据intent选择配置键
        if intent == "insight":
            name_key = MIDSCENE_INSIGHT_MODEL_NAME
            api_key_key = MIDSCENE_INSIGHT_MODEL_API_KEY
            base_url_key = MIDSCENE_INSIGHT_MODEL_BASE_URL
            socks_proxy_key = MIDSCENE_INSIGHT_MODEL_SOCKS_PROXY
            http_proxy_key = MIDSCENE_INSIGHT_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_INSIGHT_MODEL_TIMEOUT
            temperature_key = MIDSCENE_INSIGHT_MODEL_TEMPERATURE
            init_config_key = MIDSCENE_INSIGHT_MODEL_INIT_CONFIG_JSON
        elif intent == "planning":
            name_key = MIDSCENE_PLANNING_MODEL_NAME
            api_key_key = MIDSCENE_PLANNING_MODEL_API_KEY
            base_url_key = MIDSCENE_PLANNING_MODEL_BASE_URL
            socks_proxy_key = MIDSCENE_PLANNING_MODEL_SOCKS_PROXY
            http_proxy_key = MIDSCENE_PLANNING_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_PLANNING_MODEL_TIMEOUT
            temperature_key = MIDSCENE_PLANNING_MODEL_TEMPERATURE
            init_config_key = MIDSCENE_PLANNING_MODEL_INIT_CONFIG_JSON
        else:
            name_key = MIDSCENE_MODEL_NAME
            api_key_key = MIDSCENE_MODEL_API_KEY
            base_url_key = MIDSCENE_MODEL_BASE_URL
            socks_proxy_key = MIDSCENE_MODEL_SOCKS_PROXY
            http_proxy_key = MIDSCENE_MODEL_HTTP_PROXY
            timeout_key = MIDSCENE_MODEL_TIMEOUT
            temperature_key = MIDSCENE_MODEL_TEMPERATURE
            init_config_key = MIDSCENE_MODEL_INIT_CONFIG_JSON
        
        # 获取配置值，回退到默认配置
        model_name = self._get_config_value(name_key) or self._get_config_value(MIDSCENE_MODEL_NAME) or ""
        api_key = self._get_config_value(api_key_key) or self._get_config_value(MIDSCENE_MODEL_API_KEY)
        base_url = self._get_config_value(base_url_key) or self._get_config_value(MIDSCENE_MODEL_BASE_URL)
        socks_proxy = self._get_config_value(socks_proxy_key) or self._get_config_value(MIDSCENE_MODEL_SOCKS_PROXY)
        http_proxy = self._get_config_value(http_proxy_key) or self._get_config_value(MIDSCENE_MODEL_HTTP_PROXY)
        
        # 解析超时
        timeout_str = self._get_config_value(timeout_key) or self._get_config_value(MIDSCENE_MODEL_TIMEOUT)
        timeout = int(timeout_str) if timeout_str else None
        
        # 解析温度
        temperature_str = self._get_config_value(temperature_key) or self._get_config_value(MIDSCENE_MODEL_TEMPERATURE)
        temperature = float(temperature_str) if temperature_str else None
        
        # 解析额外配置
        extra_config_str = self._get_config_value(init_config_key) or self._get_config_value(MIDSCENE_MODEL_INIT_CONFIG_JSON)
        extra_config = None
        if extra_config_str:
            try:
                extra_config = json.loads(extra_config_str)
            except json.JSONDecodeError:
                pass
        
        # 解析模型家族
        model_family = self._get_config_value(MIDSCENE_MODEL_FAMILY)
        vl_mode = self._resolve_vl_mode(model_family)
        
        # 构建模型描述
        model_description = f"{intent}: {model_name}"
        if base_url:
            model_description += f" @ {base_url}"
        
        return ModelConfig(
            model_name=model_name,
            openai_api_key=api_key,
            openai_base_url=base_url,
            socks_proxy=socks_proxy,
            http_proxy=http_proxy,
            timeout=timeout,
            temperature=temperature,
            openai_extra_config=extra_config,
            vl_mode_raw=model_family,
            vl_mode=vl_mode,
            model_description=model_description,
            intent=intent,
            create_openai_client=self._create_openai_client,
        )
    
    def throw_error_if_non_vl_model(self) -> None:
        """如果不是VL模型则抛出错误"""
        config = self.get_model_config("default")
        if not config.vl_mode:
            print(
                "Warning: Non-VL model detected. "
                "Consider using a VL model for better performance. "
                "https://midscenejs.com/model-config"
            )


# 全局实例
global_config_manager = GlobalConfigManager()
global_model_config_manager = ModelConfigManager()

# 互相注册
global_config_manager.register_model_config_manager(global_model_config_manager)
global_model_config_manager.register_global_config_manager(global_config_manager)


def override_ai_config(
    new_config: dict[str, str],
    extend_mode: bool = False
) -> None:
    """覆盖AI配置的便捷函数"""
    global_config_manager.override_ai_config(new_config, extend_mode)


def get_preferred_language() -> str:
    """获取首选语言"""
    prefer = global_config_manager.get_env_config_value(MIDSCENE_PREFERRED_LANGUAGE)
    if prefer:
        return prefer
    
    # 根据时区判断
    import time
    try:
        tz_name = time.tzname[0] if time.tzname else ""
        if "China" in tz_name or "CST" in tz_name:
            return "Chinese"
    except Exception:
        pass
    
    return "English"
