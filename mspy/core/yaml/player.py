"""
YAML脚本执行器

对应TypeScript源码: packages/core/src/yaml/player.ts
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from enum import Enum

from mspy.shared.logger import get_debug
from mspy.shared.utils import async_sleep_ms
from mspy.core.yaml.parser import MidsceneYamlScript, MidsceneYamlTask, MidsceneYamlFlowItem

debug = get_debug('yaml:player')

T = TypeVar('T')


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TaskStatusItem:
    """任务状态项"""
    name: str
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[Exception] = None
    duration: int = 0


class ScriptPlayer(Generic[T]):
    """脚本执行器
    
    负责解析和执行YAML脚本
    """
    
    def __init__(
        self,
        script: MidsceneYamlScript,
        agent_provider: Callable[[], Any],  # 返回包含agent的字典
    ):
        """初始化脚本执行器
        
        Args:
            script: 解析后的YAML脚本
            agent_provider: Agent提供函数
        """
        self._script = script
        self._agent_provider = agent_provider
        
        # 执行状态
        self._status: str = "pending"
        self._task_status_list: List[TaskStatusItem] = []
        self._result: Dict[str, Any] = {}
        self._error_in_setup: Optional[Exception] = None
        
        # 输出配置
        self._output: Optional[str] = None
        self._report_file: Optional[str] = None
        
        # 初始化任务状态列表
        for task in script.tasks:
            self._task_status_list.append(TaskStatusItem(name=task.name))
    
    @property
    def status(self) -> str:
        """获取执行状态"""
        return self._status
    
    @property
    def task_status_list(self) -> List[TaskStatusItem]:
        """获取任务状态列表"""
        return self._task_status_list
    
    @property
    def result(self) -> Dict[str, Any]:
        """获取执行结果"""
        return self._result
    
    @property
    def error_in_setup(self) -> Optional[Exception]:
        """获取设置阶段的错误"""
        return self._error_in_setup
    
    @property
    def output(self) -> Optional[str]:
        """获取输出路径"""
        return self._output
    
    @output.setter
    def output(self, value: str):
        """设置输出路径"""
        self._output = value
    
    @property
    def report_file(self) -> Optional[str]:
        """获取报告文件路径"""
        return self._report_file
    
    async def run(self) -> None:
        """执行脚本"""
        self._status = "running"
        
        try:
            # 获取Agent
            agent_result = self._agent_provider()
            if hasattr(agent_result, '__await__'):
                agent_result = await agent_result
            
            agent = agent_result.get('agent')
            free_fn_list = agent_result.get('freeFn', [])
            
            if not agent:
                raise ValueError("无法获取Agent实例")
            
            # 执行每个任务
            for i, task in enumerate(self._script.tasks):
                status_item = self._task_status_list[i]
                status_item.status = TaskStatus.RUNNING
                
                start_time = time.time()
                
                try:
                    await self._run_task(task, agent)
                    status_item.status = TaskStatus.FINISHED
                except Exception as e:
                    status_item.status = TaskStatus.ERROR
                    status_item.error = e
                    
                    if not task.continue_on_error:
                        self._status = "error"
                        raise
                
                status_item.duration = int((time.time() - start_time) * 1000)
            
            self._status = "finished"
            
            # 保存报告
            if hasattr(agent, 'report_file'):
                self._report_file = agent.report_file
            
            # 清理资源
            for fn in free_fn_list:
                try:
                    if callable(fn):
                        result = fn()
                        if hasattr(result, '__await__'):
                            await result
                except Exception as e:
                    debug('清理资源时发生错误:', str(e))
                    
        except Exception as e:
            self._status = "error"
            self._error_in_setup = e
            raise
    
    async def _run_task(self, task: MidsceneYamlTask, agent: Any) -> None:
        """执行单个任务
        
        Args:
            task: 任务定义
            agent: Agent实例
        """
        debug(f"执行任务: {task.name}")
        
        for item in task.flow:
            await self._run_flow_item(item, agent)
    
    async def _run_flow_item(self, item: MidsceneYamlFlowItem, agent: Any) -> None:
        """执行流程项
        
        Args:
            item: 流程项
            agent: Agent实例
        """
        # 处理sleep
        if item.sleep:
            debug(f"休眠 {item.sleep}ms")
            await async_sleep_ms(item.sleep)
            return
        
        # 处理log
        if item.log:
            debug(f"日志: {item.log}")
            print(f"[Log] {item.log}")
            return
        
        # 处理AI动作
        if item.ai_act:
            await agent.ai_act(item.ai_act)
        elif item.ai_tap:
            await agent.ai_tap(item.ai_tap)
        elif item.ai_hover:
            await agent.ai_hover(item.ai_hover)
        elif item.ai_input:
            # ai_input可以是字典 {locate: ..., value: ...}
            if isinstance(item.ai_input, dict):
                locate = item.ai_input.get('locate', '')
                value = item.ai_input.get('value', '')
                await agent.ai_input(locate, value)
            else:
                debug(f"无效的aiInput格式: {item.ai_input}")
        elif item.ai_keyboard_press:
            await agent.ai_keyboard_press(item.ai_keyboard_press)
        elif item.ai_scroll:
            if isinstance(item.ai_scroll, dict):
                direction = item.ai_scroll.get('direction', 'down')
                locate = item.ai_scroll.get('locate')
                await agent.ai_scroll(direction, locate)
            else:
                await agent.ai_scroll()
        elif item.ai_assert:
            await agent.ai_assert(item.ai_assert)
        elif item.ai_wait_for:
            await agent.ai_wait_for(item.ai_wait_for)
        elif item.ai_query:
            result = await agent.ai_query(item.ai_query)
            # 将结果存储到self._result
            if isinstance(item.ai_query, str):
                self._result[item.ai_query] = result
            elif isinstance(item.ai_query, dict):
                self._result.update(result if isinstance(result, dict) else {})
