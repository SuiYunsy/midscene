"""
环境配置测试
"""

import os
import pytest

from mspy.shared.env import (
    global_config_manager,
    ModelConfig,
    Intent,
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_BASE_URL,
)
from mspy.shared.env.types import (
    VlModeTypes,
    UITarsModelVersion,
    MODEL_ENV_KEYS,
    GLOBAL_ENV_KEYS,
    BOOLEAN_ENV_KEYS,
)
from mspy.shared.env.parse_model_config import (
    model_family_to_vl_config,
    parse_json,
    mask_config,
)


class TestTypes:
    """类型测试"""
    
    def test_intent_literal(self):
        """测试Intent类型"""
        intents: list[Intent] = ["insight", "planning", "default"]
        for intent in intents:
            assert intent in ("insight", "planning", "default")
    
    def test_model_config(self):
        """测试ModelConfig模型"""
        config = ModelConfig(
            model_name="gpt-4o",
            openai_api_key="test-key",
            openai_base_url="https://api.openai.com/v1",
            temperature=0.5,
        )
        
        assert config.model_name == "gpt-4o"
        assert config.openai_api_key == "test-key"
        assert config.temperature == 0.5
        assert config.intent == "default"


class TestParseModelConfig:
    """模型配置解析测试"""
    
    def test_model_family_to_vl_config_qwen(self):
        """测试qwen模型族转换"""
        vl_mode, version = model_family_to_vl_config("qwen2.5-vl")
        assert vl_mode == "qwen2.5-vl"
        assert version is None
    
    def test_model_family_to_vl_config_gemini(self):
        """测试gemini模型族转换"""
        vl_mode, version = model_family_to_vl_config("gemini")
        assert vl_mode == "gemini"
        assert version is None
    
    def test_model_family_to_vl_config_ui_tars(self):
        """测试ui-tars模型族转换"""
        vl_mode, version = model_family_to_vl_config("vlm-ui-tars")
        assert vl_mode == "vlm-ui-tars"
        assert version == UITarsModelVersion.V1_0
    
    def test_model_family_to_vl_config_none(self):
        """测试空模型族"""
        vl_mode, version = model_family_to_vl_config(None)
        assert vl_mode is None
        assert version is None
    
    def test_parse_json_valid(self):
        """测试有效JSON解析"""
        result = parse_json("test", '{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_parse_json_invalid(self):
        """测试无效JSON解析"""
        result = parse_json("test", "invalid json")
        assert result is None
    
    def test_parse_json_none(self):
        """测试空值解析"""
        result = parse_json("test", None)
        assert result is None
    
    def test_mask_config(self):
        """测试配置掩码"""
        config = {
            "model_name": "gpt-4o",
            "openai_api_key": "sk-1234567890abcdef",
            "api_key": "another-key",
        }
        
        masked = mask_config(config)
        
        assert masked["model_name"] == "gpt-4o"
        assert "****" in masked["openai_api_key"]
        assert masked["openai_api_key"].startswith("sk-1")


class TestGlobalConfigManager:
    """全局配置管理器测试"""
    
    def test_get_all_env_config(self):
        """测试获取所有环境配置"""
        config = global_config_manager.get_all_env_config()
        assert isinstance(config, dict)
    
    def test_env_keys_groups(self):
        """测试环境变量分组"""
        assert len(MODEL_ENV_KEYS) > 0
        assert len(GLOBAL_ENV_KEYS) > 0
        assert len(BOOLEAN_ENV_KEYS) > 0
