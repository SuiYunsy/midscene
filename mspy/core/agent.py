"""Agent：暴露 aiAct / aiAssert API。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .device import AbstractInterface
from .service import Service
from .task_runner import TaskRunner
from .tasks import TaskExecutionError, TaskExecutor
from ..shared.env import ConfigManager, global_config
from ..shared.logger import get_logger

logger = get_logger("agent")


class Agent:
    def __init__(
        self,
        interface: AbstractInterface,
        opts: Optional[Dict[str, Any]] = None,
        config_manager: ConfigManager = global_config,
    ) -> None:
        self.interface = interface
        self.config_manager = config_manager
        self.service = Service(lambda: self.interface.get_context())
        self.executor = TaskExecutor(self.interface, self.service, self.config_manager)
        self.runner = TaskRunner(self.executor)
        self.opts = opts or {}
        self.dry_mode = bool(self.opts.get("dryMode", False))
        logger.info("Agent created for interface=%s", self.interface.interface_type)

    def aiAct(self, task_prompt: str):
        if self.dry_mode:
            logger.info("Dry mode enabled, skip aiAct")
            return None
        logger.info("aiAct start: %s", task_prompt)
        return self.runner.run_ai_act(task_prompt)

    def ai_assert(self, assertion: str):
        if self.dry_mode:
            logger.info("Dry mode enabled, skip aiAssert")
            return None
        logger.info("aiAssert start: %s", assertion)
        return self.runner.run_ai_assert(assertion)

    # 别名，兼容大小写
    aiAssert = ai_assert
