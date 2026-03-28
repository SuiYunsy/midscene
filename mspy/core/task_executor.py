# -*- coding: utf-8 -*-
"""
Midscene Task Executor Module
任务执行器模块，负责协调任务的执行
"""

import time
from functools import partial
from typing import Dict, Any, List, Optional, Callable

from ..shared import (
    get_logger,
    ModelConfig,
    UIContext,
    ExecutionTask,
    ExecutionTaskTiming,
    PlanningAction,
    PlanningAIResponse,
    assert_condition,
    sleep_ms,
)
from .task_runner import TaskRunner, TaskRunnerOptions, TaskExecutionError
from .conversation_history import ConversationHistory
from .llm_planning import plan
from .service import Service
from .device import AbstractInterface, define_action_assert

logger = get_logger("device-task-executor")

# 单个规划循环中允许的最大错误次数
MAX_ERROR_COUNT_IN_PLANNING_LOOP = 5


class ExecutionSession:
    """执行会话，封装TaskRunner的创建和管理"""
    
    def __init__(
        self,
        title: str,
        ui_context_builder: Callable,
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化执行会话
        
        Args:
            title: 会话标题
            ui_context_builder: UI上下文构建函数
            options: 选项
        """
        self.title = title
        self._ui_context_builder = ui_context_builder
        
        runner_options = TaskRunnerOptions(
            tasks=options.get("tasks", []) if options else [],
            on_task_start=options.get("onTaskStart") if options else None,
            on_task_update=options.get("onTaskUpdate") if options else None,
        )
        
        self._runner = TaskRunner(title, ui_context_builder, runner_options)
    
    def get_runner(self) -> TaskRunner:
        """获取任务运行器"""
        return self._runner
    
    async def append(
        self,
        task: Any,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """追加任务"""
        allow_when_error = options.get("allowWhenError", False) if options else False
        await self._runner.append(task, allow_when_error)
    
    async def append_and_run(
        self,
        task: Any,
        options: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """追加任务并执行"""
        allow_when_error = options.get("allowWhenError", False) if options else False
        return await self._runner.append_and_flush(task, allow_when_error)
    
    async def append_error_plan(self, error_msg: str) -> Dict[str, Any]:
        """追加错误计划"""
        return await self._runner.append_error_plan(error_msg)


class TaskExecutor:
    """任务执行器，负责协调任务的执行"""
    
    def __init__(
        self,
        interface_instance: AbstractInterface,
        service: Service,
        opts: Dict[str, Any],
    ):
        """
        初始化任务执行器
        
        Args:
            interface_instance: 设备接口实例
            service: 服务实例
            opts: 选项
        """
        self.interface = interface_instance
        self.service = service
        self.on_task_start_callback = opts.get("onTaskStart")
        self.replanning_cycle_limit = opts.get("replanningCycleLimit")
        self._hooks = opts.get("hooks", {})
        self._conversation_history = ConversationHistory()
        self._provided_action_space = opts.get("actionSpace", [])
    
    def _create_execution_session(
        self,
        title: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExecutionSession:
        """创建执行会话"""
        return ExecutionSession(
            title,
            lambda: self.service.context_retriever_fn(),
            {
                "onTaskStart": self.on_task_start_callback,
                "tasks": options.get("tasks", []) if options else [],
                "onTaskUpdate": self._hooks.get("onTaskUpdate"),
            },
        )
    
    def _get_action_space(self) -> List[Dict[str, Any]]:
        """获取动作空间"""
        return self._provided_action_space
    
    async def action(
        self,
        user_prompt: str,
        model_config_for_planning: ModelConfig,
        model_config_for_default_intent: ModelConfig,
        include_bbox_in_planning: bool = True,
        ai_act_context: Optional[str] = None,
        cacheable: bool = True,
        replanning_cycle_limit_override: Optional[int] = None,
        images_include_count: Optional[int] = 2,
    ) -> Dict[str, Any]:
        """
        执行动作
        
        Args:
            user_prompt: 用户提示
            model_config_for_planning: 规划模型配置
            model_config_for_default_intent: 默认意图模型配置
            include_bbox_in_planning: 是否在规划中包含bbox
            ai_act_context: AI动作上下文
            cacheable: 是否可缓存
            replanning_cycle_limit_override: 重新规划循环限制覆盖
            images_include_count: 包含的图像数量
        
        Returns:
            执行结果
        """
        self._conversation_history.reset()
        
        session = self._create_execution_session(f"Action - {user_prompt}")
        runner = session.get_runner()
        
        replan_count = 0
        yaml_flow = []
        replanning_cycle_limit = replanning_cycle_limit_override or self.replanning_cycle_limit
        
        assert_condition(
            replanning_cycle_limit is not None,
            "replanningCycleLimit is required for TaskExecutor.action",
        )
        
        error_count_in_loop = 0
        
        # 主规划循环
        while True:
            # 创建规划任务
            async def planning_executor(param, executor_context):
                start_time = time.time()
                ui_context = executor_context.get("uiContext")
                assert_condition(ui_context, "uiContext is required for Planning task")
                
                action_space = self._get_action_space()
                logger.debug(f"actionSpace for this interface is: {', '.join(a.get('name', '') for a in action_space)}")
                assert_condition(isinstance(action_space, list), "actionSpace must be a list")
                
                if not action_space:
                    logger.warning(f"ActionSpace for {self.interface.interface_type} is empty")
                
                plan_result = await plan(
                    param.get("userInstruction"),
                    ui_context,
                    action_space,
                    model_config_for_planning,
                    self._conversation_history,
                    action_context=param.get("aiActContext"),
                    images_include_count=param.get("imagesIncludeCount"),
                )
                
                logger.debug(f"planResult: {plan_result}")
                
                executor_context["task"].log = executor_context["task"].log or {}
                executor_context["task"].log["rawResponse"] = plan_result.raw_response
                executor_context["task"].usage = plan_result.usage
                executor_context["task"].output = {
                    "actions": plan_result.actions,
                    "more_actions_needed_by_instruction": plan_result.more_actions_needed_by_instruction,
                    "log": plan_result.log,
                }
                
                # 处理sleep
                final_actions = list(plan_result.actions or [])
                if plan_result.sleep:
                    time_now = time.time()
                    time_remaining = plan_result.sleep - int((time_now - start_time) * 1000)
                    if time_remaining > 0:
                        final_actions.append(PlanningAction(
                            type="Sleep",
                            param={"timeMs": time_remaining},
                        ))
                
                assert_condition(
                    not plan_result.error,
                    f"Failed to continue: {plan_result.error}\n{plan_result.log or ''}",
                )
                
                return {"cache": {"hit": False}}
            
            planning_task = ExecutionTask(
                type="Planning",
                sub_type="Plan",
                param={
                    "userInstruction": user_prompt,
                    "aiActContext": ai_act_context,
                    "imagesIncludeCount": images_include_count,
                },
            )
            planning_task.executor = planning_executor
            
            result = await session.append_and_run(
                planning_task,
                {"allowWhenError": True},
            )
            
            plan_result = result.get("output") if result else None
            
            # 执行规划的动作
            plans = plan_result.get("actions", []) if plan_result else []
            
            # 转换计划为可执行任务
            try:
                executables = await self._convert_plan_to_executable(
                    plans,
                    model_config_for_planning,
                    model_config_for_default_intent,
                    {"cacheable": cacheable, "subTask": True},
                )
            except Exception as e:
                return await session.append_error_plan(
                    f"Error converting plans to executable tasks: {e}, plans: {plans}",
                )
            
            # 检查未消费的反馈消息
            if self._conversation_history.pending_feedback_message:
                logger.warning(
                    f"unconsumed pending feedback message detected: {self._conversation_history.pending_feedback_message}"
                )
            
            # 执行任务
            error_flag = False
            try:
                await session.append_and_run(executables)
            except Exception as e:
                error_flag = True
                error_count_in_loop += 1
                self._conversation_history.pending_feedback_message = f"Error executing running tasks: {str(e)}"
                logger.debug(
                    f"error when executing running tasks, current error count: {error_count_in_loop}"
                )
            
            if error_count_in_loop > MAX_ERROR_COUNT_IN_PLANNING_LOOP:
                return await session.append_error_plan("Too many errors in one planning loop")
            
            # 检查任务是否完成
            more_actions_needed = plan_result.get("more_actions_needed_by_instruction") if plan_result else False
            if not more_actions_needed:
                if error_flag:
                    logger.debug("more_actions_needed is false, but there are errors, continue")
                else:
                    break
            
            # 增加重新规划计数
            replan_count += 1
            
            if replan_count > replanning_cycle_limit:
                error_msg = f"Replanned {replanning_cycle_limit} times, exceeding the limit"
                return await session.append_error_plan(error_msg)
            
            if not self._conversation_history.pending_feedback_message:
                self._conversation_history.pending_feedback_message = "I have finished the action previously planned."
        
        return {
            "output": {"yamlFlow": yaml_flow},
            "runner": runner,
        }
    
    async def _convert_plan_to_executable(
        self,
        plans: List[PlanningAction],
        model_config_for_planning: ModelConfig,
        model_config_for_default_intent: ModelConfig,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[ExecutionTask]:
        """
        将规划动作转换为可执行任务
        
        Args:
            plans: 规划动作列表
            model_config_for_planning: 规划模型配置
            model_config_for_default_intent: 默认意图模型配置
            options: 选项
        
        Returns:
            可执行任务列表
        """
        tasks = []
        cacheable = options.get("cacheable") if options else None
        sub_task = options.get("subTask", False) if options else False
        
        action_space = self._get_action_space()
        
        for plan_action in plans:
            plan_type = plan_action.type
            
            if plan_type == "Finished":
                # 完成动作
                async def finished_executor(param, context):
                    pass
                
                task = ExecutionTask(
                    type="Action Space",
                    sub_type="Finished",
                    param=None,
                    thought=plan_action.thought,
                    sub_task=sub_task,
                )
                task.executor = finished_executor
                tasks.append(task)
                
            elif plan_type == "Sleep":
                # 睡眠动作
                time_ms = plan_action.param.get("timeMs", 3000) if plan_action.param else 3000
                
                # 使用工厂函数来捕获time_ms值
                def make_sleep_executor(sleep_time: int):
                    async def sleep_executor(param, context):
                        await sleep_ms(sleep_time)
                    return sleep_executor
                
                task = ExecutionTask(
                    type="Action Space",
                    sub_type="Sleep",
                    param=plan_action.param,
                    thought=plan_action.thought,
                    sub_task=sub_task,
                )
                task.executor = make_sleep_executor(time_ms)
                tasks.append(task)
                
            elif plan_type == "Locate":
                # 定位动作
                locate_param = plan_action.param
                
                async def locate_executor(param, context):
                    ui_context = context.get("uiContext")
                    assert_condition(
                        param.get("prompt") or param.get("bbox"),
                        f"No prompt or bbox to locate, param={param}",
                    )
                    
                    if not ui_context:
                        ui_context = await self.service.context_retriever_fn()
                    
                    assert_condition(ui_context, "uiContext is required for Locate task")
                    
                    # 如果有bbox，直接使用
                    if param.get("bbox"):
                        from .common import adapt_bbox_to_rect, generate_element_by_position
                        
                        rect = adapt_bbox_to_rect(
                            param["bbox"],
                            ui_context.size.width,
                            ui_context.size.height,
                            vl_mode=model_config_for_default_intent.vl_mode,
                        )
                        center = (rect.left + rect.width // 2, rect.top + rect.height // 2)
                        
                        from ..shared import LocateResultElement
                        element = LocateResultElement(
                            center=center,
                            rect=rect,
                            description=param.get("prompt", ""),
                        )
                        
                        return {
                            "output": {"element": element},
                            "hitBy": {"from": "Plan", "context": {"bbox": param["bbox"]}},
                        }
                    
                    # 否则调用AI定位
                    result = await self.service.locate(
                        param,
                        {"context": ui_context},
                        model_config_for_default_intent,
                    )
                    
                    return {
                        "output": {"element": result.get("element")},
                    }
                
                task = ExecutionTask(
                    type="Planning",
                    sub_type="Locate",
                    param=locate_param,
                    thought=plan_action.thought,
                    sub_task=sub_task,
                )
                task.executor = locate_executor
                tasks.append(task)
                
            else:
                # 查找动作定义
                action = next((a for a in action_space if a.get("name") == plan_type), None)
                
                if not action:
                    raise ValueError(f"Action type '{plan_type}' not found")
                
                param = plan_action.param or {}
                
                # 处理定位字段
                param_schema = action.get("param_schema", {})
                for field_name, field_info in param_schema.items():
                    if field_info.get("is_locator") and param.get(field_name):
                        # 创建定位任务
                        locate_param = param[field_name]
                        
                        async def locate_for_action(p, ctx, field=field_name, lp=locate_param):
                            ui_context = ctx.get("uiContext")
                            
                            if isinstance(lp, dict) and lp.get("bbox"):
                                from .common import adapt_bbox_to_rect
                                from ..shared import LocateResultElement
                                
                                rect = adapt_bbox_to_rect(
                                    lp["bbox"],
                                    ui_context.size.width,
                                    ui_context.size.height,
                                    vl_mode=model_config_for_default_intent.vl_mode,
                                )
                                center = (rect.left + rect.width // 2, rect.top + rect.height // 2)
                                
                                element = LocateResultElement(
                                    center=center,
                                    rect=rect,
                                    description=lp.get("prompt", ""),
                                )
                                
                                return {"output": {"element": element}}
                            
                            result = await self.service.locate(
                                lp,
                                {"context": ui_context},
                                model_config_for_default_intent,
                            )
                            return {"output": {"element": result.get("element")}}
                        
                        locate_task = ExecutionTask(
                            type="Planning",
                            sub_type="Locate",
                            param=locate_param,
                            sub_task=sub_task,
                        )
                        locate_task.executor = locate_for_action
                        tasks.append(locate_task)
                
                # 创建动作任务
                async def action_executor(p, ctx, act=action, pt=plan_type):
                    ui_context = ctx.get("uiContext")
                    assert_condition(ui_context, f"uiContext is required for Action task")
                    
                    element = ctx.get("element")
                    
                    # 执行动作
                    call_fn = act.get("call")
                    if call_fn:
                        # 替换定位字段为元素
                        action_param = dict(p)
                        for field_name, field_info in act.get("param_schema", {}).items():
                            if field_info.get("is_locator") and element:
                                action_param[field_name] = element
                        
                        await call_fn(action_param, ctx)
                    
                    # 延迟
                    delay = act.get("delay_after_runner", 300)
                    if delay > 0:
                        await sleep_ms(delay)
                    
                    return {"output": {"success": True, "action": pt, "param": p}}
                
                action_task = ExecutionTask(
                    type="Action Space",
                    sub_type=plan_type,
                    thought=plan_action.thought,
                    param=param,
                    sub_task=sub_task,
                )
                action_task.executor = action_executor
                tasks.append(action_task)
        
        return tasks
    
    async def create_type_query_execution(
        self,
        query_type: str,
        demand: Any,
        model_config: ModelConfig,
        opt: Optional[Dict[str, Any]] = None,
        multimodal_prompt: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建类型查询执行
        
        Args:
            query_type: 查询类型 (Query, Boolean, Number, String, Assert)
            demand: 数据需求
            model_config: 模型配置
            opt: 选项
            multimodal_prompt: 多模态提示
        
        Returns:
            执行结果
        """
        session = self._create_execution_session(f"{query_type} - {demand}")
        
        async def query_executor(param, context):
            task = context.get("task")
            ui_context = context.get("uiContext")
            assert_condition(ui_context, "uiContext is required for Query task")
            
            is_type_restricted = query_type != "Query"
            demand_input = demand
            key_of_result = "result"
            
            if is_type_restricted and query_type in ("Assert", "WaitFor"):
                key_of_result = "StatementIsTruthy"
                if query_type == "Assert":
                    demand_input = {key_of_result: f"Boolean, whether the following statement is true: {demand}"}
                else:
                    demand_input = {key_of_result: f"Boolean, the user wants to do some 'wait for' operation, please check whether the following statement is true: {demand}"}
            elif is_type_restricted:
                demand_input = {key_of_result: f"{query_type}, {demand}"}
            
            extract_result = await self.service.extract(
                demand_input,
                model_config,
                opt,
            )
            
            data = extract_result.get("data")
            usage = extract_result.get("usage")
            thought = extract_result.get("thought")
            dump = extract_result.get("dump")
            
            task.log = {"dump": dump}
            
            output_result = data
            if is_type_restricted:
                if isinstance(data, str):
                    output_result = data
                elif query_type == "WaitFor":
                    output_result = data.get(key_of_result) if data else False
                elif data is None:
                    output_result = None
                else:
                    assert_condition(
                        data.get(key_of_result) is not None,
                        "No result in query data",
                    )
                    output_result = data.get(key_of_result)
            
            if query_type == "Assert" and not output_result:
                task.usage = usage
                task.thought = thought
                raise AssertionError(f"Assertion failed: {thought}")
            
            return {
                "output": output_result,
                "log": dump,
                "usage": usage,
                "thought": thought,
            }
        
        query_task = ExecutionTask(
            type="Insight",
            sub_type=query_type,
            param={"dataDemand": demand},
        )
        query_task.executor = query_executor
        
        runner = session.get_runner()
        result = await session.append_and_run(query_task)
        
        if not result:
            raise RuntimeError("result of taskExecutor is undefined")
        
        return {
            "output": result.get("output"),
            "thought": result.get("thought"),
            "runner": runner,
        }
