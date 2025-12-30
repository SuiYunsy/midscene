from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from mspy.shared.config import RuntimeConfig
from mspy.shared.logger import get_logger
from mspy.shared.report import ReportCollector
from mspy.shared.yaml_loader import load_yaml
from mspy.shared.cache import InMemoryCache
from .agent import Agent, AgentOptions
from mspy.web_integration.playwright_adapter import PlaywrightInterface


class YamlScriptRunner:
    """
    YAML 脚本执行器。
    中文注释：解析 YAML -> 初始化 Playwright -> 调用 Agent 调度动作。
    """

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()
        self.logger = get_logger("mspy.yaml")

    def _load_tasks(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        tasks = script.get("tasks") or []
        if not isinstance(tasks, list):
            raise ValueError("tasks 必须是数组")
        return tasks

    def run(self, yaml_path: str | Path) -> ReportCollector:
        data = load_yaml(yaml_path)
        script_name = Path(yaml_path).stem
        reporter = ReportCollector(script_name=script_name, output_dir=Path(".mspy-output"))
        tasks = self._load_tasks(data)

        # 当前只支持 Web 平台
        target = data.get("target", data.get("web", {}))
        base_url = target.get("url") if isinstance(target, dict) else None
        runtime_config = self.config.merge({"base_url": base_url} if base_url else {})

        with PlaywrightInterface(config=runtime_config) as interface:
            cache = InMemoryCache()
            agent = Agent(interface=interface, options=AgentOptions(cache=cache, reporter=reporter))

            for task in tasks:
                flow = task.get("flow") or []
                if not flow:
                    self.logger.warning("任务缺少 flow，跳过")
                    continue
                agent.run_flow(flow)

        reporter.dump()
        return reporter
