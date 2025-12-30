from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from mspy.shared.cache import InMemoryCache
from mspy.shared.logger import get_logger
from mspy.shared.report import ReportCollector
from .action_space import ActionRequest, ActionResult


class AbstractInterface(Protocol):
    """
    Python 版统一动作空间接口，封装浏览器操作。
    """

    def navigate(self, url: str) -> None: ...
    def click(self, selector: str) -> None: ...
    def input(self, selector: str, text: str) -> None: ...
    def expect_text(self, selector: str, contains: str, timeout: int | None = None) -> None: ...
    def evaluate(self, script: str) -> Any: ...
    def sleep(self, ms: int) -> None: ...
    def screenshot(self, title: str | None = None) -> str: ...


@dataclass
class AgentOptions:
    cache: InMemoryCache
    reporter: ReportCollector


class Agent:
    """
    核心引擎：承接 YAML 任务，规划并调度动作。
    中文注释：保留与 TS 版相似的职责，但实现简化，避免 MCP 依赖。
    """

    def __init__(self, interface: AbstractInterface, options: AgentOptions) -> None:
        self.interface = interface
        self.cache = options.cache
        self.reporter = options.reporter
        self.logger = get_logger("mspy.agent")

    @staticmethod
    def _require_param(params: Dict[str, Any], key: str) -> Any:
        if key not in params:
            raise ValueError(f"缺少必填参数: {key}")
        return params[key]

    def call_action(self, request: ActionRequest) -> ActionResult:
        name = request.name.lower()
        params = request.params or {}
        self.logger.debug(f"call_action: {name} params={params}")

        def require(key: str) -> Any:
            if key not in params:
                raise ValueError(f"缺少必填参数: {key}")
            return params[key]

        try:
            if name in {"navigate", "goto"}:
                self.interface.navigate(self._require_param(params, "url"))
            elif name in {"click", "tap"}:
                self.interface.click(self._require_param(params, "selector"))
            elif name in {"input", "fill"}:
                self.interface.input(
                    self._require_param(params, "selector"), str(params.get("text", ""))
                )
            elif name in {"expect", "assert"}:
                self.interface.expect_text(
                    self._require_param(params, "selector"),
                    self._require_param(params, "contains"),
                    params.get("timeout"),
                )
            elif name in {"sleep", "wait"}:
                self.interface.sleep(int(params.get("ms", params.get("timeout", 0))))
            elif name in {"evaluate", "javascript"}:
                payload = self.interface.evaluate(self._require_param(params, "script"))
                return ActionResult(ok=True, payload=payload)
            elif name in {"screenshot", "capture"}:
                path = self.interface.screenshot(params.get("title"))
                return ActionResult(ok=True, payload=path)
            else:
                return ActionResult(ok=False, detail=f"未知动作: {request.name}")
        except (AssertionError, TimeoutError, ValueError, RuntimeError) as exc:
            return ActionResult(ok=False, detail=str(exc))

        return ActionResult(ok=True)

    def run_flow(self, flow: List[Dict[str, Any]]) -> None:
        for step in flow:
            # step 形如 {"navigate": {"url": "https://..."}} 或 {"click": {"selector": "#btn"}}
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"不支持的步骤格式: {step}")
            action_name, params = next(iter(step.items()))
            params = params or {}

            report_step = self.reporter.start_step(action_name)
            result = self.call_action(ActionRequest(name=action_name, params=params))
            if result.ok:
                report_step.finish("done")
            else:
                report_step.finish("error", result.detail)
                self.reporter.mark_script_status("error")
                raise RuntimeError(result.detail or "执行失败")

        self.reporter.mark_script_status("done")
