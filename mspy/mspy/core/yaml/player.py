"""
YAML脚本播放器
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional, Any, Dict, List, Callable, Awaitable, Literal

from mspy.core.yaml.parser import MidsceneYamlScript, MidsceneYamlTask
from mspy.core.yaml.utils import build_detailed_locate_param
from mspy.core.agent.agent import Agent
from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

logger = logging.getLogger("midscene.yaml")
debug = get_debug("yaml-player")


ScriptPlayerStatusValue = Literal["init", "running", "done", "error"]


class ScriptPlayerTaskStatus:
    """任务状态"""
    
    def __init__(
        self,
        name: str,
        index: int,
        flow: Optional[List[Dict[str, Any]]] = None,
        continue_on_error: bool = False,
    ):
        self.name = name
        self.index = index
        self.flow = flow
        self.continue_on_error = continue_on_error
        self.status: ScriptPlayerStatusValue = "init"
        self.current_step: Optional[int] = None
        self.total_steps: int = len(flow) if flow else 0
        self.error: Optional[Exception] = None


class FreeFn:
    """资源释放函数"""
    
    def __init__(self, name: str, fn: Callable[[], Awaitable[None]]):
        self.name = name
        self.fn = fn


class ScriptPlayer:
    """
    YAML脚本播放器
    
    解析并执行YAML格式的自动化脚本。
    """
    
    # AI任务处理器映射
    AI_TASK_HANDLER_MAP = {
        "aiQuery": "ai_query",
        "aiNumber": "ai_number",
        "aiString": "ai_string",
        "aiBoolean": "ai_boolean",
        "aiAsk": "ai_ask",
        "aiLocate": "ai_locate",
    }
    
    def __init__(
        self,
        script: MidsceneYamlScript,
        setup_agent: Callable[[Any], Awaitable[tuple[Agent, List[FreeFn]]]],
        on_task_status_change: Optional[Callable[[ScriptPlayerTaskStatus], None]] = None,
        script_path: Optional[str] = None,
    ):
        """
        初始化播放器
        
        Args:
            script: YAML脚本对象
            setup_agent: Agent设置函数
            on_task_status_change: 任务状态变化回调
            script_path: 脚本路径
        """
        self.script = script
        self.setup_agent = setup_agent
        self.on_task_status_change = on_task_status_change
        self.script_path = script_path
        
        self.current_task_index: Optional[int] = None
        self.status: ScriptPlayerStatusValue = "init"
        self.report_file: Optional[str] = None
        self.result: Dict[str, Any] = {}
        self.output: Optional[str] = None
        self.error_in_setup: Optional[Exception] = None
        self.agent_status_tip: Optional[str] = None
        
        self._unnamed_result_index = 0
        self._interface_agent: Optional[Agent] = None
        self._action_space: List[Any] = []
        
        # 初始化任务状态列表
        self.task_status_list: List[ScriptPlayerTaskStatus] = []
        for i, task in enumerate(script.tasks):
            self.task_status_list.append(ScriptPlayerTaskStatus(
                name=task.name,
                index=i,
                flow=task.flow,
                continue_on_error=task.continue_on_error,
            ))
        
        # 设置输出路径
        target = script.web or script.target
        if target and hasattr(target, "output") and target.output:
            self.output = str(Path.cwd() / target.output)
        elif script_path:
            script_name = Path(script_path).stem.replace(".yaml", "").replace(".yml", "")
            self.output = str(
                Path(get_midscene_run_sub_dir("output")) / 
                f"{script_name}-{int(time.time())}.json"
            )
    
    def _set_result(self, key: Optional[str], value: Any) -> None:
        """设置结果"""
        key_to_use = key or str(self._unnamed_result_index)
        if not key:
            self._unnamed_result_index += 1
        
        if key_to_use in self.result:
            logger.warning(f"Result key {key_to_use} already exists, will overwrite")
        
        self.result[key_to_use] = value
        self._flush_result()
    
    def _flush_result(self) -> None:
        """刷新结果到文件"""
        if self.output:
            output_path = Path(self.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.result, f, indent=2, ensure_ascii=False)
    
    def _set_player_status(
        self,
        status: ScriptPlayerStatusValue,
        error: Optional[Exception] = None,
    ) -> None:
        """设置播放器状态"""
        self.status = status
        self.error_in_setup = error
    
    def _notify_task_status_change(self, task_index: Optional[int] = None) -> None:
        """通知任务状态变化"""
        index = task_index if task_index is not None else self.current_task_index
        if index is not None and self.on_task_status_change:
            self.on_task_status_change(self.task_status_list[index])
    
    def _set_task_status(
        self,
        index: int,
        status: ScriptPlayerStatusValue,
        error: Optional[Exception] = None,
    ) -> None:
        """设置任务状态"""
        self.task_status_list[index].status = status
        if error:
            self.task_status_list[index].error = error
        self._notify_task_status_change(index)
    
    def _set_task_index(self, task_index: int) -> None:
        """设置当前任务索引"""
        self.current_task_index = task_index
    
    async def play_task(
        self,
        task_status: ScriptPlayerTaskStatus,
        agent: Agent,
    ) -> None:
        """
        执行单个任务
        
        Args:
            task_status: 任务状态
            agent: Agent实例
        """
        flow = task_status.flow
        assert_condition(flow, "Missing flow in task")
        
        for flow_item_index, flow_item in enumerate(flow):
            task_status.current_step = flow_item_index
            debug(f"Playing step {flow_item_index}, flowItem={json.dumps(flow_item)}")
            
            # 处理aiAct/aiAction/ai
            if any(key in flow_item for key in ("aiAct", "aiAction", "ai")):
                prompt = flow_item.get("aiAct") or flow_item.get("aiAction") or flow_item.get("ai")
                assert_condition(prompt, "Missing prompt for ai (aiAct)")
                await agent.ai_act(prompt)
            
            # 处理aiAssert
            elif "aiAssert" in flow_item:
                prompt = flow_item["aiAssert"]
                msg = flow_item.get("errorMessage")
                assert_condition(prompt, "Missing prompt for aiAssert")
                
                try:
                    await agent.ai_assert(prompt, msg)
                    self._set_result(flow_item.get("name"), {"pass": True})
                except AssertionError as e:
                    self._set_result(flow_item.get("name"), {
                        "pass": False,
                        "message": str(e),
                    })
                    raise
            
            # 处理简单AI任务
            elif any(key in flow_item for key in self.AI_TASK_HANDLER_MAP):
                for ai_key, agent_method in self.AI_TASK_HANDLER_MAP.items():
                    if ai_key in flow_item:
                        prompt = flow_item[ai_key]
                        name = flow_item.get("name")
                        assert_condition(prompt, f"Missing prompt for {ai_key}")
                        
                        method = getattr(agent, agent_method, None)
                        if method:
                            result = await method(prompt)
                            self._set_result(name, result)
                        break
            
            # 处理aiWaitFor
            elif "aiWaitFor" in flow_item:
                prompt = flow_item["aiWaitFor"]
                timeout = flow_item.get("timeout", 15000)
                assert_condition(prompt, "Missing prompt for aiWaitFor")
                await agent.ai_wait_for(prompt, timeout_ms=timeout)
            
            # 处理sleep
            elif "sleep" in flow_item:
                ms = flow_item["sleep"]
                if isinstance(ms, str):
                    ms = int(ms)
                assert_condition(ms and ms > 0, f"ms for sleep must be greater than 0, got {ms}")
                await asyncio.sleep(ms / 1000)
            
            # 处理aiInput
            elif "aiInput" in flow_item:
                locate = flow_item.get("aiInput") or flow_item.get("locate", "")
                value = flow_item.get("value", "")
                await agent.ai_input(locate, value)
            
            # 处理aiTap
            elif "aiTap" in flow_item:
                prompt = flow_item["aiTap"]
                await agent.ai_tap(prompt)
            
            # 处理其他操作...
            else:
                debug(f"Unknown flow item: {flow_item}")
        
        self.report_file = agent.report_file
    
    async def run(self) -> None:
        """
        运行脚本
        """
        platform = self.script.web or self.script.target
        
        self._set_player_status("running")
        
        agent: Optional[Agent] = None
        free_fn: List[FreeFn] = []
        
        try:
            result = await self.setup_agent(platform)
            agent = result[0]
            free_fn = result[1]
            self._action_space = agent.interface.action_space()
        except Exception as e:
            self._set_player_status("error", e)
            return
        
        self._interface_agent = agent
        
        # 执行任务
        task_index = 0
        error_flag = False
        
        while task_index < len(self.script.tasks):
            task_status = self.task_status_list[task_index]
            self._set_task_status(task_index, "running")
            self._set_task_index(task_index)
            
            try:
                await self.play_task(task_status, self._interface_agent)
                self._set_task_status(task_index, "done")
            except Exception as e:
                self._set_task_status(task_index, "error", e)
                
                if task_status.continue_on_error:
                    pass  # 继续执行
                else:
                    self.report_file = agent.report_file
                    error_flag = True
                    break
            
            self.report_file = agent.report_file
            task_index += 1
        
        if error_flag:
            self._set_player_status("error")
        else:
            self._set_player_status("done")
        
        self.agent_status_tip = ""
        
        # 释放资源
        for fn in free_fn:
            try:
                await fn.fn()
            except Exception:
                pass
