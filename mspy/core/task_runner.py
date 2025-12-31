"""
任务运行器模块
"""

import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

from ..shared import (
    get_debug,
    UIContext,
    ExecutionTask,
    ExecutionTaskStatus,
    ExecutionDump,
    ExecutionRecorderItem,
    assert_condition,
)

debug = get_debug('task-runner')

# UI上下文缓存TTL (毫秒)
UI_CONTEXT_CACHE_TTL_MS = 300


class TaskExecutionError(Exception):
    """任务执行错误"""
    
    def __init__(
        self,
        message: str,
        runner: 'TaskRunner',
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
        on_task_update: Optional[Callable[['TaskRunner', Optional[TaskExecutionError]], None]] = None,
        tasks: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        初始化任务运行器
        
        Args:
            name: 运行器名称
            ui_context_builder: UI上下文构建函数
            on_task_start: 任务开始回调
            on_task_update: 任务更新回调
            tasks: 初始任务列表
        """
        self.name = name
        self._ui_context_builder = ui_context_builder
        self.on_task_start = on_task_start
        self.on_task_update = on_task_update
        self.tasks: List[ExecutionTask] = []
        self.status = 'init'
        
        self._last_ui_context: Optional[Dict[str, Any]] = None
        
        if tasks:
            for task_def in tasks:
                self.tasks.append(self._mark_task_as_pending(task_def))
            self.status = 'pending'
    
    def _mark_task_as_pending(self, task_def: Dict[str, Any]) -> ExecutionTask:
        """将任务定义标记为待处理状态"""
        return ExecutionTask(
            type=task_def.get('type', ''),
            sub_type=task_def.get('sub_type'),
            param=task_def.get('param'),
            thought=task_def.get('thought'),
            status=ExecutionTaskStatus.PENDING,
            sub_task=task_def.get('sub_task', False),
        )
    
    async def _get_ui_context(self, force_refresh: bool = False) -> Optional[UIContext]:
        """获取UI上下文"""
        now = int(time.time() * 1000)
        
        # 检查是否可以复用缓存
        should_reuse = (
            not force_refresh and 
            self._last_ui_context and
            now - self._last_ui_context['captured_at'] <= UI_CONTEXT_CACHE_TTL_MS
        )
        
        if should_reuse and self._last_ui_context:
            debug(f"reuse cached uiContext captured {now - self._last_ui_context['captured_at']}ms ago")
            return self._last_ui_context['context']
        
        try:
            context = self._ui_context_builder()
            if hasattr(context, '__await__'):
                context = await context
            
            if context:
                self._last_ui_context = {
                    'context': context,
                    'captured_at': int(time.time() * 1000),
                }
            else:
                self._last_ui_context = None
            
            return context
        except Exception as e:
            self._last_ui_context = None
            raise
    
    async def _capture_screenshot(self) -> Optional[str]:
        """捕获截图"""
        try:
            ui_context = await self._get_ui_context(force_refresh=True)
            return ui_context.screenshot_base64 if ui_context else None
        except Exception as e:
            debug(f"error while capturing screenshot: {e}")
            return None
    
    def _attach_recorder_item(
        self,
        task: ExecutionTask,
        screenshot: Optional[str],
        phase: str = 'after-calling'
    ) -> None:
        """附加记录项"""
        if not screenshot:
            return
        
        recorder_item = ExecutionRecorderItem(
            type='screenshot',
            ts=int(time.time() * 1000),
            screenshot=screenshot,
            timing=phase,
        )
        
        task.recorder.append(recorder_item)
    
    async def _emit_on_task_update(self, error: Optional[TaskExecutionError] = None) -> None:
        """触发任务更新事件"""
        if self.on_task_update:
            result = self.on_task_update(self, error)
            if hasattr(result, '__await__'):
                await result
    
    def _find_previous_non_sub_task_ui_context(self, current_index: int) -> Optional[UIContext]:
        """查找前一个非子任务的UI上下文"""
        for i in range(current_index - 1, -1, -1):
            candidate = self.tasks[i]
            if not candidate.sub_task and candidate.ui_context:
                return candidate.ui_context
        return None
    
    async def append(
        self,
        task: Union[Dict[str, Any], List[Dict[str, Any]]],
        allow_when_error: bool = False
    ) -> None:
        """
        添加任务
        
        Args:
            task: 任务定义或任务定义列表
            allow_when_error: 是否允许在错误状态下添加
        """
        self._normalize_status_from_error(allow_when_error)
        
        if isinstance(task, list):
            for t in task:
                self.tasks.append(self._mark_task_as_pending(t))
        else:
            self.tasks.append(self._mark_task_as_pending(task))
        
        if self.status != 'running':
            self.status = 'pending'
        
        await self._emit_on_task_update()
    
    def _normalize_status_from_error(
        self,
        allow_when_error: bool = False,
        error_message: Optional[str] = None
    ) -> None:
        """从错误状态恢复"""
        if self.status != 'error':
            return
        
        if not allow_when_error:
            error_task = self.latest_error_task()
            msg = error_message or (
                f"task runner is in error state, cannot proceed\n"
                f"error={error_task.error if error_task else 'unknown'}\n"
                f"{error_task.error_stack if error_task else ''}"
            )
            raise RuntimeError(msg)
        
        self.status = 'pending' if self.tasks else 'init'
    
    async def append_and_flush(
        self,
        task: Union[Dict[str, Any], List[Dict[str, Any]]],
        allow_when_error: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        添加任务并执行
        
        Args:
            task: 任务定义或任务定义列表
            allow_when_error: 是否允许在错误状态下执行
        
        Returns:
            {'output': Any, 'thought': str} 或 None
        """
        await self.append(task, allow_when_error)
        return await self.flush(allow_when_error)
    
    async def flush(self, allow_when_error: bool = False) -> Optional[Dict[str, Any]]:
        """
        执行所有待处理的任务
        
        Args:
            allow_when_error: 是否允许在错误状态下执行
        
        Returns:
            {'output': Any, 'thought': str} 或 None
        """
        if self.status == 'init' and self.tasks:
            debug("illegal state for task runner, status is init but tasks are not empty")
        
        self._normalize_status_from_error(allow_when_error)
        assert_condition(self.status != 'running', "task runner is already running")
        assert_condition(self.status != 'completed', "task runner is already completed")
        
        # 查找下一个待处理任务
        next_pending_index = -1
        for i, task in enumerate(self.tasks):
            if task.status == ExecutionTaskStatus.PENDING:
                next_pending_index = i
                break
        
        if next_pending_index < 0:
            return None
        
        self.status = 'running'
        await self._emit_on_task_update()
        
        task_index = next_pending_index
        successfully_completed = True
        previous_find_output = None
        
        while task_index < len(self.tasks):
            task = self.tasks[task_index]
            assert_condition(
                task.status == ExecutionTaskStatus.PENDING,
                f"task status should be pending, but got: {task.status}"
            )
            
            task.timing = {'start': int(time.time() * 1000)}
            
            try:
                task.status = ExecutionTaskStatus.RUNNING
                await self._emit_on_task_update()
                
                if self.on_task_start:
                    result = self.on_task_start(task)
                    if hasattr(result, '__await__'):
                        await result
                
                # 获取UI上下文
                if task.sub_task:
                    ui_context = self._find_previous_non_sub_task_ui_context(task_index)
                    assert_condition(
                        ui_context,
                        "subTask requires uiContext from previous non-subTask task"
                    )
                else:
                    ui_context = await self._get_ui_context()
                
                task.ui_context = ui_context
                
                # 执行任务（这里需要由外部提供executor）
                # 简化版本：直接标记为完成
                
                is_last_task = task_index == len(self.tasks) - 1
                
                if is_last_task:
                    screenshot = await self._capture_screenshot()
                    self._attach_recorder_item(task, screenshot, 'after-calling')
                
                task.status = ExecutionTaskStatus.FINISHED
                task.timing['end'] = int(time.time() * 1000)
                task.timing['cost'] = task.timing['end'] - task.timing['start']
                
                await self._emit_on_task_update()
                task_index += 1
                
            except Exception as e:
                successfully_completed = False
                task.error = e
                task.error_message = str(e)
                task.error_stack = traceback.format_exc()
                task.status = ExecutionTaskStatus.FAILED
                task.timing['end'] = int(time.time() * 1000)
                task.timing['cost'] = task.timing['end'] - task.timing['start']
                
                await self._emit_on_task_update()
                break
        
        # 将剩余任务标记为取消
        for i in range(task_index + 1, len(self.tasks)):
            self.tasks[i].status = ExecutionTaskStatus.CANCELLED
        
        if task_index + 1 < len(self.tasks):
            await self._emit_on_task_update()
        
        finalize_error = None
        if not successfully_completed:
            self.status = 'error'
            error_task = self.latest_error_task()
            message = (
                error_task.error_message if error_task else "Task execution failed"
            )
            if error_task and error_task.error_stack:
                message = f"{message}\n{error_task.error_stack}"
            
            finalize_error = TaskExecutionError(
                message,
                self,
                error_task,
                error_task.error if error_task else None
            )
            await self._emit_on_task_update(finalize_error)
        else:
            self.status = 'completed'
            await self._emit_on_task_update()
        
        if finalize_error:
            raise finalize_error
        
        if self.tasks:
            output_index = min(task_index, len(self.tasks) - 1)
            task = self.tasks[output_index]
            return {
                'thought': task.thought,
                'output': task.output,
            }
        
        return None
    
    def is_in_error_state(self) -> bool:
        """检查是否处于错误状态"""
        return self.status == 'error'
    
    def latest_error_task(self) -> Optional[ExecutionTask]:
        """获取最近的错误任务"""
        if self.status != 'error':
            return None
        
        for task in self.tasks:
            if task.status == ExecutionTaskStatus.FAILED:
                return task
        
        return None
    
    def dump(self) -> ExecutionDump:
        """导出执行数据"""
        return ExecutionDump(
            log_time=int(time.time() * 1000),
            name=self.name,
            tasks=self.tasks,
        )
    
    async def append_error_plan(self, error_msg: str) -> Dict[str, Any]:
        """
        添加错误计划
        
        Args:
            error_msg: 错误消息
        
        Returns:
            {'output': None, 'runner': TaskRunner}
        """
        error_task = {
            'type': 'Action Space',
            'sub_type': 'Error',
            'param': {'thought': error_msg},
            'thought': error_msg,
        }
        
        try:
            await self.append_and_flush(error_task)
        except:
            pass
        
        return {
            'output': None,
            'runner': self,
        }
