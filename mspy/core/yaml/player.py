# -*- coding: utf-8 -*-
"""
YAML 脚本播放器
提供 YAML 脚本的执行功能。
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from mspy.shared.types import (
    MidsceneYamlScript,
    MidsceneYamlTask,
    MidsceneYamlFlowItem,
)
from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

from mspy.core.agent import Agent
from .utils import build_detailed_locate_param, build_detailed_locate_param_and_rest_params


debug = get_debug("yaml-player")


class ScriptPlayer:
    """
    YAML 脚本播放器
    用于解析和执行 YAML 格式的自动化脚本
    """
    
    def __init__(
        self,
        script: MidsceneYamlScript,
        setup_agent: Callable,
        on_task_status_change: Optional[Callable] = None,
        script_path: Optional[str] = None,
    ):
        """
        初始化脚本播放器
        
        Args:
            script: YAML 脚本对象
            setup_agent: 设置 Agent 的函数
            on_task_status_change: 任务状态变化回调
            script_path: 脚本文件路径
        """
        self.script = script
        self.setup_agent = setup_agent
        self.on_task_status_change = on_task_status_change
        self.script_path = script_path
        
        self.current_task_index: Optional[int] = None
        self.task_status_list: List[Dict[str, Any]] = []
        self.status = "init"  # 'init' | 'running' | 'done' | 'error'
        self.report_file: Optional[str] = None
        self.result: Dict[str, Any] = {}
        self._unnamed_result_index = 0
        self.output: Optional[str] = None
        self.unstable_log_content: Optional[str] = None
        self.error_in_setup: Optional[Exception] = None
        self._interface_agent: Optional[Agent] = None
        self.agent_status_tip: Optional[str] = None
        self.target: Optional[Dict[str, Any]] = None
        self._action_space: List[Any] = []
        
        # 解析目标配置
        self.target = (
            script.target or
            script.web or
            script.android or
            script.ios
        )
        
        # 设置输出路径
        if self.target and self.target.get('output'):
            self.output = str(Path.cwd() / self.target['output'])
            debug(f"setting output by config.output: {self.output}")
        else:
            script_name = "script"
            if script_path:
                script_name = Path(script_path).stem
            timestamp = int(datetime.now().timestamp() * 1000)
            self.output = str(
                Path(get_midscene_run_sub_dir("output")) / f"{script_name}-{timestamp}.json"
            )
            debug(f"setting output by script path: {self.output}")
        
        # 初始化任务状态列表
        self.task_status_list = []
        for i, task in enumerate(script.tasks):
            self.task_status_list.append({
                'name': task.name,
                'index': i,
                'status': 'init',
                'flow': task.flow,
                'total_steps': len(task.flow),
                'current_step': 0,
                'continue_on_error': task.continue_on_error,
            })
    
    def _set_result(self, key: Optional[str], value: Any) -> None:
        """设置结果"""
        key_to_use = key if key else str(self._unnamed_result_index)
        if not key:
            self._unnamed_result_index += 1
        
        if key_to_use in self.result:
            print(f"Warning: result key {key_to_use} already exists, will overwrite")
        
        self.result[key_to_use] = value
        self._flush_result()
    
    def _set_player_status(self, status: str, error: Optional[Exception] = None) -> None:
        """设置播放器状态"""
        self.status = status
        self.error_in_setup = error
    
    def _notify_task_status_change(self, task_index: Optional[int] = None) -> None:
        """通知任务状态变化"""
        idx = task_index if task_index is not None else self.current_task_index
        
        if idx is None:
            return
        
        task_status = self.task_status_list[idx]
        if self.on_task_status_change:
            self.on_task_status_change(task_status)
    
    def _set_task_status(
        self,
        index: int,
        status: str,
        error: Optional[Exception] = None
    ) -> None:
        """设置任务状态"""
        self.task_status_list[index]['status'] = status
        if error:
            self.task_status_list[index]['error'] = error
        
        self._notify_task_status_change(index)
    
    def _set_task_index(self, task_index: int) -> None:
        """设置当前任务索引"""
        self.current_task_index = task_index
    
    def _flush_result(self) -> None:
        """将结果写入文件"""
        if self.output:
            output_path = Path(self.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.result, f, indent=2, ensure_ascii=False)
    
    async def _play_task(self, task_status: Dict[str, Any], agent: Agent) -> None:
        """
        播放单个任务
        
        Args:
            task_status: 任务状态
            agent: Agent 实例
        """
        flow = task_status.get('flow', [])
        assert_condition(flow, "missing flow in task")
        
        for step_index, flow_item in enumerate(flow):
            task_status['current_step'] = step_index
            item_data = flow_item.data if hasattr(flow_item, 'data') else flow_item
            
            debug(f"playing step {step_index}, flowItem={json.dumps(item_data, ensure_ascii=False)}")
            
            # 处理 ai/aiAct/aiAction
            if any(key in item_data for key in ['ai', 'aiAct', 'aiAction']):
                prompt = item_data.get('ai') or item_data.get('aiAct') or item_data.get('aiAction')
                assert_condition(prompt, "missing prompt for ai (aiAct)")
                await agent.ai_act(prompt)
            
            # 处理 aiAssert
            elif 'aiAssert' in item_data:
                prompt = item_data['aiAssert']
                msg = item_data.get('errorMessage')
                assert_condition(prompt, "missing prompt for aiAssert")
                
                result = await agent.ai_assert(prompt, msg, keep_raw_response=True)
                self._set_result(item_data.get('name'), result)
                
                if result and not result.get('pass'):
                    raise AssertionError(result.get('message', 'Assertion failed'))
            
            # 处理 aiQuery
            elif 'aiQuery' in item_data:
                prompt = item_data['aiQuery']
                assert_condition(prompt, "missing prompt for aiQuery")
                result = await agent.ai_query(prompt)
                self._set_result(item_data.get('name'), result)
            
            # 处理 aiWaitFor
            elif 'aiWaitFor' in item_data:
                prompt = item_data['aiWaitFor']
                timeout = item_data.get('timeout', 15000)
                assert_condition(prompt, "missing prompt for aiWaitFor")
                await agent.ai_wait_for(prompt, timeout_ms=timeout)
            
            # 处理 sleep
            elif 'sleep' in item_data:
                ms = item_data['sleep']
                if isinstance(ms, str):
                    ms = int(ms)
                assert_condition(ms and ms > 0, f"ms for sleep must be greater than 0, but got {ms}")
                await asyncio.sleep(ms / 1000)
            
            # 处理 javascript
            elif 'javascript' in item_data:
                result = await agent.evaluate_javascript(item_data['javascript'])
                self._set_result(item_data.get('name'), result)
            
            # 处理 aiInput
            elif 'aiInput' in item_data:
                ai_input = item_data.get('aiInput')
                value = item_data.get('value')
                
                locate_prompt = item_data.get('locate') or ai_input
                if item_data.get('locate'):
                    value = ai_input or value
                
                if locate_prompt:
                    detailed = build_detailed_locate_param(locate_prompt, item_data)
                    await agent._call_action_in_action_space('Input', {
                        **item_data,
                        'value': str(value) if value is not None else '',
                        'locate': detailed,
                    })
            
            # 处理 aiKeyboardPress
            elif 'aiKeyboardPress' in item_data:
                ai_press = item_data.get('aiKeyboardPress')
                key_name = item_data.get('keyName', item_data.get('key_name'))
                
                locate_prompt = item_data.get('locate') or ai_press
                if item_data.get('locate'):
                    key_name = ai_press or key_name
                elif key_name:
                    locate_prompt = ai_press
                else:
                    key_name = ai_press
                
                detailed = build_detailed_locate_param(locate_prompt or '', item_data) if locate_prompt else None
                await agent._call_action_in_action_space('KeyboardPress', {
                    **item_data,
                    'key_name': key_name,
                    'locate': detailed,
                })
            
            # 处理 aiScroll
            elif 'aiScroll' in item_data:
                ai_scroll = item_data.get('aiScroll')
                locate_prompt = item_data.get('locate') or ai_scroll
                
                await agent.ai_scroll(locate_prompt, item_data)
            
            # 处理 aiTap
            elif 'aiTap' in item_data:
                prompt = item_data['aiTap']
                await agent.ai_tap(prompt, item_data)
            
            # 处理 aiHover
            elif 'aiHover' in item_data:
                prompt = item_data['aiHover']
                await agent.ai_hover(prompt, item_data)
            
            else:
                debug(f"unknown flowItem: {item_data}")
        
        self.report_file = agent.report_file
    
    async def run(self) -> None:
        """运行脚本"""
        tasks = self.script.tasks
        
        self._set_player_status("running")
        
        agent: Optional[Agent] = None
        free_fn: List[Dict[str, Any]] = []
        
        try:
            result = await self.setup_agent(self.target)
            agent = result['agent']
            free_fn = result.get('free_fn', [])
            self._action_space = await agent._get_action_space()
        except Exception as e:
            self._set_player_status("error", e)
            return
        
        self._interface_agent = agent
        
        task_index = 0
        self._set_player_status("running")
        error_flag = False
        
        while task_index < len(tasks):
            task_status = self.task_status_list[task_index]
            self._set_task_status(task_index, "running")
            self._set_task_index(task_index)
            
            try:
                await self._play_task(task_status, self._interface_agent)
                self._set_task_status(task_index, "done")
            except Exception as e:
                self._set_task_status(task_index, "error", e)
                
                if task_status.get('continue_on_error'):
                    pass  # 继续下一个任务
                else:
                    self.report_file = agent.report_file if agent else None
                    error_flag = True
                    break
            
            self.report_file = agent.report_file if agent else None
            task_index += 1
        
        if error_flag:
            self._set_player_status("error")
        else:
            self._set_player_status("done")
        
        self.agent_status_tip = ""
        
        # 清理资源
        for fn in free_fn:
            try:
                if 'fn' in fn:
                    await fn['fn']() if asyncio.iscoroutinefunction(fn['fn']) else fn['fn']()
            except Exception:
                pass
