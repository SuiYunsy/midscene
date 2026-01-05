"""任务执行器"""
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
from .types import (
    PlanningAction, PlanningResponse, UIContext, ActionResult,
    ExecutionDump, ExecutionTask, TaskTiming, TaskStatus, LocateResult, Rect,
)
from .planning import plan, DEFAULT_ACTION_SPACE
from .conversation import ConversationHistory
from ..shared.config import Config, get_config
from ..shared.logger import get_logger
from ..shared.utils import sleep_ms
from ..shared.constants import MAX_ERROR_COUNT_IN_PLANNING_LOOP

logger = get_logger("task-executor")

class TaskExecutor:
    """任务执行器 - 负责执行规划的动作"""
    def __init__(
        self,
        get_context: Callable[[], Coroutine[Any, Any, UIContext]],
        action_handlers: Dict[str, Callable[..., Coroutine[Any, Any, Any]]],
        config: Optional[Config] = None,
    ):
        self.get_context = get_context
        self.action_handlers = action_handlers
        self.config = config or get_config()
        self.conversation_history = ConversationHistory(self.config.max_images_in_history)
        self.tasks: List[ExecutionTask] = []
        self.assert_results: List[Dict[str, Any]] = []
    async def execute_action(self, action: PlanningAction) -> ActionResult:
        """执行单个动作"""
        action_type = action.type
        handler = self.action_handlers.get(action_type)
        if not handler:
            return ActionResult(
                success=False,
                error=f"未知的动作类型: {action_type}",
            )
        try:
            # 处理定位参数 - 将bbox转换为实际坐标
            param = action.param.copy()
            context = await self.get_context()
            # 处理locate参数
            for key in ["locate", "from", "to"]:
                if key in param and isinstance(param[key], dict):
                    param[key] = self._resolve_locate(param[key], context.size)
            result = await handler(param)
            # 检查是否是断言动作
            if action_type == "Print_Assert_Result":
                self.assert_results.append({
                    "condition": param.get("condition", ""),
                    "thought": param.get("thought", ""),
                    "result": param.get("result", False),
                })
            return ActionResult(success=True, output=result)
        except Exception as e:
            logger.error(f"动作执行失败 {action_type}: {e}")
            return ActionResult(success=False, error=str(e))
    def _resolve_locate(self, locate_data: Dict[str, Any], size) -> LocateResult:
        """将定位数据转换为LocateResult"""
        prompt = locate_data.get("prompt", "")
        bbox = locate_data.get("bbox", [])
        # bbox格式: [left, top, right, bottom] 基于0-1000坐标
        if bbox and len(bbox) == 4:
            left = int(bbox[0] / 1000 * size.width)
            top = int(bbox[1] / 1000 * size.height)
            right = int(bbox[2] / 1000 * size.width)
            bottom = int(bbox[3] / 1000 * size.height)
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            return LocateResult(
                center=(center_x, center_y),
                rect=Rect(left=left, top=top, width=right - left, height=bottom - top),
                prompt=prompt,
                bbox=bbox,
            )
        # 如果没有bbox，使用屏幕中心
        center_x = size.width // 2
        center_y = size.height // 2
        return LocateResult(
            center=(center_x, center_y),
            rect=Rect(left=0, top=0, width=size.width, height=size.height),
            prompt=prompt,
        )
    async def ai_act(
        self,
        instruction: str,
        action_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行AI自动规划
        主循环：规划 -> 执行 -> 规划 -> 执行 ...
        """
        self.conversation_history.reset()
        self.assert_results.clear()
        replan_count = 0
        error_count = 0
        replan_limit = self.config.replanning_cycle_limit
        yaml_flow: List[Dict[str, Any]] = []
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        start_time = time.time()
        while True:
            # 获取当前上下文
            context = await self.get_context()
            # 执行规划
            plan_result = await plan(
                user_instruction=instruction,
                context=context,
                conversation_history=self.conversation_history,
                action_context=action_context,
                max_images=self.config.max_images_in_history,
                config=self.config,
            )
            # 累计token使用
            if plan_result.usage:
                total_usage["prompt_tokens"] += plan_result.usage.get("prompt_tokens", 0)
                total_usage["completion_tokens"] += plan_result.usage.get("completion_tokens", 0)
                total_usage["total_tokens"] += plan_result.usage.get("total_tokens", 0)
            logger.info(f"规划结果: {plan_result.log}")
            # 检查错误
            if plan_result.error:
                error_count += 1
                if error_count > MAX_ERROR_COUNT_IN_PLANNING_LOOP:
                    raise RuntimeError(f"规划循环中错误过多: {plan_result.error}")
                self.conversation_history.pending_feedback_message = f"Error: {plan_result.error}"
                continue
            # 执行动作
            action_error = False
            for action in plan_result.actions:
                logger.info(f"执行动作: {action.type} - {action.param}")
                result = await self.execute_action(action)
                if not result.success:
                    action_error = True
                    error_count += 1
                    self.conversation_history.pending_feedback_message = f"动作执行失败: {result.error}"
                    break
                # 记录yaml流程
                yaml_flow.append({
                    "action": action.type,
                    "param": action.param,
                })
            # 处理sleep
            if plan_result.sleep and plan_result.sleep > 0:
                logger.info(f"等待 {plan_result.sleep}ms")
                await sleep_ms(plan_result.sleep)
            # 检查是否完成
            if not plan_result.more_actions_needed and not action_error:
                break
            # 检查重规划次数
            replan_count += 1
            if replan_count > replan_limit:
                raise RuntimeError(f"重规划次数超过限制 ({replan_limit})")
            if error_count > MAX_ERROR_COUNT_IN_PLANNING_LOOP:
                raise RuntimeError("规划循环中错误过多")
            # 设置反馈消息
            if not self.conversation_history.pending_feedback_message and not action_error:
                self.conversation_history.pending_feedback_message = "I have finished the action previously planned."
        end_time = time.time()
        duration = int((end_time - start_time) * 1000)
        return {
            "success": True,
            "yaml_flow": yaml_flow,
            "usage": total_usage,
            "duration_ms": duration,
            "assert_results": self.assert_results,
        }
