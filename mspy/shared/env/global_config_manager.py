# -*- coding: utf-8 -*-
"""
全局配置管理器
管理全局环境变量配置。
"""

import os
import re
from typing import Any, Dict, List, Optional

from .constants import (
    ALL_ENV_KEYS,
    BOOLEAN_ENV_KEYS,
    GLOBAL_ENV_KEYS,
    MODEL_ENV_KEYS,
    NUMBER_ENV_KEYS,
    STRING_ENV_KEYS,
    MATCH_BY_POSITION,
)


class GlobalConfigManager:
    """
    收集并管理来自环境变量、覆盖配置等的全局配置
    提供方法获取合并后的配置值
    """
    
    def __init__(self):
        self._override: Optional[Dict[str, Any]] = None
        self._extend_mode: bool = False
        self._keys_have_been_read: Dict[str, bool] = {}
        self._global_model_config_manager: Optional[Any] = None
    
    def get_all_env_config(self) -> Dict[str, Optional[str]]:
        """
        获取所有环境变量配置
        每次调用都重新计算，因为环境变量可能随时更新
        """
        env_config: Dict[str, Optional[str]] = {}
        
        for name in ALL_ENV_KEYS:
            env_config[name] = os.environ.get(name)
        
        if self._override:
            if self._extend_mode:
                return {**env_config, **self._override}
            else:
                return {**self._override}
        
        return env_config
    
    def get_env_config_value(self, key: str) -> Optional[str]:
        """
        获取字符串类型的环境变量值
        
        Args:
            key: 环境变量键名
            
        Returns:
            配置值或 None
        """
        if key == MATCH_BY_POSITION:
            raise ValueError(
                "MATCH_BY_POSITION is discarded, use MIDSCENE_MODEL_FAMILY instead"
            )
        
        if key not in STRING_ENV_KEYS:
            raise ValueError(f"getEnvConfigValue with key {key} is not supported.")
        
        all_config = self.get_all_env_config()
        self._keys_have_been_read[key] = True
        
        value = all_config.get(key)
        if isinstance(value, str):
            return value.strip()
        return value
    
    def get_env_config_in_number(self, key: str) -> int:
        """
        获取数字类型的环境变量值
        
        Args:
            key: 环境变量键名
            
        Returns:
            配置值的整数形式
        """
        if key not in NUMBER_ENV_KEYS:
            raise ValueError(f"getEnvConfigInNumber with key {key} is not supported")
        
        all_config = self.get_all_env_config()
        self._keys_have_been_read[key] = True
        
        value = all_config.get(key, "")
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def get_env_config_in_boolean(self, key: str) -> bool:
        """
        获取布尔类型的环境变量值
        
        Args:
            key: 环境变量键名
            
        Returns:
            配置值的布尔形式
        """
        if key not in BOOLEAN_ENV_KEYS:
            raise ValueError(f"getEnvConfigInBoolean with key {key} is not supported")
        
        all_config = self.get_all_env_config()
        self._keys_have_been_read[key] = True
        
        value = all_config.get(key)
        
        if not value:
            return False
        
        if re.match(r'^(true|1)$', value, re.IGNORECASE):
            return True
        if re.match(r'^(false|0)$', value, re.IGNORECASE):
            return False
        
        return bool(value.strip()) if isinstance(value, str) else bool(value)
    
    def register_model_config_manager(self, manager: Any) -> None:
        """注册全局模型配置管理器"""
        self._global_model_config_manager = manager
    
    def override_ai_config(
        self,
        new_config: Dict[str, str],
        extend_mode: bool = False
    ) -> None:
        """
        覆盖 AI 配置（已弃用，建议使用 Agent 构造函数的 modelConfig 参数）
        
        Args:
            new_config: 新的配置字典
            extend_mode: True 表示与全局配置合并，False 表示完全覆盖
        """
        valid_keys = set(GLOBAL_ENV_KEYS + MODEL_ENV_KEYS)
        
        for key in new_config:
            if key not in valid_keys:
                raise ValueError(f"Failed to override AI config, invalid key: {key}")
            
            value = new_config[key]
            if not isinstance(value, str):
                raise ValueError(
                    f"Failed to override AI config, value for key {key} must be a string, "
                    f"but got with type {type(value).__name__}"
                )
            
            if key in self._keys_have_been_read:
                print(
                    f"Warning: try to override AI config with key {key}, "
                    "but it has been read."
                )
        
        if extend_mode and self._override:
            saved_config = {**self._override, **new_config}
        else:
            saved_config = new_config
        
        self._override = saved_config
        self._extend_mode = extend_mode
        
        if self._global_model_config_manager:
            self._global_model_config_manager.clear_model_config_map()
        else:
            raise RuntimeError(
                "globalModelConfigManager is not registered, which should not happen"
            )


# 全局单例
global_config_manager = GlobalConfigManager()
