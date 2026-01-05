"""YAML script player/executor."""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Literal

from midscene.shared.logger import get_logger
from midscene.core.yaml.parser import MidsceneYamlScript, MidsceneYamlTask

logger = get_logger("yaml:player")

TaskStatus = Literal["pending", "running", "finished", "error", "skipped"]


class TaskStatusInfo:
    """Status information for a task."""
    
    def __init__(self, name: str):
        self.name = name
        self.status: TaskStatus = "pending"
        self.error: Optional[Exception] = None
        self.result: Any = None


class ScriptPlayer:
    """
    Executes a YAML automation script.
    """
    
    def __init__(
        self,
        script: MidsceneYamlScript,
        agent_factory: Callable[[], Any],
    ):
        """
        Initialize the script player.
        
        Args:
            script: Parsed YAML script
            agent_factory: Async function that returns {"agent": Agent, "free_fn": []}
        """
        self.script = script
        self._agent_factory = agent_factory
        self._status: TaskStatus = "pending"
        self._task_status_list: List[TaskStatusInfo] = []
        self._result: Dict[str, Any] = {}
        self._error_in_setup: Optional[Exception] = None
        self._report_file: Optional[str] = None
        self._output: Optional[str] = None
    
    @property
    def status(self) -> TaskStatus:
        """Get the overall execution status."""
        return self._status
    
    @property
    def task_status_list(self) -> List[TaskStatusInfo]:
        """Get the status list for all tasks."""
        return self._task_status_list
    
    @property
    def result(self) -> Dict[str, Any]:
        """Get the execution result."""
        return self._result
    
    @property
    def error_in_setup(self) -> Optional[Exception]:
        """Get any error that occurred during setup."""
        return self._error_in_setup
    
    @property
    def report_file(self) -> Optional[str]:
        """Get the report file path."""
        return self._report_file
    
    @property
    def output(self) -> Optional[str]:
        """Get or set the output path."""
        return self._output
    
    @output.setter
    def output(self, value: str) -> None:
        self._output = value
    
    async def run(self) -> None:
        """Execute the script."""
        self._status = "running"
        
        # Initialize task status list
        for task in self.script.tasks:
            self._task_status_list.append(TaskStatusInfo(task.name))
        
        # Get agent
        try:
            agent_result = await self._agent_factory()
            if asyncio.iscoroutine(agent_result):
                agent_result = await agent_result
            agent = agent_result.get("agent")
            free_fns = agent_result.get("free_fn", [])
        except Exception as e:
            self._error_in_setup = e
            self._status = "error"
            logger.error("Failed to create agent: %s", str(e))
            return
        
        try:
            # Execute tasks
            for i, task in enumerate(self.script.tasks):
                task_status = self._task_status_list[i]
                task_status.status = "running"
                
                try:
                    result = await self._execute_task(agent, task)
                    task_status.status = "finished"
                    task_status.result = result
                    
                    # Store result if task has output
                    if result:
                        self._result[task.name] = result
                        
                except Exception as e:
                    task_status.status = "error"
                    task_status.error = e
                    logger.error("Task '%s' failed: %s", task.name, str(e))
                    
                    if not task.continue_on_error:
                        # Mark remaining tasks as skipped
                        for j in range(i + 1, len(self._task_status_list)):
                            self._task_status_list[j].status = "skipped"
                        self._status = "error"
                        return
            
            self._status = "finished"
            
        finally:
            # Call cleanup functions
            for free_fn in free_fns:
                try:
                    if asyncio.iscoroutinefunction(free_fn):
                        await free_fn()
                    else:
                        free_fn()
                except Exception as e:
                    logger.error("Cleanup function failed: %s", str(e))
    
    async def _execute_task(
        self,
        agent: Any,
        task: MidsceneYamlTask,
    ) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            agent: The agent to use
            task: The task to execute
            
        Returns:
            Task result
        """
        result = {}
        
        for flow_item in task.flow:
            if not isinstance(flow_item, dict):
                continue
            
            # Handle each flow item type
            if "aiTap" in flow_item:
                await agent.ai_tap(flow_item["aiTap"])
            
            elif "aiHover" in flow_item:
                await agent.ai_hover(flow_item["aiHover"])
            
            elif "aiInput" in flow_item:
                input_config = flow_item["aiInput"]
                if isinstance(input_config, dict):
                    locate = input_config.get("locate", "")
                    value = input_config.get("value", "")
                    await agent.ai_input(locate, {"value": value})
                else:
                    # Legacy format: [locate, value]
                    await agent.ai_input(input_config[0], {"value": input_config[1]})
            
            elif "aiKeyboardPress" in flow_item:
                key_config = flow_item["aiKeyboardPress"]
                if isinstance(key_config, dict):
                    await agent.ai_keyboard_press(
                        key_config.get("locate"),
                        {"key_name": key_config.get("key")}
                    )
                else:
                    await agent.ai_keyboard_press(None, {"key_name": key_config})
            
            elif "aiScroll" in flow_item:
                scroll_config = flow_item["aiScroll"]
                await agent.ai_scroll(
                    scroll_config.get("locate"),
                    {
                        "direction": scroll_config.get("direction", "down"),
                        "distance": scroll_config.get("distance", 300),
                    }
                )
            
            elif "aiAssert" in flow_item:
                await agent.ai_assert(flow_item["aiAssert"])
            
            elif "aiWaitFor" in flow_item:
                wait_config = flow_item["aiWaitFor"]
                if isinstance(wait_config, dict):
                    await agent.ai_wait_for(
                        wait_config.get("assertion", ""),
                        wait_config.get("options"),
                    )
                else:
                    await agent.ai_wait_for(wait_config)
            
            elif "aiQuery" in flow_item:
                query_result = await agent.ai_query(flow_item["aiQuery"])
                result.update(query_result if isinstance(query_result, dict) else {"query": query_result})
            
            elif "aiAct" in flow_item or "aiAction" in flow_item:
                action_prompt = flow_item.get("aiAct") or flow_item.get("aiAction")
                await agent.ai_act(action_prompt)
            
            elif "sleep" in flow_item:
                sleep_ms = flow_item["sleep"]
                await asyncio.sleep(sleep_ms / 1000)
        
        return result
