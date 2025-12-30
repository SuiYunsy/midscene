"""
环境变量与模型配置读取。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 默认使用仓库根目录下的 .env
_ROOT = Path(__file__).resolve().parents[3]
_ENV_PATH = _ROOT / ".env"
load_dotenv(_ENV_PATH)


@dataclass
class ModelConfig:
    """模型配置，聚焦 Python 版本所需的核心字段。"""

    model: str
    base_url: Optional[str] = None
    temperature: float = 0.2
    timeout: int = 90
    vl_mode: Optional[str] = None


@dataclass
class EnvConfig:
    """全局环境配置。"""

    openai_api_key: str
    openai_base_url: Optional[str]
    model: str
    playwright_headless: bool = True

    @property
    def model_config(self) -> ModelConfig:
        return ModelConfig(
            model=self.model,
            base_url=self.openai_base_url,
        )


def load_env() -> EnvConfig:
    """加载 .env 配置，缺失必需字段时抛出异常。"""

    from os import getenv

    api_key = getenv("OPENAI_API_KEY")
    base_url = getenv("OPENAI_BASE_URL")
    model = getenv("MIDSCENE_MODEL", "gpt-4o-mini")
    headless_raw = getenv("PLAYWRIGHT_HEADLESS", "true").lower()
    headless = headless_raw not in {"0", "false", "no"}

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required. Please set it in .env before running.",
        )

    return EnvConfig(
        openai_api_key=api_key,
        openai_base_url=base_url,
        model=model,
        playwright_headless=headless,
    )
