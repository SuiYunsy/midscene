"""
任务运行器

从 packages/core/src/task-runner.ts 迁移
"""

import time
import traceback
from typing import Any, Callable, Optional

from mspy.core.types import (
    ExecutionDump,
    ExecutionRecorderItem,
    ExecutionTask,
    ExecutionTaskTiming,
    UIContext,
)
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition


_debug = get_debug("task-runner")

# UI上下文缓存TTL（毫秒）
UI_CONTEXT_CACHE_TTL_MS = 300


class TaskExecutionError(Exception):
    """任务执行错误"""
    
    def __init__(
        self,
        message: str,
        runner: "TaskRunner",
        error_task: Optional[ExecutionTask] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.runner = runner
        self.error_task = error_task
        self.cause = cause


class TaskRunner:
    """任务运行器"""
    
    def __init__(
        self,
        name: str,
        ui_context_builder: Callable[[], UIContext],
        on_task_start: Optional[Callable[[ExecutionTask], None]] = None,
        on_task_update: Optional[Callable[["TaskRunner", Optional[TaskExecutionError]], None]] = None,
        tasks: Optional[list[dict[str, Any]]] = None,
    ):
        self.name = name
        self.tasks: list[ExecutionTask] = []
        self.status: str = "init"
        self.on_task_start = on_task_start
        self._ui_context_builder = ui_context_builder
        self._on_task_update = on_task_update
        self._last_ui_context: Optional[dict[str, Any]] = None
        
        if tasks:
            for task_data in tasks:
                self.tasks.append(self._mark_task_as_pending(task_data))
            self.status = "pending" if self.tasks else "init"
    
    def _mark_task_as_pending(self, task_data: dict[str, Any]) -> ExecutionTask:
        """将任务标记为待处理"""
        return ExecutionTask(
            type=task_data.get("type", "Insight"),
            status="pending",
            sub_type=task_data.get("sub_type"),
            sub_task=task_data.get("sub_task", False),
            param=task_data.get("param"),
            thought=task_data.get("thought"),
        )
    
    async def _emit_on_task_update(
        self,
        error: Optional[TaskExecutionError] = None
    ) -> None:
        """触发任务更新回调"""
        if self._on_task_update:
            self._on_task_update(self, error)
    
    async def _get_ui_context(
        self,
        force_refresh: bool = False
    ) -> Optional[UIContext]:
        """获取UI上下文"""
        now = int(time.time() * 1000)
        
        # 检查是否可以复用缓存
        should_reuse = (
            not force_refresh and
            self._last_ui_context and
            now - self._last_ui_context["captured_at"] <= UI_CONTEXT_CACHE_TTL_MS
        )
        
        if should_reuse and self._last_ui_context:
            _debug(
                f"reuse cached uiContext captured "
                f"{now - self._last_ui_context['captured_at']}ms ago"
            )
            return self._last_ui_context["context"]
        
        try:
            ui_context = self._ui_context_builder()
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
            print(f"error while capturing screenshot: {e}")
        return None
    
    def _attach_recorder_item(
        self,
        task: ExecutionTask,
        screenshot: Optional[str],
        phase: str
    ) -> None:
        """附加记录项"""
        if not screenshot:
            return
        
        recorder_item = ExecutionRecorderItem(
            type="screenshot",
            ts=int(time.time() * 1000),
            screenshot=screenshot,
            timing=phase,
        )
        
        if not task.recorder:
            task.recorder = []
        task.recorder.append(recorder_item)
    
    def _normalize_status_from_error(
        self,
        allow_when_error: bool = False,
        error_message: Optional[str] = None
    ) -> None:
        """从错误状态恢复"""
        if self.status != "error":
            return
        
        default_msg = (
            f"task runner is in error state, cannot proceed\n"
            f"error={self.latest_error_task().error if self.latest_error_task() else None}"
        )
        assert_condition(allow_when_error, error_message or default_msg)
        
        self.status = "pending" if self.tasks else "init"
    
    async def append(
        self,
        task: dict[str, Any] | list[dict[str, Any]],
        allow_when_error: bool = False
    ) -> None:
        """添加任务"""
        self._normalize_status_from_error(
            allow_when_error,
            f"task runner is in error state, cannot append task"
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
        task: dict[str, Any] | list[dict[str, Any]],
        allow_when_error: bool = False
    ) -> Optional[dict[str, Any]]:
        """添加并执行任务"""
        await self.append(task, allow_when_error)
        return await self.flush(allow_when_error)
    
    async def flush(
        self,
        allow_when_error: bool = False
    ) -> Optional[dict[str, Any]]:
        """执行所有待处理任务"""
        if self.status == "init" and self.tasks:
            print(
                "illegal state for task runner, "
                "status is init but tasks are not empty"
            )
        
        self._normalize_status_from_error(
            allow_when_error,
            "task runner is in error state"
        )
        assert_condition(self.status != "running", "task runner is already running")
        assert_condition(self.status != "completed", "task runner is already completed")
        
        # 找到下一个待处理的任务
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
        
        while task_index < len(self.tasks):
            task = self.tasks[task_index]
            assert_condition(
                task.status == "pending",
                f"task status should be pending, but got: {task.status}"
            )
            
            task.timing = ExecutionTaskTiming(start=int(time.time() * 1000))
            
            try:
                task.status = "running"
                await self._emit_on_task_update()
                
                # 调用任务开始回调
                if self.on_task_start:
                    try:
                        self.on_task_start(task)
                    except Exception as e:
                        print(f"error in on_task_start: {e}")
                
                # TODO: 执行任务逻辑（需要executor）
                # 这里暂时只是模拟
                _debug(f"executing task: {task.type}")
                
                # 最后一个任务，捕获截图
                is_last_task = task_index == len(self.tasks) - 1
                if is_last_task:
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
                task.error_message = str(e)
                task.error_stack = traceback.format_exc()
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
        
        finalize_error: Optional[TaskExecutionError] = None
        if not successfully_completed:
            self.status = "error"
            error_task = self.latest_error_task()
            message_base = (
                error_task.error_message
                if error_task and error_task.error_message
                else "Task execution failed"
            )
            stack = error_task.error_stack if error_task else None
            message = f"{message_base}\n{stack}" if stack else message_base
            finalize_error = TaskExecutionError(
                message, self, error_task,
                cause=error_task.error if error_task else None
            )
            await self._emit_on_task_update(finalize_error)
        else:
            self.status = "completed"
            await self._emit_on_task_update()
        
        if finalize_error:
            raise finalize_error
        
        if self.tasks:
            output_index = min(task_index, len(self.tasks) - 1)
            return {
                "thought": self.tasks[output_index].thought,
                "output": self.tasks[output_index].output,
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
        """导出Dump数据"""
        return ExecutionDump(
            log_time=int(time.time() * 1000),
            name=self.name,
            tasks=self.tasks,
        )
    
    async def append_error_plan(self, error_msg: str) -> dict[str, Any]:
        """添加错误计划"""
        error_task = {
            "type": "Action Space",
            "sub_type": "Error",
            "param": {"thought": error_msg},
            "thought": error_msg,
        }
        await self.append_and_flush(error_task)
        
        return {
            "output": None,
            "runner": self,
        }
