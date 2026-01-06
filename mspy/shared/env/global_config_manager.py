"""
全局配置管理器

对应TypeScript源码: packages/shared/src/env/global-config-manager.ts
"""

import os
from typing import Any, Dict, Optional

from mspy.shared.env.types import (
    ALL_ENV_KEYS,
    BOOLEAN_ENV_KEYS,
    NUMBER_ENV_KEYS,
    MIDSCENE_DEBUG_MODE,
    MIDSCENE_CACHE,
)


class GlobalConfigManager:
    """全局配置管理器
    
    管理Midscene的全局环境变量配置
    """
    
    def __init__(self):
        """初始化全局配置管理器"""
        self._config_override: Dict[str, Optional[str]] = {}
        self._model_config_managers = []
    
    def get_env_config(self, key: str) -> Optional[str]:
        """获取单个环境配置
        
        Args:
            key: 配置键
            
        Returns:
            配置值或None
        """
        # 优先使用覆盖配置
        if key in self._config_override:
            return self._config_override[key]
        
        return os.environ.get(key)
    
    def get_env_config_in_boolean(self, key: str) -> bool:
        """获取布尔类型的环境配置
        
        Args:
            key: 配置键
            
        Returns:
            布尔值
        """
        value = self.get_env_config(key)
        if value is None:
            return False
        
        return value.lower() in ('true', '1', 'yes')
    
    def get_env_config_in_number(self, key: str) -> Optional[int]:
        """获取数字类型的环境配置
        
        Args:
            key: 配置键
            
        Returns:
            数字值或None
        """
        value = self.get_env_config(key)
        if value is None:
            return None
        
        try:
            return int(value)
        except ValueError:
            return None
    
    def get_all_env_config(self) -> Dict[str, Optional[str]]:
        """获取所有环境配置
        
        Returns:
            配置字典
        """
        result = {}
        for key in ALL_ENV_KEYS:
            result[key] = self.get_env_config(key)
        return result
    
    def override_config(self, config: Dict[str, Optional[str]]) -> None:
        """覆盖配置
        
        Args:
            config: 要覆盖的配置字典
        """
        self._config_override.update(config)
        
        # 通知所有注册的模型配置管理器清除缓存
        for manager in self._model_config_managers:
            try:
                manager.clear_model_config_map()
            except RuntimeError:
                pass  # 隔离模式下忽略
    
    def clear_override_config(self) -> None:
        """清除覆盖配置"""
        self._config_override.clear()
        
        # 通知所有注册的模型配置管理器清除缓存
        for manager in self._model_config_managers:
            try:
                manager.clear_model_config_map()
            except RuntimeError:
                pass
    
    def register_model_config_manager(self, manager: Any) -> None:
        """注册模型配置管理器
        
        Args:
            manager: ModelConfigManager实例
        """
        if manager not in self._model_config_managers:
            self._model_config_managers.append(manager)
            manager.register_global_config_manager(self)
    
    def is_debug_mode(self) -> bool:
        """检查是否为调试模式"""
        return self.get_env_config_in_boolean(MIDSCENE_DEBUG_MODE)
    
    def is_cache_enabled(self) -> bool:
        """检查是否启用缓存"""
        return self.get_env_config_in_boolean(MIDSCENE_CACHE)
