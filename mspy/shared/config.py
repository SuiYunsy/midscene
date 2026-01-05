"""配置管理模块"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv
from .constants import (
    ENV_MODEL_NAME, ENV_MODEL_BASE_URL, ENV_MODEL_API_KEY, ENV_MODEL_FAMILY,
    ENV_HTTP_PROXY, ENV_SOCKS_PROXY, ENV_SKIP_CERT_VERIFICATION,
    ENV_MAX_IMAGES_IN_HISTORY, ENV_REPLANNING_CYCLE_LIMIT,
    ENV_MODEL_TIMEOUT, ENV_MODEL_TEMPERATURE,
    DEFAULT_REPLANNING_CYCLE_LIMIT, DEFAULT_MAX_IMAGES_IN_HISTORY,
)

@dataclass
class Config:
    """模型配置类 - 仅支持qwen3-vl"""
    model_name: str = "qwen3-vl"
    model_base_url: str = ""
    model_api_key: str = ""
    model_family: str = "qwen3-vl"  # 固定为qwen3-vl
    http_proxy: Optional[str] = None
    socks_proxy: Optional[str] = None
    skip_cert_verification: bool = False
    max_images_in_history: int = DEFAULT_MAX_IMAGES_IN_HISTORY
    replanning_cycle_limit: int = DEFAULT_REPLANNING_CYCLE_LIMIT
    timeout: Optional[int] = None  # 毫秒
    temperature: float = 0.0
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        load_dotenv()
        skip_cert = os.getenv(ENV_SKIP_CERT_VERIFICATION, "false").lower() in ("true", "1", "yes")
        timeout_str = os.getenv(ENV_MODEL_TIMEOUT)
        timeout = int(timeout_str) if timeout_str else None
        temp_str = os.getenv(ENV_MODEL_TEMPERATURE)
        temperature = float(temp_str) if temp_str else 0.0
        max_images_str = os.getenv(ENV_MAX_IMAGES_IN_HISTORY)
        max_images = int(max_images_str) if max_images_str else DEFAULT_MAX_IMAGES_IN_HISTORY
        replanning_str = os.getenv(ENV_REPLANNING_CYCLE_LIMIT)
        replanning = int(replanning_str) if replanning_str else DEFAULT_REPLANNING_CYCLE_LIMIT
        return cls(
            model_name=os.getenv(ENV_MODEL_NAME, "qwen3-vl"),
            model_base_url=os.getenv(ENV_MODEL_BASE_URL, ""),
            model_api_key=os.getenv(ENV_MODEL_API_KEY, ""),
            model_family="qwen3-vl",  # 强制固定
            http_proxy=os.getenv(ENV_HTTP_PROXY),
            socks_proxy=os.getenv(ENV_SOCKS_PROXY),
            skip_cert_verification=skip_cert,
            max_images_in_history=max_images,
            replanning_cycle_limit=replanning,
            timeout=timeout,
            temperature=temperature,
        )

_global_config: Optional[Config] = None

def get_config() -> Config:
    """获取全局配置单例"""
    global _global_config
    if _global_config is None:
        _global_config = Config.from_env()
    return _global_config

def set_config(config: Config) -> None:
    """设置全局配置"""
    global _global_config
    _global_config = config
