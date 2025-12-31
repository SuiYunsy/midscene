"""任务执行器，负责调用模型规划并驱动设备动作。"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Optional

from .ai_model.conversation_history import ConversationHistory
from .ai_model.prompt.llm_planning import system_prompt_to_task_planning
from .ai_model.service_caller import call_ai_with_object_response
from .device import AbstractInterface
from .service import Service
from .types import ActionSpaceItem, ExecutionResult, PlanOutput, UIContext
from ..shared.env import ConfigManager, ModelConfig
from ..shared.logger import get_logger
from ..shared.utils import assert_true, compact_dict

logger = get_logger("task-executor")


class TaskExecutionError(Exception):
    """执行失败异常。"""


class TaskExecutor:
    def __init__(
        self,
        interface: AbstractInterface,
        service: Service,
        config: ConfigManager,
    ) -> None:
        self.interface = interface
        self.service = service
        self.config = config
        self.history = ConversationHistory()

    def _planning_model(self) -> ModelConfig:
        return self.config.model_config("planning")

    def _insight_model(self) -> ModelConfig:
        return self.config.model_config("insight")

    def _build_messages(
        self,
        instruction: str,
        context: UIContext,
        action_space: Iterable[ActionSpaceItem],
        include_bbox: bool,
    ) -> List[Dict[str, Any]]:
        system_prompt = system_prompt_to_task_planning(
            action_space=action_space,
            vl_mode=self._planning_model().family,
            include_bbox=include_bbox,
        )
        system_msg = {"role": "system", "content": system_prompt}
        user_content = [
            {"type": "text", "text": instruction},
            {
                "type": "image_url",
                "image_url": {"url": context.screenshot_base64, "detail": "high"},
            },
        ]
        if context.url:
            user_content.insert(0, {"type": "text", "text": f"URL: {context.url}"})
        user_msg = {"role": "user", "content": user_content}
        return [system_msg, user_msg, *self.history.snapshot(max_images=4)]

    def _apply_action(
        self, plan: PlanOutput, context: UIContext, model_config: ModelConfig
    ) -> ExecutionResult:
        action = plan.action or {}
        action_type = action.get("type") or ""
        param = action.get("param") or {}

        if action_type.lower() in ("tap", "click"):
            locate = param.get("locate") or {}
            bbox = locate.get("bbox")
            prompt = locate.get("prompt")
            if not bbox and prompt:
                locate_result = self.service.locate(str(prompt), model_config)
                bbox = locate_result.bbox
                param["locate"] = compact_dict(
                    {"prompt": prompt, "bbox": list(bbox), "center": locate_result.center}
                )
            if bbox:
                return ExecutionResult(
                    success=bool(
                        self.interface.perform_action(
                            "Tap", {"bbox": bbox}, context
                        )
                    ),
                    raw={"bbox": bbox},
                )
            raise TaskExecutionError("No bbox found for tap action")

        if action_type == "Print_Assert_Result":
            result = param.get("success", True)
            message = param.get("message", "Assertion finished")
            logger.info("Assert result: %s | %s", result, message)
            return ExecutionResult(success=bool(result), message=str(message))

        # 默认直接透传给接口
        res = self.interface.perform_action(action_type, param, context)
        return ExecutionResult(success=bool(res), raw=res)

    def run_ai_act(
        self, instruction: str, max_cycles: int = 3, include_bbox: bool = True
    ) -> PlanOutput:
        planning_model = self._planning_model()
        action_space = self.interface.action_space()
        assert_true(action_space, "Action space must not be empty")

        last_plan: Optional[PlanOutput] = None
        for cycle in range(max_cycles):
            context = self.interface.get_context()
            messages = self._build_messages(
                instruction, context, action_space, include_bbox=include_bbox
            )
            logger.info("Planning cycle %s started", cycle + 1)
            plan_response = call_ai_with_object_response(
                messages, planning_model
            )["content"]
            plan = PlanOutput(
                log=plan_response.get("log", ""),
                action=plan_response.get("action"),
                more_actions_needed_by_instruction=bool(
                    plan_response.get("more_actions_needed_by_instruction", False)
                ),
                sleep=plan_response.get("sleep"),
                error=plan_response.get("error"),
            )
            self.history.append({"role": "assistant", "content": plan.log})
            last_plan = plan

            if plan.error:
                raise TaskExecutionError(plan.error)
            if plan.sleep:
                time.sleep(plan.sleep / 1000)
            if plan.action:
                exec_result = self._apply_action(plan, context, planning_model)
                if not exec_result.success:
                    raise TaskExecutionError(exec_result.message or "Action failed")
            if not plan.more_actions_needed_by_instruction:
                return plan

        assert_true(last_plan is not None, "No plan produced")
        return last_plan

    def run_ai_assert(self, assertion: str) -> ExecutionResult:
        insight_model = self._insight_model()
        passed, thought = self.service.assert_text(assertion, insight_model)
        if not passed:
            raise TaskExecutionError(f"Assertion failed: {thought or assertion}")
        return ExecutionResult(success=True, message=thought)
