from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(path: str | Path) -> Dict[str, Any]:
    """
    加载 YAML 文件，返回字典。
    中文注释：简单封装，确保使用 safe_load，避免执行任意代码。
    """

    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
