"""
任务运行器模块
Task runner module
"""
import time
from typing import Any, Dict, List, Optional, Callable, Awaitable

from ..shared import (
    get_debug,
    assert_condition,
    UIContext,
    ExecutionTask,
    ExecutionDump,
    LocateResultElement,
)

debug = get_debug("task-runner")

UI_CONTEXT_CACHE_TTL_MS = 300


class TaskExecutionError(Exception):
    """Task execution error with context."""
    
    def __init__(
        self,
        message: str,
        runner: "TaskRunner",
        error_task: Optional[ExecutionTask] = None,
    ):
        super().__init__(message)
        self.runner = runner
        self.error_task = error_task


class TaskRunner:
    """
    Task runner for executing a sequence of tasks.
    用于执行任务序列的任务运行器
    """
    
    def __init__(
        self,
        name: str,
        ui_context_builder: Callable[[], Awaitable[UIContext]],
        on_task_start: Optional[Callable[[ExecutionTask], Awaitable[None]]] = None,
        on_task_update: Optional[Callable[["TaskRunner", Optional[TaskExecutionError]], Awaitable[None]]] = None,
        tasks: Optional[List[ExecutionTask]] = None,
    ):
        self.name = name
        self.tasks: List[ExecutionTask] = tasks or []
        self.status: str = "pending" if tasks else "init"
        self.on_task_start = on_task_start
        self._ui_context_builder = ui_context_builder
        self._on_task_update = on_task_update
        self._last_ui_context: Optional[Dict[str, Any]] = None
    
    async def _emit_on_task_update(self, error: Optional[TaskExecutionError] = None) -> None:
        """Emit task update event."""
        if self._on_task_update:
            await self._on_task_update(self, error)
    
    async def _get_ui_context(self, force_refresh: bool = False) -> Optional[UIContext]:
        """Get UI context with caching."""
        now = int(time.time() * 1000)
        
        should_reuse = (
            not force_refresh
            and self._last_ui_context
            and now - self._last_ui_context["captured_at"] <= UI_CONTEXT_CACHE_TTL_MS
        )
        
        if should_reuse and self._last_ui_context:
            debug.debug(
                f"Reusing cached UI context captured {now - self._last_ui_context['captured_at']}ms ago"
            )
            return self._last_ui_context["context"]
        
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
        except Exception:
            self._last_ui_context = None
            raise
    
    async def _capture_screenshot(self) -> Optional[str]:
        """Capture screenshot."""
        try:
            ui_context = await self._get_ui_context(force_refresh=True)
            return ui_context.screenshot_base64 if ui_context else None
        except Exception as e:
            debug.error(f"Error while capturing screenshot: {e}")
            return None
    
    def _mark_task_as_pending(self, task: ExecutionTask) -> ExecutionTask:
        """Mark a task as pending."""
        task.status = "pending"
        return task
    
    def _normalize_status_from_error(
        self,
        allow_when_error: bool = False,
        error_message: Optional[str] = None,
    ) -> None:
        """Normalize status from error state."""
        if self.status != "error":
            return
        
        if not allow_when_error:
            error_task = self.latest_error_task()
            raise AssertionError(
                error_message
                or f"Task runner is in error state, cannot proceed. "
                f"Error: {error_task.error_message if error_task else 'unknown'}"
            )
        
        # Reset runner state so new tasks can run
        self.status = "pending" if self.tasks else "init"
    
    async def append(
        self,
        task: ExecutionTask | List[ExecutionTask],
        allow_when_error: bool = False,
    ) -> None:
        """Append task(s) to the runner."""
        self._normalize_status_from_error(
            allow_when_error,
            f"Task runner is in error state, cannot append task"
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
        task: ExecutionTask | List[ExecutionTask],
        allow_when_error: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Append task(s) and flush."""
        await self.append(task, allow_when_error)
        return await self.flush(allow_when_error)
    
    async def flush(
        self,
        allow_when_error: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Flush and execute pending tasks.
        执行待处理的任务
        """
        if self.status == "init" and self.tasks:
            debug.warning("Illegal state: status is init but tasks are not empty")
        
        self._normalize_status_from_error(allow_when_error, "Task runner is in error state")
        assert_condition(self.status != "running", "Task runner is already running")
        assert_condition(self.status != "completed", "Task runner is already completed")
        
        # Find next pending task
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
        previous_locate_output: Optional[LocateResultElement] = None
        
        while task_index < len(self.tasks):
            task = self.tasks[task_index]
            assert_condition(
                task.status == "pending",
                f"Task status should be pending, got: {task.status}"
            )
            
            start_time = int(time.time() * 1000)
            
            try:
                task.status = "running"
                await self._emit_on_task_update()
                
                if self.on_task_start:
                    try:
                        await self.on_task_start(task)
                    except Exception as e:
                        debug.error(f"Error in on_task_start: {e}")
                
                # Get UI context
                ui_context = await self._get_ui_context()
                
                # Execute task
                executor = getattr(task, "executor", None)
                if executor:
                    executor_context = {
                        "task": task,
                        "element": previous_locate_output,
                        "ui_context": ui_context,
                    }
                    result = await executor(task.param, executor_context)
                    
                    if result:
                        task.output = result.get("output")
                        if task.sub_type == "Locate":
                            previous_locate_output = result.get("output", {}).get("element")
                
                task.status = "finished"
                end_time = int(time.time() * 1000)
                
                await self._emit_on_task_update()
                task_index += 1
                
            except Exception as e:
                successfully_completed = False
                task.error = e
                task.error_message = str(e)
                task.status = "failed"
                
                await self._emit_on_task_update()
                break
        
        # Set remaining tasks as cancelled
        for i in range(task_index + 1, len(self.tasks)):
            self.tasks[i].status = "cancelled"
        
        if task_index + 1 < len(self.tasks):
            await self._emit_on_task_update()
        
        finalize_error: Optional[TaskExecutionError] = None
        if not successfully_completed:
            self.status = "error"
            error_task = self.latest_error_task()
            message = (
                error_task.error_message if error_task else "Task execution failed"
            )
            finalize_error = TaskExecutionError(message, self, error_task)
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
        """Check if runner is in error state."""
        return self.status == "error"
    
    def latest_error_task(self) -> Optional[ExecutionTask]:
        """Get the latest error task."""
        if self.status != "error":
            return None
        
        for task in self.tasks:
            if task.status == "failed":
                return task
        
        return None
    
    def dump(self) -> ExecutionDump:
        """Dump execution data."""
        return ExecutionDump(
            log_time=int(time.time() * 1000),
            name=self.name,
            tasks=self.tasks,
        )
    
    async def append_error_plan(self, error_msg: str) -> Dict[str, Any]:
        """Append an error plan task."""
        error_task = ExecutionTask(
            type="Action Space",
            sub_type="Error",
            param={"thought": error_msg},
            thought=error_msg,
        )
        
        async def error_executor(param: Any, context: Any) -> None:
            raise Exception(error_msg or "Error without thought")
        
        error_task.executor = error_executor
        
        try:
            await self.append_and_flush(error_task)
        except Exception:
            pass
        
        return {
            "output": None,
            "runner": self,
        }
