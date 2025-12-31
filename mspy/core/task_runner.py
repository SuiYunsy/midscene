# -*- coding: utf-8 -*-
"""
Midscene Task Runner Module
任务运行器模块，负责执行任务队列
"""

import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from ..shared import (
    get_logger,
    UIContext,
    ExecutionTask,
    ExecutionDump,
    ExecutionTaskTiming,
    assert_condition,
)

logger = get_logger("task-runner")

# UI上下文缓存TTL (毫秒)
UI_CONTEXT_CACHE_TTL_MS = 300


class TaskExecutionError(Exception):
    """任务执行错误"""
    
    def __init__(
        self,
        message: str,
        runner: "TaskRunner",
        error_task: Optional[ExecutionTask] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.runner = runner
        self.error_task = error_task
        self.cause = cause


@dataclass
class TaskRunnerOptions:
    """任务运行器选项"""
    tasks: List[ExecutionTask] = field(default_factory=list)
    on_task_start: Optional[Callable] = None
    on_task_update: Optional[Callable] = None


class TaskRunner:
    """任务运行器，负责执行任务队列"""
    
    def __init__(
        self,
        name: str,
        ui_context_builder: Callable,
        options: Optional[TaskRunnerOptions] = None,
    ):
        """
        初始化任务运行器
        
        Args:
            name: 运行器名称
            ui_context_builder: UI上下文构建函数
            options: 选项
        """
        self.name = name
        self.tasks: List[ExecutionTask] = []
        self.status = "init"  # init, pending, running, completed, error
        self._ui_context_builder = ui_context_builder
        self._on_task_start = options.on_task_start if options else None
        self._on_task_update = options.on_task_update if options else None
        self._last_ui_context: Optional[Dict[str, Any]] = None
        
        if options and options.tasks:
            for task in options.tasks:
                self.tasks.append(self._mark_task_as_pending(task))
            self.status = "pending" if self.tasks else "init"
    
    def _mark_task_as_pending(self, task: ExecutionTask) -> ExecutionTask:
        """将任务标记为待处理"""
        task.status = "pending"
        return task
    
    async def _emit_on_task_update(self, error: Optional[TaskExecutionError] = None) -> None:
        """触发任务更新回调"""
        if self._on_task_update:
            await self._on_task_update(self, error)
    
    async def _get_ui_context(self, force_refresh: bool = False) -> Optional[UIContext]:
        """获取UI上下文，带缓存"""
        now = int(time.time() * 1000)
        
        should_reuse = (
            not force_refresh
            and self._last_ui_context
            and now - self._last_ui_context.get("captured_at", 0) <= UI_CONTEXT_CACHE_TTL_MS
        )
        
        if should_reuse and self._last_ui_context:
            logger.debug(f"reuse cached uiContext captured {now - self._last_ui_context['captured_at']}ms ago")
            return self._last_ui_context.get("context")
        
        try:
            ui_context = await self._ui_context_builder()
            if ui_context:
                self._last_ui_context = {
                    "context": ui_context,
                    "captured_at": int(time.time() * 1000),
                }
            else:
                self._last_ui_context = None
            return ui_context
        except Exception as e:
            self._last_ui_context = None
            raise e
    
    async def _capture_screenshot(self) -> Optional[str]:
        """捕获截图"""
        try:
            ui_context = await self._get_ui_context(force_refresh=True)
            return ui_context.screenshot_base64 if ui_context else None
        except Exception as e:
            logger.error(f"error while capturing screenshot: {e}")
            return None
    
    def _attach_recorder_item(
        self,
        task: ExecutionTask,
        context_or_screenshot: Any,
        phase: str = "after-calling",
    ) -> None:
        """附加记录项到任务"""
        screenshot = (
            context_or_screenshot
            if isinstance(context_or_screenshot, str)
            else getattr(context_or_screenshot, "screenshot_base64", None)
        )
        
        if not screenshot:
            return
        
        recorder_item = {
            "type": "screenshot",
            "ts": int(time.time() * 1000),
            "screenshot": screenshot,
            "timing": phase,
        }
        
        if not task.recorder:
            task.recorder = []
        task.recorder.append(recorder_item)
    
    def _normalize_status_from_error(
        self,
        allow_when_error: bool = False,
        error_message: Optional[str] = None,
    ) -> None:
        """从错误状态恢复"""
        if self.status != "error":
            return
        
        default_msg = f"task runner is in error state, cannot proceed\nerror={self.latest_error_task()}"
        assert_condition(
            allow_when_error,
            error_message or default_msg,
        )
        
        # 重置运行器状态
        self.status = "pending" if self.tasks else "init"
    
    def _find_previous_non_sub_task_ui_context(
        self,
        current_index: int,
    ) -> Optional[UIContext]:
        """查找之前的非子任务UI上下文"""
        for i in range(current_index - 1, -1, -1):
            candidate = self.tasks[i]
            if candidate.sub_task:
                continue
            if candidate.ui_context:
                return candidate.ui_context
        return None
    
    async def append(
        self,
        task: Any,
        allow_when_error: bool = False,
    ) -> None:
        """
        追加任务
        
        Args:
            task: 任务或任务列表
            allow_when_error: 是否允许在错误状态下追加
        """
        self._normalize_status_from_error(
            allow_when_error,
            f"task runner is in error state, cannot append task\nerror={self.latest_error_task()}",
        )
        
        if isinstance(task, list):
            for t in task:
                self.tasks.append(self._mark_task_as_pending(t))
        else:
            self.tasks.append(self._mark_task_as_pending(task))
        
        if self.status != "running":
            self.status = "pending"
        
        await self._emit_on_task_update()
    
    async def append_and_flush(
        self,
        task: Any,
        allow_when_error: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """追加任务并执行"""
        await self.append(task, allow_when_error)
        return await self.flush(allow_when_error)
    
    async def flush(
        self,
        allow_when_error: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        执行所有待处理任务
        
        Args:
            allow_when_error: 是否允许在错误状态下执行
        
        Returns:
            最后一个任务的输出
        """
        if self.status == "init" and self.tasks:
            logger.warning("illegal state for task runner, status is init but tasks are not empty")
        
        self._normalize_status_from_error(allow_when_error, "task runner is in error state")
        assert_condition(self.status != "running", "task runner is already running")
        assert_condition(self.status != "completed", "task runner is already completed")
        
        # 查找下一个待处理任务
        next_pending_index = -1
        for i, task in enumerate(self.tasks):
            if task.status == "pending":
                next_pending_index = i
                break
        
        if next_pending_index < 0:
            return None
        
        self.status = "running"
        await self._emit_on_task_update()
        
        task_index = next_pending_index
        successfully_completed = True
        previous_find_output = None
        
        while task_index < len(self.tasks):
            task = self.tasks[task_index]
            assert_condition(
                task.status == "pending",
                f"task status should be pending, but got: {task.status}",
            )
            
            task.timing = ExecutionTaskTiming(start=int(time.time() * 1000))
            
            try:
                task.status = "running"
                await self._emit_on_task_update()
                
                # 调用任务开始回调
                if self._on_task_start:
                    try:
                        await self._on_task_start(task)
                    except Exception as e:
                        logger.error(f"error in onTaskStart: {e}")
                
                # 验证任务类型
                assert_condition(
                    task.type in ["Insight", "Action Space", "Planning"],
                    f"unsupported task type: {task.type}",
                )
                
                # 获取UI上下文
                ui_context = None
                if task.sub_task:
                    ui_context = self._find_previous_non_sub_task_ui_context(task_index)
                    assert_condition(
                        ui_context,
                        "subTask requires uiContext from previous non-subTask task",
                    )
                else:
                    ui_context = await self._get_ui_context()
                
                task.ui_context = ui_context
                
                # 构建执行上下文
                executor_context = {
                    "task": task,
                    "element": previous_find_output.get("element") if previous_find_output else None,
                    "uiContext": ui_context,
                }
                
                # 执行任务
                executor = getattr(task, "executor", None)
                assert_condition(executor, f"executor is required for task type: {task.type}")
                
                return_value = await executor(task.param, executor_context)
                
                # 处理返回值
                if return_value:
                    task.output = return_value.get("output")
                    task.log = return_value.get("log")
                    task.hit_by = return_value.get("hitBy")
                    
                    if task.sub_type == "Locate":
                        previous_find_output = return_value.get("output")
                
                # 最后一个任务时捕获截图
                if task_index == len(self.tasks) - 1:
                    screenshot = await self._capture_screenshot()
                    self._attach_recorder_item(task, screenshot, "after-calling")
                
                task.status = "finished"
                task.timing.end = int(time.time() * 1000)
                task.timing.cost = task.timing.end - task.timing.start
                await self._emit_on_task_update()
                task_index += 1
                
            except Exception as e:
                successfully_completed = False
                task.error = e
                task.error_message = str(e) or "error-without-message"
                task.error_stack = None  # Python不像JS那样有stack属性
                task.status = "failed"
                task.timing.end = int(time.time() * 1000)
                task.timing.cost = task.timing.end - task.timing.start
                await self._emit_on_task_update()
                break
        
        # 将剩余任务标记为取消
        for i in range(task_index + 1, len(self.tasks)):
            self.tasks[i].status = "cancelled"
        
        if task_index + 1 < len(self.tasks):
            await self._emit_on_task_update()
        
        finalize_error = None
        if not successfully_completed:
            self.status = "error"
            error_task = self.latest_error_task()
            message_base = (
                error_task.error_message
                if error_task
                else "Task execution failed"
            )
            finalize_error = TaskExecutionError(
                message_base,
                self,
                error_task,
                error_task.error if error_task else None,
            )
            await self._emit_on_task_update(finalize_error)
        else:
            self.status = "completed"
            await self._emit_on_task_update()
        
        if finalize_error:
            raise finalize_error
        
        if self.tasks:
            output_index = min(task_index, len(self.tasks) - 1)
            task = self.tasks[output_index]
            return {
                "thought": task.thought,
                "output": task.output,
            }
        
        return None
    
    def is_in_error_state(self) -> bool:
        """检查是否处于错误状态"""
        return self.status == "error"
    
    def latest_error_task(self) -> Optional[ExecutionTask]:
        """获取最新的错误任务"""
        if self.status != "error":
            return None
        
        for task in self.tasks:
            if task.status == "failed":
                return task
        
        return None
    
    def dump(self) -> ExecutionDump:
        """转储执行信息"""
        return ExecutionDump(
            log_time=int(time.time() * 1000),
            name=self.name,
            tasks=self.tasks,
        )
    
    async def append_error_plan(self, error_msg: str) -> Dict[str, Any]:
        """追加错误计划"""
        async def error_executor(param, context):
            raise Exception(error_msg or "error without thought")
        
        error_task = ExecutionTask(
            type="Action Space",
            sub_type="Error",
            param={"thought": error_msg},
            thought=error_msg,
        )
        error_task.executor = error_executor
        
        try:
            await self.append_and_flush(error_task)
        except:
            pass
        
        return {
            "output": None,
            "runner": self,
        }
