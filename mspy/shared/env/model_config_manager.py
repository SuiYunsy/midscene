"""
模型配置管理器

对应TypeScript源码: packages/shared/src/env/model-config-manager.ts
"""

import os
from typing import Any, Callable, Dict, Optional

from mspy.shared.env.types import (
    IModelConfig,
    TIntent,
    TModelConfig,
    CreateOpenAIClientFn,
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_BASE_URL,
    MIDSCENE_MODEL_TIMEOUT,
    MIDSCENE_MODEL_TEMPERATURE,
    MIDSCENE_MODEL_FAMILY,
    MIDSCENE_MODEL_HTTP_PROXY,
    MIDSCENE_MODEL_SOCKS_PROXY,
    MIDSCENE_INSIGHT_MODEL_NAME,
    MIDSCENE_INSIGHT_MODEL_API_KEY,
    MIDSCENE_INSIGHT_MODEL_BASE_URL,
    MIDSCENE_PLANNING_MODEL_NAME,
    MIDSCENE_PLANNING_MODEL_API_KEY,
    MIDSCENE_PLANNING_MODEL_BASE_URL,
    VL_MODE_RAW_VALID_VALUES,
)


class ModelConfigManager:
    """模型配置管理器
    
    负责管理和解析模型配置，支持不同intent的模型配置
    """
    
    def __init__(
        self,
        model_config: Optional[TModelConfig] = None,
        create_openai_client_fn: Optional[CreateOpenAIClientFn] = None
    ):
        """初始化模型配置管理器
        
        Args:
            model_config: 模型配置字典
            create_openai_client_fn: 自定义OpenAI客户端创建函数
        """
        self._model_config = model_config
        self._create_openai_client_fn = create_openai_client_fn
        self._model_config_map: Optional[Dict[str, IModelConfig]] = None
        self._is_initialized = False
        self._isolated_mode = False
        self._global_config_manager = None
    
    def _initialize(self) -> None:
        """初始化配置映射"""
        if self._is_initialized:
            return
        
        # 获取配置源
        if self._model_config:
            self._isolated_mode = True
            config_map = self._normalize_model_config(self._model_config)
        else:
            config_map = self._get_env_config()
        
        # 解析各个intent的配置
        default_config = self._decide_model_config("default", config_map)
        if not default_config:
            raise ValueError("默认模型配置未找到")
        
        insight_config = self._decide_model_config("insight", config_map) or default_config
        planning_config = self._decide_model_config("planning", config_map) or default_config
        
        # 添加自定义客户端创建函数
        default_config.create_openai_client = self._create_openai_client_fn
        insight_config.create_openai_client = self._create_openai_client_fn
        planning_config.create_openai_client = self._create_openai_client_fn
        
        self._model_config_map = {
            "default": default_config,
            "insight": insight_config,
            "planning": planning_config,
        }
        
        self._is_initialized = True
    
    def _normalize_model_config(self, config: TModelConfig) -> Dict[str, Optional[str]]:
        """标准化模型配置"""
        return {k: str(v) if v is not None else None for k, v in config.items()}
    
    def _get_env_config(self) -> Dict[str, Optional[str]]:
        """从环境变量获取配置"""
        if self._global_config_manager:
            return self._global_config_manager.get_all_env_config()
        return dict(os.environ)
    
    def _decide_model_config(self, intent: str, config_map: Dict[str, Optional[str]]) -> Optional[IModelConfig]:
        """根据intent决定模型配置
        
        Args:
            intent: 意图类型 (default, insight, planning)
            config_map: 配置映射
            
        Returns:
            模型配置对象
        """
        # 根据intent确定配置键前缀
        if intent == "insight":
            name_key = MIDSCENE_INSIGHT_MODEL_NAME
            api_key_key = MIDSCENE_INSIGHT_MODEL_API_KEY
            base_url_key = MIDSCENE_INSIGHT_MODEL_BASE_URL
        elif intent == "planning":
            name_key = MIDSCENE_PLANNING_MODEL_NAME
            api_key_key = MIDSCENE_PLANNING_MODEL_API_KEY
            base_url_key = MIDSCENE_PLANNING_MODEL_BASE_URL
        else:
            name_key = MIDSCENE_MODEL_NAME
            api_key_key = MIDSCENE_MODEL_API_KEY
            base_url_key = MIDSCENE_MODEL_BASE_URL
        
        # 获取模型名称
        model_name = config_map.get(name_key) or config_map.get(MIDSCENE_MODEL_NAME)
        
        if not model_name:
            if intent == "default":
                # 使用默认模型名称
                model_name = "gpt-4o"
            else:
                return None
        
        # 获取API密钥和Base URL
        api_key = config_map.get(api_key_key) or config_map.get(MIDSCENE_MODEL_API_KEY) or config_map.get("OPENAI_API_KEY")
        base_url = config_map.get(base_url_key) or config_map.get(MIDSCENE_MODEL_BASE_URL) or config_map.get("OPENAI_BASE_URL")
        
        # 获取其他配置
        timeout_str = config_map.get(MIDSCENE_MODEL_TIMEOUT)
        timeout = int(timeout_str) if timeout_str else None
        
        temp_str = config_map.get(MIDSCENE_MODEL_TEMPERATURE)
        temperature = float(temp_str) if temp_str else None
        
        # 检测VL模式
        vl_mode_raw = config_map.get(MIDSCENE_MODEL_FAMILY)
        vl_mode = self._parse_vl_mode(vl_mode_raw, config_map)
        
        return IModelConfig(
            model_name=model_name,
            model_description=f"{intent} model: {model_name}",
            intent=intent,
            openai_api_key=api_key,
            openai_base_url=base_url,
            http_proxy=config_map.get(MIDSCENE_MODEL_HTTP_PROXY),
            socks_proxy=config_map.get(MIDSCENE_MODEL_SOCKS_PROXY),
            timeout=timeout,
            temperature=temperature,
            vl_mode_raw=vl_mode_raw,
            vl_mode=vl_mode,
        )
    
    def _parse_vl_mode(self, vl_mode_raw: Optional[str], config_map: Dict[str, Optional[str]]) -> Optional[str]:
        """解析VL模式
        
        Args:
            vl_mode_raw: 原始VL模式值
            config_map: 配置映射
            
        Returns:
            解析后的VL模式
        """
        if vl_mode_raw and vl_mode_raw in VL_MODE_RAW_VALID_VALUES:
            # 映射特殊值
            if vl_mode_raw.startswith("vlm-ui-tars"):
                return "vlm-ui-tars"
            return vl_mode_raw
        
        # 检查旧版配置
        if config_map.get("MIDSCENE_USE_VLM_UI_TARS"):
            return "vlm-ui-tars"
        if config_map.get("MIDSCENE_USE_QWEN_VL"):
            return "qwen2.5-vl"
        if config_map.get("MIDSCENE_USE_QWEN3_VL"):
            return "qwen3-vl"
        if config_map.get("MIDSCENE_USE_DOUBAO_VISION"):
            return "doubao-vision"
        if config_map.get("MIDSCENE_USE_GEMINI"):
            return "gemini"
        
        return None
    
    def get_model_config(self, intent: str = "default") -> IModelConfig:
        """获取指定intent的模型配置
        
        Args:
            intent: 意图类型
            
        Returns:
            模型配置对象
        """
        if not self._is_initialized:
            self._initialize()
        
        if not self._model_config_map:
            raise RuntimeError("模型配置映射未初始化")
        
        config = self._model_config_map.get(intent)
        if not config:
            raise ValueError(f"未找到intent为 '{intent}' 的模型配置")
        
        return config
    
    def get_upload_test_server_url(self) -> Optional[str]:
        """获取上传测试服务器URL"""
        config = self.get_model_config("default")
        if config.openai_extra_config:
            return config.openai_extra_config.get("REPORT_SERVER_URL")
        return None
    
    def clear_model_config_map(self) -> None:
        """清除模型配置映射"""
        if self._isolated_mode:
            raise RuntimeError("隔离模式下不能清除配置映射")
        self._is_initialized = False
        self._model_config_map = None
    
    def register_global_config_manager(self, manager: Any) -> None:
        """注册全局配置管理器"""
        self._global_config_manager = manager
    
    def throw_error_if_non_vl_model(self) -> None:
        """如果不是VL模型则抛出错误"""
        config = self.get_model_config("default")
        if not config.vl_mode:
            raise ValueError(
                "MIDSCENE_MODEL_FAMILY未设置为视觉语言模型(VL model)，"
                "无法实现元素定位。请检查模型配置。"
            )
