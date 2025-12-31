"""
YAML脚本播放器

从 packages/core/src/yaml/player.ts 迁移
"""

import asyncio
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TYPE_CHECKING

from mspy.core.yaml.parser import MidsceneYamlScript, YamlFlowItem, YamlTask
from mspy.shared.logger import get_debug

if TYPE_CHECKING:
    from mspy.core.agent import Agent


_debug = get_debug("yaml:player")


@dataclass
class TaskStatus:
    """任务状态"""
    name: str
    status: str = "pending"  # pending, running, success, error
    error: Optional[Exception] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None


class ScriptPlayer:
    """
    YAML脚本播放器
    
    执行YAML脚本中定义的任务流程
    """
    
    def __init__(
        self,
        script: MidsceneYamlScript,
        agent_factory: Callable[[], Any],
    ):
        self.script = script
        self._agent_factory = agent_factory
        self.status = "pending"  # pending, running, success, error
        self.task_status_list: list[TaskStatus] = []
        self.result: dict[str, Any] = {}
        self._agent: Optional["Agent"] = None
    
    async def run(self) -> None:
        """执行脚本"""
        self.status = "running"
        
        # 获取Agent
        agent_result = self._agent_factory()
        if hasattr(agent_result, '__await__'):
            agent_result = await agent_result
        
        self._agent = agent_result.get("agent")
        free_fn_list = agent_result.get("freeFn", [])
        
        try:
            # 初始化任务状态
            for task in self.script.tasks:
                self.task_status_list.append(TaskStatus(name=task.name))
            
            # 执行每个任务
            for i, task in enumerate(self.script.tasks):
                task_status = self.task_status_list[i]
                task_status.status = "running"
                task_status.start_time = int(time.time() * 1000)
                
                try:
                    await self._execute_task(task)
                    task_status.status = "success"
                except Exception as e:
                    task_status.status = "error"
                    task_status.error = e
                    self.status = "error"
                    _debug(f"Task '{task.name}' failed: {e}")
                    break
                finally:
                    task_status.end_time = int(time.time() * 1000)
            
            if self.status != "error":
                self.status = "success"
                
        finally:
            # 执行清理函数
            for fn in free_fn_list:
                try:
                    result = fn()
                    if hasattr(result, '__await__'):
                        await result
                except Exception as e:
                    _debug(f"Error in cleanup function: {e}")
    
    async def _execute_task(self, task: YamlTask) -> None:
        """执行单个任务"""
        _debug(f"Executing task: {task.name}")
        
        for item in task.flow:
            await self._execute_flow_item(item, task.name)
    
    async def _execute_flow_item(
        self,
        item: YamlFlowItem,
        task_name: str
    ) -> None:
        """执行流程项"""
        if not self._agent:
            raise RuntimeError("Agent not initialized")
        
        # Sleep
        if item.sleep:
            _debug(f"Sleeping for {item.sleep}ms")
            await asyncio.sleep(item.sleep / 1000)
            return
        
        # AI Act
        if item.ai_act:
            _debug(f"AI Act: {item.ai_act}")
            result = await self._agent.ai_act(item.ai_act)
            self.result[f"{task_name}:aiAct"] = result
            return
        
        # AI Assert
        if item.ai_assert:
            _debug(f"AI Assert: {item.ai_assert}")
            await self._agent.ai_assert(item.ai_assert)
            return
        
        # AI Query
        if item.ai_query:
            query = item.ai_query
            demand = query.get("demand") or query.get("prompt") or str(query)
            _debug(f"AI Query: {demand}")
            result = await self._agent.ai_query(demand)
            
            # 存储结果
            result_name = query.get("name", f"{task_name}:aiQuery")
            self.result[result_name] = result
            return
        
        # AI Wait For
        if item.ai_wait_for:
            _debug(f"AI Wait For: {item.ai_wait_for}")
            await self._agent.ai_wait_for(item.ai_wait_for)
            return
        
        # AI Tap
        if item.ai_tap:
            _debug(f"AI Tap: {item.ai_tap}")
            # TODO: 实现ai_tap
            return
        
        # AI Hover
        if item.ai_hover:
            _debug(f"AI Hover: {item.ai_hover}")
            # TODO: 实现ai_hover
            return
        
        # AI Input
        if item.ai_input:
            input_config = item.ai_input
            locate = input_config.get("locate") or input_config.get("prompt")
            value = input_config.get("value", "")
            _debug(f"AI Input: {locate} = {value}")
            # TODO: 实现ai_input
            return
        
        # AI Keyboard Press
        if item.ai_keyboard_press:
            press_config = item.ai_keyboard_press
            key = press_config.get("key") or press_config.get("keyName")
            _debug(f"AI Keyboard Press: {key}")
            # TODO: 实现ai_keyboard_press
            return
        
        # AI Scroll
        if item.ai_scroll:
            scroll_config = item.ai_scroll
            _debug(f"AI Scroll: {scroll_config}")
            # TODO: 实现ai_scroll
            return
