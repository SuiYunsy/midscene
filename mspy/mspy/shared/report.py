from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import time


@dataclass
class StepResult:
    name: str
    status: str
    detail: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    def finish(self, status: str, detail: Optional[str] = None) -> None:
        self.status = status
        self.detail = detail
        self.finished_at = time.time()


@dataclass
class ScriptResult:
    script: str
    status: str = "init"
    steps: List[StepResult] = field(default_factory=list)
    output_path: Optional[Path] = None


class ReportCollector:
    """
    报告收集器：记录每个步骤的状态，可输出 JSON。
    中文注释：与 TS 版 report.ts 功能类似，但更轻量。
    """

    def __init__(self, script_name: str, output_dir: str | Path | None = None) -> None:
        self.result = ScriptResult(script=script_name)
        self.output_dir = Path(output_dir) if output_dir else None

    def start_step(self, name: str) -> StepResult:
        step = StepResult(name=name, status="running")
        self.result.steps.append(step)
        return step

    def mark_script_status(self, status: str) -> None:
        self.result.status = status

    def dump(self) -> Optional[Path]:
        if not self.output_dir:
            return None
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / f"{self.result.script}-report.json"
        data = {
            "script": self.result.script,
            "status": self.result.status,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status,
                    "detail": step.detail,
                    "started_at": step.started_at,
                    "finished_at": step.finished_at,
                }
                for step in self.result.steps
            ],
        }
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.result.output_path = output
        return output
