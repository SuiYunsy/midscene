"""
Agent 模块 - 核心的智能代理
Agent module - the core intelligent agent
"""
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable

from ..shared import (
    get_debug,
    assert_condition,
    sleep_ms,
    ModelConfig,
    ModelConfigManager,
    UIContext,
    PlanningAction,
    PlanningAIResponse,
    ExecutionTask,
    LocateResultElement,
    DetailedLocateParam,
    ServiceError,
    INTENT_DEFAULT,
    INTENT_PLANNING,
    get_env_int,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
)

from .device import AbstractInterface, DeviceAction, define_action_assert
from .service import Service
from .task_runner import TaskRunner, TaskExecutionError
from .conversation_history import ConversationHistory
from .llm_planning import plan

debug = get_debug("agent")

MAX_ERROR_COUNT_ALLOWED_IN_ONE_PLANNING_LOOP = 5


class Agent:
    """
    AI Agent for automated UI interactions.
    用于自动化UI交互的AI代理
    """
    
    def __init__(
        self,
        interface: AbstractInterface,
        model_config_manager: Optional[ModelConfigManager] = None,
        replanning_cycle_limit: Optional[int] = None,
        ai_act_context: Optional[str] = None,
        on_task_start: Optional[Callable[[ExecutionTask], Awaitable[None]]] = None,
    ):
        self.interface = interface
        self._model_config_manager = model_config_manager or ModelConfigManager()
        self._replanning_cycle_limit = (
            replanning_cycle_limit
            or get_env_int(MIDSCENE_REPLANNING_CYCLE_LIMIT)
            or 20
        )
        self._ai_act_context = ai_act_context
        self._on_task_start = on_task_start
        
        # Initialize service
        self._service = Service(self._context_retriever)
        
        # Initialize conversation history
        self._conversation_history = ConversationHistory()
    
    def _context_retriever(self) -> UIContext:
        """Get UI context synchronously."""
        # This should be called in async context with proper handling
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.interface.get_context())
    
    async def _context_retriever_async(self) -> UIContext:
        """Get UI context asynchronously."""
        return await self.interface.get_context()
    
    def _get_action_space(self) -> List[DeviceAction]:
        """Get action space from interface."""
        actions = self.interface.action_space()
        # Add assert action if not present
        has_assert = any(a.name == "Print_Assert_Result" for a in actions)
        if not has_assert:
            actions.append(define_action_assert())
        return actions
    
    def _get_model_config_for_planning(self) -> ModelConfig:
        """Get model config for planning intent."""
        return self._model_config_manager.get_model_config(INTENT_PLANNING)
    
    def _get_model_config_for_default(self) -> ModelConfig:
        """Get default model config."""
        return self._model_config_manager.get_model_config(INTENT_DEFAULT)
    
    async def ai_act(
        self,
        instruction: str,
        ai_act_context: Optional[str] = None,
        cacheable: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute an AI-driven action based on instruction.
        根据指令执行AI驱动的动作
        
        Args:
            instruction: The user instruction to execute
            ai_act_context: Additional context for the action
            cacheable: Whether to use cache
            
        Returns:
            Dict with output and runner
        """
        debug.info(f"Starting ai_act: {instruction}")
        
        self._conversation_history.reset()
        
        model_config_planning = self._get_model_config_for_planning()
        model_config_default = self._get_model_config_for_default()
        
        include_bbox = bool(model_config_planning.vl_mode)
        
        runner = TaskRunner(
            name=f"Action: {instruction}",
            ui_context_builder=self._context_retriever_async,
            on_task_start=self._on_task_start,
        )
        
        replan_count = 0
        error_count_in_planning_loop = 0
        
        action_context = ai_act_context or self._ai_act_context
        
        # Main planning loop
        while True:
            # Get UI context
            ui_context = await self.interface.get_context()
            
            # Plan next action
            debug.info(f"Planning next action (replan #{replan_count})")
            
            action_space = self._get_action_space()
            action_space_dicts = [
                {
                    "name": a.name,
                    "description": a.description,
                    "param_fields": a.param_fields,
                }
                for a in action_space
            ]
            
            plan_result = await plan(
                user_instruction=instruction,
                context=ui_context,
                action_space=action_space_dicts,
                model_config=model_config_planning,
                conversation_history=self._conversation_history,
                include_bbox=include_bbox,
                action_context=action_context,
            )
            
            debug.info(f"Plan result: {plan_result.log}")
            
            # Execute planned actions
            actions = plan_result.actions or []
            
            error_flag = False
            for action in actions:
                try:
                    await self._execute_action(action, action_space, ui_context)
                except Exception as e:
                    error_flag = True
                    error_count_in_planning_loop += 1
                    self._conversation_history.pending_feedback_message = (
                        f"Error executing action: {e}"
                    )
                    debug.warning(f"Error executing action: {e}")
                    break
            
            if error_count_in_planning_loop > MAX_ERROR_COUNT_ALLOWED_IN_ONE_PLANNING_LOOP:
                debug.error("Too many errors in one planning loop")
                raise Exception("Too many errors in one planning loop")
            
            # Check if complete
            if not plan_result.more_actions_needed_by_instruction:
                if error_flag:
                    debug.debug("More actions not needed but errors occurred, continuing")
                else:
                    break
            
            # Increment replan count
            replan_count += 1
            
            if replan_count > self._replanning_cycle_limit:
                raise Exception(
                    f"Replanned {self._replanning_cycle_limit} times, exceeding limit. "
                    "Configure larger replanningCycleLimit or MIDSCENE_REPLANNING_CYCLE_LIMIT."
                )
            
            if not self._conversation_history.pending_feedback_message:
                self._conversation_history.pending_feedback_message = (
                    "I have finished the action previously planned."
                )
        
        debug.info(f"ai_act completed: {instruction}")
        
        return {
            "output": {},
            "runner": runner,
        }
    
    async def _execute_action(
        self,
        action: PlanningAction,
        action_space: List[DeviceAction],
        ui_context: UIContext,
    ) -> None:
        """
        Execute a single action.
        执行单个动作
        """
        action_type = action.type
        action_param = action.param
        
        # Find action in action space
        device_action = None
        for a in action_space:
            if a.name == action_type:
                device_action = a
                break
        
        if not device_action:
            raise ValueError(f"Action type '{action_type}' not found")
        
        debug.info(f"Executing action: {action_type}")
        
        # Process locate params
        for field_info in device_action.param_fields:
            field_name = field_info.get("name")
            if field_info.get("is_locator") and field_name in action_param:
                locate_param = action_param[field_name]
                
                # If already has center/rect, use directly
                if isinstance(locate_param, dict) and "bbox" in locate_param:
                    # Convert bbox to LocateResultElement
                    bbox = locate_param["bbox"]
                    if bbox and len(bbox) >= 4:
                        center = (
                            (bbox[0] + bbox[2]) // 2,
                            (bbox[1] + bbox[3]) // 2,
                        )
                        from ..shared import Rect
                        rect = Rect(
                            left=bbox[0],
                            top=bbox[1],
                            width=bbox[2] - bbox[0],
                            height=bbox[3] - bbox[1],
                        )
                        action_param[field_name] = LocateResultElement(
                            center=center,
                            rect=rect,
                            description=locate_param.get("prompt", ""),
                        )
                elif isinstance(locate_param, dict) and "prompt" in locate_param:
                    # Need to locate the element
                    locate_result = await self._service.locate(
                        DetailedLocateParam(prompt=locate_param["prompt"]),
                        ui_context,
                        self._get_model_config_for_default(),
                    )
                    if locate_result.element:
                        action_param[field_name] = locate_result.element
                    else:
                        raise ValueError(f"Element not found: {locate_param['prompt']}")
        
        # Call before invoke action hook
        await self.interface.before_invoke_action(action_type, action_param)
        
        # Add small delay
        await asyncio.sleep(0.2)
        
        # Execute the action
        await device_action.call(action_param, {"ui_context": ui_context})
        
        # Add delay after action
        delay_ms = device_action.delay_after_runner
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
        
        # Call after invoke action hook
        await self.interface.after_invoke_action(action_type, action_param)
        
        debug.info(f"Action executed: {action_type}")
    
    async def ai_assert(
        self,
        assertion: str,
    ) -> Dict[str, Any]:
        """
        Perform an AI-driven assertion.
        执行AI驱动的断言
        
        Args:
            assertion: The assertion to verify
            
        Returns:
            Dict with result
        """
        debug.info(f"Starting ai_assert: {assertion}")
        
        # Use aiAct with assertion instruction
        result = await self.ai_act(
            instruction=f"Assert that: {assertion}",
        )
        
        return result
