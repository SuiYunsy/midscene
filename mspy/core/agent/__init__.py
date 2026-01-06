# -*- coding: utf-8 -*-
"""
Agent 模块
提供 AI Agent 功能，用于自动化 UI 操作。
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from mspy.shared.types import (
    Rect,
    Size,
    LocateResultElement,
    AIUsageInfo,
    ExecutionDump,
    GroupedActionDump,
    PlanningAction,
    DetailedLocateParam,
)
from mspy.shared.env import (
    IModelConfig,
    ModelConfigManager,
    global_model_config_manager,
    global_config_manager,
)
from mspy.shared.env.constants import MIDSCENE_REPLANNING_CYCLE_LIMIT
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

from ..types import (
    UIContext,
    ServiceDump,
    ExecutionTask,
    DeviceAction,
    AgentOpt,
    ScrollParam,
)
from ..service import Service
from ..ai_model import call_ai_with_object_response, AIActionType
from ..ai_model.prompt import system_prompt_to_task_planning
from ..common import sleep

debug = get_debug("agent")

# 默认重规划循环限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20
DEFAULT_VLM_UI_TARS_REPLANNING_CYCLE_LIMIT = 40


def build_detailed_locate_param(
    prompt: Union[str, Dict[str, Any]],
    opt: Optional[Dict[str, Any]] = None
) -> DetailedLocateParam:
    """
    构建详细定位参数
    
    Args:
        prompt: 定位提示
        opt: 额外选项
        
    Returns:
        详细定位参数
    """
    if isinstance(prompt, str):
        text_prompt = prompt
    else:
        text_prompt = prompt.get("prompt", "")
    
    deep_think = (opt or {}).get("deep_think", False)
    cacheable = (opt or {}).get("cacheable", True)
    
    return DetailedLocateParam(
        prompt=text_prompt,
        deep_think=deep_think,
        cacheable=cacheable,
    )


class Agent:
    """
    AI Agent 类
    用于自动化 UI 操作，支持元素定位、数据提取、断言等功能
    """
    
    def __init__(
        self,
        interface_instance: Any,
        opts: Optional[AgentOpt] = None
    ):
        """
        初始化 Agent
        
        Args:
            interface_instance: 设备接口实例（如 PlaywrightPage）
            opts: Agent 配置选项
        """
        self.interface = interface_instance
        
        # 默认选项
        default_opts = AgentOpt(
            generate_report=True,
            auto_print_report_msg=True,
            group_name="Midscene Report",
            group_description="",
        )
        
        self.opts = opts or default_opts
        
        # 合并选项
        if opts:
            for key, value in opts.__dict__.items():
                if value is not None:
                    setattr(self.opts, key, value)
        
        # 获取环境变量中的重规划循环限制
        env_limit_str = global_config_manager.get_all_env_config().get(
            MIDSCENE_REPLANNING_CYCLE_LIMIT
        )
        if env_limit_str and self.opts.replanning_cycle_limit is None:
            try:
                self.opts.replanning_cycle_limit = int(env_limit_str)
            except ValueError:
                pass
        
        # 创建模型配置管理器
        if self.opts.model_config:
            self.model_config_manager = ModelConfigManager(self.opts.model_config)
        else:
            self.model_config_manager = global_model_config_manager
        
        # 初始化服务
        self.service = Service(self._get_ui_context)
        
        # 初始化状态
        self.dump = self._reset_dump()
        self.report_file: Optional[str] = None
        self.destroyed = False
        
        # 监听器
        self._dump_update_listeners: List[Callable] = []
        
        # 冻结的 UI 上下文
        self._frozen_ui_context: Optional[UIContext] = None
        
        # 截图缩放比例
        self._screenshot_scale: Optional[float] = None
        
        # VL 模型警告标志
        self._has_warned_non_vl_model = False
        
        debug(f"Agent initialized with interface type: {interface_instance.interface_type}")
    
    async def _get_ui_context(self) -> UIContext:
        """获取 UI 上下文"""
        # 检查 VL 模型配置
        self._ensure_vl_model_warning()
        
        # 如果上下文被冻结，返回冻结的上下文
        if self._frozen_ui_context:
            debug("Using frozen page context")
            return self._frozen_ui_context
        
        # 获取上下文
        if hasattr(self.interface, "get_context"):
            context = await self.interface.get_context()
        else:
            context = await self._common_context_parser()
        
        return context
    
    async def _common_context_parser(self) -> UIContext:
        """通用上下文解析器"""
        # 这是一个简化的实现
        screenshot = await self.interface.screenshot_base64()
        size = await self.interface.size()
        
        class SimpleUIContext(UIContext):
            def __init__(self, screenshot: str, page_size: Size):
                self._screenshot = screenshot
                self._size = page_size
            
            @property
            def screenshot_base64(self) -> str:
                return self._screenshot
            
            @property
            def size(self) -> Size:
                return self._size
        
        return SimpleUIContext(screenshot, size)
    
    def _ensure_vl_model_warning(self) -> None:
        """确保 VL 模型警告只显示一次"""
        if not self._has_warned_non_vl_model:
            interface_type = getattr(self.interface, "interface_type", None)
            if interface_type not in ("puppeteer", "playwright", "static"):
                self.model_config_manager.throw_error_if_non_vl_model()
                self._has_warned_non_vl_model = True
    
    def _reset_dump(self) -> GroupedActionDump:
        """重置转储"""
        self.dump = GroupedActionDump(
            sdk_version="1.0.0-python",  # Python 版本
            group_name=self.opts.group_name or "Midscene Report",
            group_description=self.opts.group_description,
            executions=[],
            model_briefs=[],
        )
        return self.dump
    
    def _resolve_replanning_cycle_limit(self, model_config: IModelConfig) -> int:
        """解析重规划循环限制"""
        if self.opts.replanning_cycle_limit is not None:
            return self.opts.replanning_cycle_limit
        
        if model_config.vl_mode == "vlm-ui-tars":
            return DEFAULT_VLM_UI_TARS_REPLANNING_CYCLE_LIMIT
        
        return DEFAULT_REPLANNING_CYCLE_LIMIT
    
    async def ai_tap(
        self,
        locate_prompt: Union[str, Dict[str, Any]],
        opt: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        点击元素
        
        Args:
            locate_prompt: 定位提示
            opt: 额外选项
        """
        assert_condition(locate_prompt, "missing locate prompt for tap")
        
        detailed_param = build_detailed_locate_param(locate_prompt, opt)
        await self._call_action_in_action_space("Tap", {
            "locate": detailed_param,
        })
    
    async def ai_hover(
        self,
        locate_prompt: Union[str, Dict[str, Any]],
        opt: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        悬停在元素上
        
        Args:
            locate_prompt: 定位提示
            opt: 额外选项
        """
        assert_condition(locate_prompt, "missing locate prompt for hover")
        
        detailed_param = build_detailed_locate_param(locate_prompt, opt)
        await self._call_action_in_action_space("Hover", {
            "locate": detailed_param,
        })
    
    async def ai_input(
        self,
        locate_prompt: Union[str, Dict[str, Any]],
        opt: Dict[str, Any]
    ) -> None:
        """
        输入文本
        
        Args:
            locate_prompt: 定位提示
            opt: 选项，必须包含 value 字段
        """
        value = opt.get("value")
        assert_condition(
            isinstance(value, (str, int, float)),
            "input value must be a string or number"
        )
        assert_condition(locate_prompt, "missing locate prompt for input")
        
        detailed_param = build_detailed_locate_param(locate_prompt, opt)
        await self._call_action_in_action_space("Input", {
            **opt,
            "value": str(value),
            "locate": detailed_param,
        })
    
    async def ai_keyboard_press(
        self,
        locate_prompt: Optional[Union[str, Dict[str, Any]]],
        opt: Dict[str, Any]
    ) -> None:
        """
        按下键盘按键
        
        Args:
            locate_prompt: 定位提示（可选）
            opt: 选项，必须包含 key_name 字段
        """
        key_name = opt.get("key_name")
        assert_condition(key_name, "missing key_name for keyboard press")
        
        detailed_param = None
        if locate_prompt:
            detailed_param = build_detailed_locate_param(locate_prompt, opt)
        
        await self._call_action_in_action_space("KeyboardPress", {
            **opt,
            "locate": detailed_param,
        })
    
    async def ai_scroll(
        self,
        locate_prompt: Optional[Union[str, Dict[str, Any]]],
        opt: Dict[str, Any]
    ) -> None:
        """
        滚动页面或元素
        
        Args:
            locate_prompt: 定位提示（可选）
            opt: 滚动选项
        """
        detailed_param = build_detailed_locate_param(locate_prompt or "", opt)
        await self._call_action_in_action_space("Scroll", {
            **opt,
            "locate": detailed_param,
        })
    
    async def ai_act(self, task_prompt: str, cacheable: bool = True) -> Any:
        """
        执行 AI 动作
        
        Args:
            task_prompt: 任务提示
            cacheable: 是否可缓存
            
        Returns:
            执行结果
        """
        model_config = self.model_config_manager.get_model_config("planning")
        default_config = self.model_config_manager.get_model_config("default")
        
        # 检查是否同一模型
        include_bbox = (
            model_config.model_name == default_config.model_name and
            model_config.openai_base_url == default_config.openai_base_url
        )
        
        replanning_limit = self._resolve_replanning_cycle_limit(model_config)
        
        # 获取动作空间
        action_space = await self._get_action_space()
        
        # 生成系统提示词
        system_prompt = await system_prompt_to_task_planning(
            action_space=[a.__dict__ for a in action_space],
            vl_mode=model_config.vl_mode,
            include_bbox=include_bbox,
        )
        
        # 获取上下文
        context = await self._get_ui_context()
        
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": context.screenshot_base64,
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Instruction: {task_prompt}",
                    },
                ],
            },
        ]
        
        # 调用 AI
        result = await call_ai_with_object_response(
            messages, AIActionType.PLAN, model_config
        )
        
        content = result["content"]
        
        # 解析动作
        action = content.get("action") if isinstance(content, dict) else None
        
        if action:
            action_type = action.get("type")
            action_param = action.get("param", {})
            
            debug(f"Executing action: {action_type} with param: {action_param}")
            
            # 执行动作
            await self._call_action_in_action_space(action_type, action_param)
        
        return content
    
    async def ai_query(
        self,
        demand: Union[str, Dict[str, str]],
        screenshot_included: bool = True
    ) -> Any:
        """
        查询数据
        
        Args:
            demand: 数据需求
            screenshot_included: 是否包含截图
            
        Returns:
            查询结果
        """
        model_config = self.model_config_manager.get_model_config("insight")
        result = await self.service.extract(
            demand, model_config, screenshot_included
        )
        return result.data
    
    async def ai_assert(
        self,
        assertion: Union[str, Dict[str, Any]],
        msg: Optional[str] = None,
        keep_raw_response: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        断言验证
        
        Args:
            assertion: 断言条件
            msg: 自定义错误消息
            keep_raw_response: 是否保留原始响应
            
        Returns:
            如果 keep_raw_response 为 True，返回结果字典
        """
        model_config = self.model_config_manager.get_model_config("insight")
        
        # 提取断言文本
        if isinstance(assertion, str):
            assertion_text = assertion
        else:
            assertion_text = assertion.get("prompt", str(assertion))
        
        # 使用 extract 来验证断言
        result = await self.service.extract(
            f"Verify this assertion and return {{'pass': true/false, 'thought': 'reason'}}: {assertion_text}",
            model_config,
        )
        
        data = result.data
        pass_result = data.get("pass", False) if isinstance(data, dict) else False
        thought = data.get("thought", "") if isinstance(data, dict) else ""
        
        message = None
        if not pass_result:
            message = f"Assertion failed: {msg or assertion_text}\nReason: {thought or '(no_reason)'}"
        
        if keep_raw_response:
            return {
                "pass": pass_result,
                "thought": thought,
                "message": message,
            }
        
        if not pass_result:
            raise AssertionError(message)
        
        return None
    
    async def ai_wait_for(
        self,
        assertion: Union[str, Dict[str, Any]],
        timeout_ms: int = 15000,
        check_interval_ms: int = 3000
    ) -> None:
        """
        等待条件满足
        
        Args:
            assertion: 等待条件
            timeout_ms: 超时时间（毫秒）
            check_interval_ms: 检查间隔（毫秒）
        """
        start_time = time.time()
        timeout_seconds = timeout_ms / 1000
        
        while True:
            try:
                result = await self.ai_assert(assertion, keep_raw_response=True)
                if result and result.get("pass"):
                    return
            except Exception:
                pass
            
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(
                    f"Timeout waiting for assertion: {assertion}"
                )
            
            await sleep(check_interval_ms)
    
    async def ai_locate(
        self,
        prompt: Union[str, Dict[str, Any]],
        opt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        定位元素
        
        Args:
            prompt: 定位提示
            opt: 额外选项
            
        Returns:
            定位结果
        """
        detailed_param = build_detailed_locate_param(prompt, opt)
        model_config = self.model_config_manager.get_model_config("default")
        
        result = await self.service.locate(detailed_param, model_config)
        
        if result.element:
            return {
                "rect": result.element.rect,
                "center": result.element.center,
            }
        
        return {"rect": None, "center": None}
    
    async def _get_action_space(self) -> List[DeviceAction]:
        """获取动作空间"""
        if hasattr(self.interface, "action_space"):
            return self.interface.action_space()
        return []
    
    async def _call_action_in_action_space(
        self,
        action_type: str,
        param: Dict[str, Any]
    ) -> Any:
        """
        调用动作空间中的动作
        
        Args:
            action_type: 动作类型
            param: 动作参数
            
        Returns:
            动作执行结果
        """
        debug(f"callActionInActionSpace: {action_type}, param: {param}")
        
        # 获取动作空间
        action_space = await self._get_action_space()
        
        # 查找动作
        action = None
        for a in action_space:
            if a.name == action_type:
                action = a
                break
        
        if not action:
            raise ValueError(f"Action not found: {action_type}")
        
        # 处理定位参数
        locate_param = param.get("locate")
        if locate_param:
            # 定位元素
            model_config = self.model_config_manager.get_model_config("default")
            locate_result = await self.service.locate(locate_param, model_config)
            
            if locate_result.element:
                param["locate"] = locate_result.element
            else:
                raise ValueError(f"Element not found for: {locate_param}")
        
        # 执行动作
        if action.call:
            return await action.call(param)
        
        return None
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文"""
        debug("Freezing page context")
        context = await self._get_ui_context()
        self._frozen_ui_context = context
        debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        debug("Unfreezing page context")
        self._frozen_ui_context = None
        debug("Page context unfrozen successfully")
    
    async def destroy(self) -> None:
        """销毁 Agent"""
        if self.destroyed:
            return
        
        if hasattr(self.interface, "destroy"):
            await self.interface.destroy()
        
        self._reset_dump()
        self.destroyed = True


def create_agent(
    interface_instance: Any,
    opts: Optional[AgentOpt] = None
) -> Agent:
    """
    创建 Agent 实例
    
    Args:
        interface_instance: 设备接口实例
        opts: Agent 配置选项
        
    Returns:
        Agent 实例
    """
    return Agent(interface_instance, opts)
