"""环境配置与模型配置管理。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from .logger import get_logger

DEFAULT_MODEL_FAMILY = "qwen3-vl"  # override via .env
DEFAULT_MODEL_NAME = "Local-Qwen3-VL-235B-A22B"  # placeholder for quick start


@dataclass
class ModelConfig:
    """模型配置，兼容视觉模型与HTTP代理。"""

    model_name: str
    base_url: str
    api_key: str
    family: str = DEFAULT_MODEL_FAMILY
    http_proxy: Optional[str] = None
    timeout: int = 120
    temperature: float = 0.2

    def as_http_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


class ConfigManager:
    """简化后的全局配置管理器，剔除兼容与废弃字段。"""

    def __init__(self) -> None:
        load_dotenv()
        self.logger = get_logger("config")
        self._overrides: Dict[str, Any] = {}

    def override(self, values: Dict[str, Any]) -> None:
        """允许在运行时覆写配置。"""
        self.logger.info("Applying runtime config overrides")
        self._overrides.update({k: v for k, v in values.items() if v is not None})

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if key in self._overrides:
            return self._overrides[key]
        return os.getenv(key, default)

    def model_config(self, intent: str = "default") -> ModelConfig:
        """根据意图返回模型配置，planning/insight/default 共用主体配置。"""
        model_name = (
            self.get("MIDSCENE_MODEL_NAME") or self.get("MODEL_NAME") or DEFAULT_MODEL_NAME
        )
        base_url = self.get("MIDSCENE_MODEL_BASE_URL") or self.get("MODEL_BASE_URL")
        api_key = self.get("MIDSCENE_MODEL_API_KEY") or self.get("MODEL_API_KEY")
        family = self.get("MIDSCENE_MODEL_FAMILY") or DEFAULT_MODEL_FAMILY
        http_proxy = self.get("MIDSCENE_MODEL_HTTP_PROXY") or self.get("HTTP_PROXY")
        timeout_val = self.get("MIDSCENE_MODEL_TIMEOUT")
        temperature_val = self.get("MIDSCENE_MODEL_TEMPERATURE")

        if not base_url or not api_key:
            raise RuntimeError(
                "Missing model base url or api key. Please configure .env first."
            )

        timeout = int(timeout_val) if timeout_val else 120
        temperature = float(temperature_val) if temperature_val else 0.2

        self.logger.info(
            "Loaded model config | intent=%s | model=%s | family=%s | base=%s",
            intent,
            model_name,
            family,
            base_url,
        )

        return ModelConfig(
            model_name=model_name,
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            family=family,
            http_proxy=http_proxy,
            timeout=timeout,
            temperature=temperature,
        )


global_config = ConfigManager()
