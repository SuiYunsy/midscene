"""
环境变量与模型配置读取。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

def _find_repo_root() -> Path:
    """向上查找仓库根目录，避免硬编码层级。"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pnpm-workspace.yaml").exists():
            return parent
    raise RuntimeError("Failed to locate repository root; set MSPY_ENV_PATH to override.")


# 默认使用仓库根目录下的 .env，可通过环境变量覆盖
def _load_env_file() -> Path:
    from os import getenv

    override = getenv("MSPY_ENV_PATH")
    if override:
        env_path = Path(override).expanduser()
    else:
        env_path = _find_repo_root() / ".env"
    load_dotenv(env_path)
    return env_path


_ENV_PATH = _load_env_file()


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
