"""轻量级任务运行器，负责包装 TaskExecutor。"""

from __future__ import annotations

from typing import Optional

from .tasks import TaskExecutionError, TaskExecutor
from ..shared.logger import get_logger

logger = get_logger("task-runner")


class TaskRunner:
    def __init__(self, executor: TaskExecutor) -> None:
        self.executor = executor

    def run_ai_act(self, instruction: str):
        logger.info("TaskRunner begin aiAct: %s", instruction)
        return self.executor.run_ai_act(instruction)

    def run_ai_assert(self, assertion: str):
        logger.info("TaskRunner begin aiAssert: %s", assertion)
        return self.executor.run_ai_assert(assertion)
