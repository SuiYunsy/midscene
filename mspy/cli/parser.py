"""YAML脚本解析器"""
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class YamlTask:
    """YAML任务"""
    name: str
    flow: List[Dict[str, Any]]
    continue_on_error: bool = False

@dataclass
class YamlWebConfig:
    """Web配置"""
    url: Optional[str] = None
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    user_data_dir: Optional[str] = None
    cookies: Optional[List[Dict[str, Any]]] = None
    local_storage: Optional[Dict[str, str]] = None
    wait_for_navigation_timeout: int = 10000
    wait_for_network_idle_timeout: int = 5000

@dataclass
class YamlScript:
    """YAML脚本"""
    tasks: List[YamlTask]
    web: Optional[YamlWebConfig] = None
    agent: Optional[Dict[str, Any]] = None

def parse_yaml_script(content: str, source: str = "yaml") -> YamlScript:
    """解析YAML脚本内容"""
    data = yaml.safe_load(content)
    if not data:
        raise ValueError(f"空的YAML脚本: {source}")
    # 解析web配置
    web_config = None
    web_data = data.get("web") or data.get("target")
    if web_data:
        web_config = YamlWebConfig(
            url=web_data.get("url"),
            headless=web_data.get("headless", True),
            viewport_width=web_data.get("viewWidth", 1280),
            viewport_height=web_data.get("viewHeight", 720),
            user_data_dir=web_data.get("userDataDir"),
            cookies=web_data.get("cookies"),
            local_storage=web_data.get("localStorage"),
            wait_for_navigation_timeout=web_data.get("waitForNavigationTimeout", 10000),
            wait_for_network_idle_timeout=web_data.get("waitForNetworkIdleTimeout", 5000),
        )
    # 解析任务列表
    tasks = []
    tasks_data = data.get("tasks", [])
    for task_data in tasks_data:
        task = YamlTask(
            name=task_data.get("name", "unnamed"),
            flow=task_data.get("flow", []),
            continue_on_error=task_data.get("continueOnError", False),
        )
        tasks.append(task)
    return YamlScript(
        tasks=tasks,
        web=web_config,
        agent=data.get("agent"),
    )

def load_yaml_file(filepath: str) -> YamlScript:
    """从文件加载YAML脚本"""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"YAML文件不存在: {filepath}")
    content = path.read_text(encoding="utf-8")
    return parse_yaml_script(content, filepath)
