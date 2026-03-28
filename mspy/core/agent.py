# -*- coding: utf-8 -*-
"""
Midscene Agent Module
Agent模块，提供高级AI驱动的自动化接口
"""

import time
from typing import Dict, Any, List, Optional, Callable, Union

from ..shared import (
    get_logger,
    ModelConfig,
    ModelConfigManager,
    global_model_config_manager,
    UIContext,
    Size,
    Rect,
    LocateResultElement,
    PlanningAction,
    ExecutionDump,
    GroupedActionDump,
    assert_condition,
    image_info_of_base64,
    resize_img_base64,
    TUserPrompt,
    get_env_int,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
)
from .device import AbstractInterface, define_action_assert
from .service import Service
from .task_executor import TaskExecutor
from .task_runner import TaskRunner

logger = get_logger("agent")

# 默认重新规划循环限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20


def _distance_of_two_points(p1: tuple, p2: tuple) -> int:
    """计算两点之间的距离"""
    import math
    x1, y1 = p1
    x2, y2 = p2
    return round(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))


def _included_in_rect(point: tuple, rect: Rect) -> bool:
    """检查点是否在矩形内"""
    x, y = point
    return (
        rect.left <= x <= rect.left + rect.width
        and rect.top <= y <= rect.top + rect.height
    )


class Agent:
    """
    Midscene Agent类
    提供AI驱动的自动化接口，支持aiAct和aiAssert等操作
    """
    
    def __init__(
        self,
        interface_instance: AbstractInterface,
        opts: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Agent
        
        Args:
            interface_instance: 设备接口实例
            opts: 选项配置
        """
        self.interface = interface_instance
        self.opts = opts or {}
        
        # 配置选项
        self.opts.setdefault("generateReport", True)
        self.opts.setdefault("autoPrintReportMsg", True)
        self.opts.setdefault("groupName", "Midscene Report")
        self.opts.setdefault("groupDescription", "")
        
        # 处理重新规划循环限制
        env_limit = get_env_int(MIDSCENE_REPLANNING_CYCLE_LIMIT)
        if self.opts.get("replanningCycleLimit") is None and env_limit:
            self.opts["replanningCycleLimit"] = env_limit
        
        # AI动作上下文
        self._ai_act_context = self.opts.get("aiActContext") or self.opts.get("aiActionContext")
        
        # 模型配置管理器
        model_config = self.opts.get("modelConfig")
        if model_config:
            self.model_config_manager = ModelConfigManager(model_config)
        else:
            self.model_config_manager = global_model_config_manager
        
        # 服务
        self.service = Service(self._get_ui_context)
        
        # 动作空间
        base_action_space = self.interface.action_space()
        full_action_space = base_action_space + [define_action_assert()]
        
        # 任务执行器
        self.task_executor = TaskExecutor(
            self.interface,
            self.service,
            {
                "onTaskStart": self._callback_on_task_start,
                "replanningCycleLimit": self.opts.get("replanningCycleLimit"),
                "actionSpace": full_action_space,
                "hooks": {
                    "onTaskUpdate": self._on_task_update,
                },
            },
        )
        
        # 执行转储
        self.dump: GroupedActionDump = self._reset_dump()
        
        # 状态
        self.destroyed = False
        self._screenshot_scale: Optional[float] = None
        self._frozen_ui_context: Optional[UIContext] = None
        self._dump_update_listeners: List[Callable] = []
        self._execution_dump_index_by_runner: Dict[int, int] = {}
    
    @property
    def page(self) -> AbstractInterface:
        """兼容性属性，返回interface"""
        return self.interface
    
    def _reset_dump(self) -> GroupedActionDump:
        """重置转储"""
        self.dump = GroupedActionDump(
            sdk_version="1.0.0-python",
            group_name=self.opts.get("groupName", ""),
            group_description=self.opts.get("groupDescription"),
            model_briefs=[],
            executions=[],
        )
        self._execution_dump_index_by_runner = {}
        return self.dump
    
    def _append_execution_dump(
        self,
        execution: ExecutionDump,
        runner: Optional[TaskRunner] = None,
    ) -> None:
        """追加执行转储"""
        if runner:
            runner_id = id(runner)
            existing_index = self._execution_dump_index_by_runner.get(runner_id)
            if existing_index is not None:
                self.dump.executions[existing_index] = execution
                return
            self.dump.executions.append(execution)
            self._execution_dump_index_by_runner[runner_id] = len(self.dump.executions) - 1
            return
        self.dump.executions.append(execution)
    
    async def _callback_on_task_start(self, task: Any) -> None:
        """任务开始回调"""
        on_task_start_tip = self.opts.get("onTaskStartTip")
        if on_task_start_tip:
            param = getattr(task, "param", None)
            param_str = str(param) if param else ""
            tip = f"{task.type} - {param_str}" if param_str else task.type
            await on_task_start_tip(tip)
    
    async def _on_task_update(
        self,
        runner: TaskRunner,
        error: Optional[Exception] = None,
    ) -> None:
        """任务更新回调"""
        execution_dump = runner.dump()
        self._append_execution_dump(execution_dump, runner)
        
        # 调用所有注册的dump更新监听器
        for listener in self._dump_update_listeners:
            try:
                listener(self.dump, execution_dump)
            except Exception as e:
                logger.error(f"Error in onDumpUpdate listener: {e}")
    
    async def _get_screenshot_scale(self, context: UIContext) -> float:
        """获取截图缩放比例"""
        if self._screenshot_scale is not None:
            return self._screenshot_scale
        
        page_width = context.size.width
        assert_condition(
            page_width and page_width > 0,
            f"Invalid page width when computing screenshot scale: {page_width}",
        )
        
        logger.debug("will get image info of base64")
        img_info = image_info_of_base64(context.screenshot_base64)
        screenshot_width = img_info["width"]
        logger.debug("image info of base64 done")
        
        assert_condition(
            screenshot_width and screenshot_width > 0,
            f"Invalid screenshot width: {screenshot_width}",
        )
        
        computed_scale = screenshot_width / page_width
        assert_condition(
            computed_scale > 0,
            f"Invalid computed screenshot scale: {computed_scale}",
        )
        
        logger.debug(
            f"Computed screenshot scale {computed_scale} from screenshot width {screenshot_width} and page width {page_width}"
        )
        
        self._screenshot_scale = computed_scale
        return self._screenshot_scale
    
    async def _get_ui_context(self, action: Optional[str] = None) -> UIContext:
        """获取UI上下文"""
        # 如果页面上下文被冻结，返回冻结的上下文
        if self._frozen_ui_context:
            logger.debug(f"Using frozen page context for action: {action}")
            return self._frozen_ui_context
        
        # 获取原始上下文
        if hasattr(self.interface, "get_context"):
            logger.debug(f"Using page.getContext for action: {action}")
            context = await self.interface.get_context()
        else:
            logger.debug("Using commonContextParser")
            screenshot = await self.interface.screenshot_base64()
            page_size = await self.interface.size()
            context = UIContext(
                screenshot_base64=screenshot,
                size=page_size,
            )
        
        logger.debug("will get screenshot scale")
        computed_scale = await self._get_screenshot_scale(context)
        logger.debug(f"computedScreenshotScale: {computed_scale}")
        
        if computed_scale != 1:
            logger.debug(f"Applying computed screenshot scale: {computed_scale:.4f}")
            target_width = round(context.size.width)
            target_height = round(context.size.height)
            logger.debug(f"Resizing screenshot to {target_width}x{target_height}")
            context.screenshot_base64 = resize_img_base64(
                context.screenshot_base64,
                {"width": target_width, "height": target_height},
            )
        else:
            logger.debug(f"screenshot scale={computed_scale}")
        
        return context
    
    def _resolve_replanning_cycle_limit(self, model_config: ModelConfig) -> int:
        """解析重新规划循环限制"""
        if self.opts.get("replanningCycleLimit") is not None:
            return self.opts["replanningCycleLimit"]
        return DEFAULT_REPLANNING_CYCLE_LIMIT
    
    async def get_action_space(self) -> List[Dict[str, Any]]:
        """获取动作空间"""
        common_assertion_action = define_action_assert()
        return self.interface.action_space() + [common_assertion_action]
    
    async def set_ai_act_context(self, prompt: str) -> None:
        """设置AI动作上下文"""
        if self._ai_act_context:
            logger.warning("aiActContext is already set, will override")
        self._ai_act_context = prompt
        self.opts["aiActContext"] = prompt
        self.opts["aiActionContext"] = prompt
    
    async def ai_act(
        self,
        task_prompt: str,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        执行AI驱动的动作
        
        Args:
            task_prompt: 任务提示
            opt: 选项
        
        Returns:
            执行结果
        """
        opt = opt or {}
        
        model_config_for_planning = self.model_config_manager.get_model_config("planning")
        default_intent_model_config = self.model_config_manager.get_model_config("default")
        
        include_bbox_in_planning = (
            model_config_for_planning.model_name == default_intent_model_config.model_name
            and model_config_for_planning.openai_base_url == default_intent_model_config.openai_base_url
        )
        logger.debug(f"setting includeBboxInPlanning to {include_bbox_in_planning}")
        
        cacheable = opt.get("cacheable")
        replanning_cycle_limit = self._resolve_replanning_cycle_limit(model_config_for_planning)
        
        images_include_count = 2
        
        result = await self.task_executor.action(
            task_prompt,
            model_config_for_planning,
            default_intent_model_config,
            include_bbox_in_planning,
            self._ai_act_context,
            cacheable,
            replanning_cycle_limit,
            images_include_count,
        )
        
        return result.get("output")
    
    async def ai_action(
        self,
        task_prompt: str,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        ai_act的别名（已弃用）
        
        Args:
            task_prompt: 任务提示
            opt: 选项
        
        Returns:
            执行结果
        """
        return await self.ai_act(task_prompt, opt)
    
    async def ai_assert(
        self,
        assertion: TUserPrompt,
        msg: Optional[str] = None,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        执行AI断言
        
        Args:
            assertion: 断言内容
            msg: 失败消息
            opt: 选项
        
        Returns:
            如果keepRawResponse为True，返回包含pass、thought、message的字典
        
        Raises:
            AssertionError: 当断言失败且keepRawResponse不为True时
        """
        opt = opt or {}
        model_config = self.model_config_manager.get_model_config("insight")
        
        service_opt = {
            "domIncluded": opt.get("domIncluded", False),
            "screenshotIncluded": opt.get("screenshotIncluded", True),
        }
        
        # 解析断言
        if isinstance(assertion, str):
            text_prompt = assertion
            assertion_text = assertion
        else:
            text_prompt = assertion.get("prompt", "")
            assertion_text = text_prompt
        
        try:
            result = await self.task_executor.create_type_query_execution(
                "Assert",
                text_prompt,
                model_config,
                service_opt,
            )
            
            output = result.get("output")
            thought = result.get("thought")
            
            passed = bool(output)
            message = None if passed else f"Assertion failed: {msg or assertion_text}\nReason: {thought or '(no_reason)'}"
            
            if opt.get("keepRawResponse"):
                return {
                    "pass": passed,
                    "thought": thought,
                    "message": message,
                }
            
            if not passed:
                raise AssertionError(message)
                
        except Exception as e:
            thought = getattr(e, "thought", None)
            raw_message = str(e)
            reason = thought or raw_message or "(no_reason)"
            message = f"Assertion failed: {msg or assertion_text}\nReason: {reason}"
            
            if opt.get("keepRawResponse"):
                return {
                    "pass": False,
                    "thought": thought,
                    "message": message,
                }
            
            raise AssertionError(message) from e
    
    async def ai(self, *args, **kwargs) -> Any:
        """ai_act的别名"""
        return await self.ai_act(*args, **kwargs)
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文"""
        logger.debug("Freezing page context")
        context = await self._get_ui_context()
        context._is_frozen = True
        self._frozen_ui_context = context
        logger.debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        logger.debug("Unfreezing page context")
        self._frozen_ui_context = None
        logger.debug("Page context unfrozen successfully")
    
    def add_dump_update_listener(
        self,
        listener: Callable,
    ) -> Callable:
        """
        添加dump更新监听器
        
        Args:
            listener: 监听器函数
        
        Returns:
            移除函数
        """
        self._dump_update_listeners.append(listener)
        
        def remove():
            self.remove_dump_update_listener(listener)
        
        return remove
    
    def remove_dump_update_listener(self, listener: Callable) -> None:
        """移除dump更新监听器"""
        if listener in self._dump_update_listeners:
            self._dump_update_listeners.remove(listener)
    
    def clear_dump_update_listeners(self) -> None:
        """清除所有dump更新监听器"""
        self._dump_update_listeners.clear()
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self.destroyed:
            return
        
        if hasattr(self.interface, "destroy") and self.interface.destroy:
            await self.interface.destroy()
        
        self._reset_dump()
        self.destroyed = True


def create_agent(
    interface_instance: AbstractInterface,
    opts: Optional[Dict[str, Any]] = None,
) -> Agent:
    """
    创建Agent实例
    
    Args:
        interface_instance: 设备接口实例
        opts: 选项
    
    Returns:
        Agent实例
    """
    return Agent(interface_instance, opts)
