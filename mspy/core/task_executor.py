"""
任务执行器模块
Task executor for Midscene Python SDK
"""
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
import time

from ..shared import (
    get_debug,
    assert_value,
    sleep,
    UIContext,
    IModelConfig,
    PlanningAction,
    PlanningAIResponse,
    LocateResultElement,
)
from .device import AbstractInterface, DeviceAction, define_action_assert
from .service import Service
from .llm_planning import plan, AIActionType
from .conversation_history import ConversationHistory

debug = get_debug("device-task-executor")


class TaskExecutionError(Exception):
    """任务执行错误"""
    
    def __init__(self, message: str, error_task: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_task = error_task


@dataclass
class ExecutionResult:
    """执行结果"""
    output: Any = None
    thought: Optional[str] = None
    error: Optional[Exception] = None


class TaskExecutor:
    """
    任务执行器
    负责执行规划后的任务
    """
    
    def __init__(
        self,
        interface: AbstractInterface,
        service: Service,
        action_space: List[DeviceAction],
        replanning_cycle_limit: int = 20,
    ):
        """
        初始化任务执行器
        
        Args:
            interface: 设备接口
            service: 服务实例
            action_space: 动作空间
            replanning_cycle_limit: 重规划周期限制
        """
        self.interface = interface
        self.service = service
        self.action_space = action_space
        self.replanning_cycle_limit = replanning_cycle_limit
        self.conversation_history = ConversationHistory()
    
    def _get_action_space(self) -> List[DeviceAction]:
        """获取动作空间"""
        return self.action_space
    
    def _convert_action_space_for_prompt(self) -> List[Dict[str, Any]]:
        """将动作空间转换为提示词格式"""
        result = []
        for action in self.action_space:
            result.append({
                "name": action.name,
                "description": action.description,
                "param_schema": action.param_schema,
            })
        return result
    
    async def _execute_action(
        self,
        action: PlanningAction,
        context: UIContext,
    ) -> ExecutionResult:
        """
        执行单个动作
        
        Args:
            action: 规划动作
            context: UI上下文
            
        Returns:
            ExecutionResult
        """
        action_type = action.type
        param = action.param
        
        # 找到对应的动作定义
        action_def = next(
            (a for a in self.action_space if a.name == action_type),
            None
        )
        
        if not action_def:
            raise TaskExecutionError(f"Action type '{action_type}' not found in action space")
        
        if not action_def.call:
            raise TaskExecutionError(f"Action '{action_type}' has no call function defined")
        
        debug(f"Executing action: {action_type} with param: {param}")
        
        try:
            # 执行before钩子
            await self.interface.before_invoke_action(action_type, param)
            
            # 处理locate参数
            locate_param = param.get("locate")
            element = None
            
            if locate_param:
                # 如果有bbox，直接构建元素
                bbox = locate_param.get("bbox")
                if bbox and len(bbox) == 4:
                    xmin, ymin, xmax, ymax = bbox
                    from ..shared import Rect
                    element = LocateResultElement(
                        center=(int((xmin + xmax) / 2), int((ymin + ymax) / 2)),
                        rect=Rect(
                            left=xmin,
                            top=ymin,
                            width=xmax - xmin,
                            height=ymax - ymin,
                        ),
                        description=locate_param.get("prompt", ""),
                    )
                    # 更新param中的locate为解析后的元素
                    param["locate"] = element
            
            # 调用动作 - 大多数动作只需要param参数
            import inspect
            if inspect.iscoroutinefunction(action_def.call):
                result = await action_def.call(param)
            else:
                result = action_def.call(param)
            
            # 执行延迟
            if action_def.delay_after_runner > 0:
                await sleep(action_def.delay_after_runner)
            
            # 执行after钩子
            await self.interface.after_invoke_action(action_type, param)
            
            return ExecutionResult(output=result)
            
        except Exception as e:
            debug(f"Error executing action {action_type}: {e}")
            return ExecutionResult(error=e)
    
    async def action(
        self,
        user_prompt: str,
        model_config_for_planning: IModelConfig,
        model_config_for_default_intent: IModelConfig,
        include_bbox_in_planning: bool = True,
        ai_act_context: Optional[str] = None,
        cacheable: bool = True,
        replanning_cycle_limit_override: Optional[int] = None,
        images_include_count: Optional[int] = 2,
    ) -> ExecutionResult:
        """
        执行动作规划和执行
        
        Args:
            user_prompt: 用户提示
            model_config_for_planning: 规划模型配置
            model_config_for_default_intent: 默认意图模型配置
            include_bbox_in_planning: 是否在规划中包含bbox
            ai_act_context: AI动作上下文
            cacheable: 是否可缓存
            replanning_cycle_limit_override: 重规划周期限制覆盖
            images_include_count: 图片包含数量
            
        Returns:
            ExecutionResult
        """
        self.conversation_history.reset()
        
        replan_count = 0
        replanning_limit = replanning_cycle_limit_override or self.replanning_cycle_limit
        error_count_in_loop = 0
        max_error_count = 5
        
        # 主规划循环
        while True:
            # 获取UI上下文
            context = await self.service.context_retriever_fn()
            
            debug(f"Planning iteration {replan_count + 1}")
            
            # 获取动作空间
            action_space_for_prompt = self._convert_action_space_for_prompt()
            
            # 执行规划
            try:
                plan_result = await plan(
                    user_instruction=user_prompt,
                    context=context,
                    interface_type=self.interface.interface_type,
                    action_space=action_space_for_prompt,
                    model_config=model_config_for_planning,
                    conversation_history=self.conversation_history,
                    include_bbox=include_bbox_in_planning,
                    action_context=ai_act_context,
                    images_include_count=images_include_count,
                )
            except Exception as e:
                debug(f"Planning failed: {e}")
                raise TaskExecutionError(f"Planning failed: {e}")
            
            # 检查错误
            if plan_result.error:
                debug(f"Plan returned error: {plan_result.error}")
                raise TaskExecutionError(plan_result.error)
            
            # 获取规划的动作
            actions = plan_result.actions or []
            
            debug(f"Got {len(actions)} actions from planning")
            
            # 执行每个动作
            error_flag = False
            for action in actions:
                debug(f"Executing action: {action.type}, thought: {action.thought}")
                
                result = await self._execute_action(action, context)
                
                if result.error:
                    error_flag = True
                    error_count_in_loop += 1
                    self.conversation_history.pending_feedback_message = (
                        f"Error executing action: {result.error}"
                    )
                    debug(f"Action error: {result.error}, error count: {error_count_in_loop}")
                    break
            
            # 检查错误数量
            if error_count_in_loop > max_error_count:
                raise TaskExecutionError("Too many errors in one planning loop")
            
            # 处理sleep
            if plan_result.sleep and plan_result.sleep > 0:
                debug(f"Sleeping for {plan_result.sleep}ms")
                await sleep(plan_result.sleep)
            
            # 检查是否完成
            if not plan_result.more_actions_needed_by_instruction:
                if error_flag:
                    debug("more_actions_needed_by_instruction is false but there were errors, continuing")
                else:
                    debug("Task completed successfully")
                    break
            
            # 增加重规划计数
            replan_count += 1
            
            if replan_count > replanning_limit:
                raise TaskExecutionError(
                    f"Replanned {replanning_limit} times, exceeding the limit. "
                    "Please configure a larger value for replanningCycleLimit."
                )
            
            # 设置反馈消息
            if not self.conversation_history.pending_feedback_message:
                self.conversation_history.pending_feedback_message = (
                    "I have finished the action previously planned."
                )
        
        return ExecutionResult(output={"yamlFlow": []})
    
    async def wait_for(
        self,
        assertion: str,
        timeout_ms: int,
        check_interval_ms: int,
        model_config: IModelConfig,
    ) -> ExecutionResult:
        """
        等待断言成立
        
        Args:
            assertion: 断言
            timeout_ms: 超时时间（毫秒）
            check_interval_ms: 检查间隔（毫秒）
            model_config: 模型配置
            
        Returns:
            ExecutionResult
        """
        assert_value(assertion, "No assertion for waitFor")
        assert_value(timeout_ms, "No timeoutMs for waitFor")
        assert_value(check_interval_ms, "No checkIntervalMs for waitFor")
        assert_value(
            check_interval_ms <= timeout_ms,
            f"checkIntervalMs must be less than timeoutMs: {check_interval_ms} > {timeout_ms}"
        )
        
        start_time = int(time.time() * 1000)
        last_check_start = start_time
        error_thought = ""
        
        while last_check_start - start_time <= timeout_ms:
            current_check_start = int(time.time() * 1000)
            last_check_start = current_check_start
            
            # 获取上下文
            context = await self.service.context_retriever_fn()
            
            # 执行断言检查
            try:
                result = await self.service.extract(
                    {"StatementIsTruthy": f"Boolean, whether the following statement is true: {assertion}"},
                    model_config,
                )
                
                if result.get("data", {}).get("StatementIsTruthy"):
                    return ExecutionResult(output=None)
                
                error_thought = result.get("thought", f"Assertion not met: {assertion}")
                
            except Exception as e:
                error_thought = str(e)
            
            # 等待检查间隔
            now = int(time.time() * 1000)
            if now - current_check_start < check_interval_ms:
                await sleep(check_interval_ms - (now - current_check_start))
        
        raise TaskExecutionError(f"waitFor timeout: {error_thought}")
