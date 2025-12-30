from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RuntimeConfig:
    """
    运行时配置，统一入口。

    中文注释：封装常见的环境参数，避免到处传递松散的 dict。
    """

    headless: bool = True
    base_url: Optional[str] = None
    timeout: int = 30_000
    extra: Dict[str, Any] = field(default_factory=dict)

    def merge(self, override: Dict[str, Any] | None) -> "RuntimeConfig":
        """合并用户覆盖参数，返回新的配置实例。"""
        if not override:
            return self
        merged = {**self.__dict__, **override}
        merged_extra = {**self.extra, **(override.get("extra", {}) or {})}
        merged["extra"] = merged_extra
        return RuntimeConfig(**merged)
