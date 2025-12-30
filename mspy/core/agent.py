"""
Agent - 智能体模块
提供 aiAct、aiAssert 等核心功能
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable

from mspy.shared.types import (
    DeviceAction,
    IModelConfig,
    PlanningAction,
    LocateResultElement,
    Rect,
    Size,
    UIContext,
)
from mspy.shared.config import (
    GlobalConfigManager,
    ModelConfigManager,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
)
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition, uuid
from mspy.core.types import (
    ConversationHistory,
    ExecutionDump,
    ExecutionTask,
    ExecutionTaskStatus,
    GroupedActionDump,
)
from mspy.core.service import Service
from mspy.core.ai_model import plan


debug = get_debug("agent")


# 默认重规划周期限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20


@dataclass
class AgentOpt:
    """Agent 配置选项"""
    test_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: Optional[str] = None
    generate_report: bool = True
    auto_print_report_msg: bool = True
    ai_act_context: Optional[str] = None
    report_file_name: Optional[str] = None
    model_config: Optional[Dict[str, Union[str, int]]] = None
    replanning_cycle_limit: Optional[int] = None
    create_openai_client: Optional[Callable[..., Any]] = None


@dataclass
class AiActOptions:
    """aiAct 选项"""
    cacheable: bool = True


class AbstractInterface:
    """抽象接口基类"""
    
    @property
    def interface_type(self) -> str:
        """接口类型"""
        raise NotImplementedError
    
    async def screenshot_base64(self) -> str:
        """获取截图 base64"""
        raise NotImplementedError
    
    async def size(self) -> Size:
        """获取页面尺寸"""
        raise NotImplementedError
    
    def action_space(self) -> List[DeviceAction]:
        """获取动作空间"""
        raise NotImplementedError
    
    async def destroy(self) -> None:
        """销毁接口"""
        pass


class Agent:
    """
    Midscene 智能体
    提供 aiAct、aiAssert 等核心功能
    """
    
    def __init__(
        self,
        interface: AbstractInterface,
        opts: Optional[AgentOpt] = None,
    ):
        """
        初始化智能体
        
        Args:
            interface: 设备接口
            opts: 配置选项
        """
        self.interface = interface
        self.opts = opts or AgentOpt()
        
        # 模型配置管理器
        if self.opts.model_config or self.opts.create_openai_client:
            self.model_config_manager = ModelConfigManager(
                self.opts.model_config,
                self.opts.create_openai_client,
            )
        else:
            from mspy.shared.config import global_model_config_manager
            self.model_config_manager = global_model_config_manager
        
        # 服务
        self.service = Service(self._get_ui_context)
        
        # 转储数据
        self.dump = self._reset_dump()
        
        # 状态
        self.destroyed = False
        self._frozen_ui_context: Optional[UIContext] = None
        self._has_warned_non_vl_model = False
        self._conversation_history = ConversationHistory()
    
    def _reset_dump(self) -> GroupedActionDump:
        """重置转储数据"""
        return GroupedActionDump(
            sdk_version="0.1.0",  # Python 版本
            group_name=self.opts.group_name,
            group_description=self.opts.group_description,
            executions=[],
            model_briefs=[],
        )
    
    def _ensure_vl_model_warning(self) -> None:
        """确保 VL 模型警告只显示一次"""
        if not self._has_warned_non_vl_model:
            # Python 实现只支持 playwright 和 static
            if self.interface.interface_type not in ("playwright", "static"):
                self.model_config_manager.throw_error_if_non_vl_model()
                self._has_warned_non_vl_model = True
    
    async def _get_ui_context(self) -> UIContext:
        """获取 UI 上下文"""
        self._ensure_vl_model_warning()
        
        # 如果上下文已冻结，返回冻结的上下文
        if self._frozen_ui_context:
            debug("Using frozen page context")
            return self._frozen_ui_context
        
        # 获取新的上下文
        screenshot = await self.interface.screenshot_base64()
        size = await self.interface.size()
        
        class SimpleUIContext(UIContext):
            def __init__(self, screenshot: str, size: Size):
                self._screenshot = screenshot
                self._size = size
            
            @property
            def screenshot_base64(self) -> str:
                return self._screenshot
            
            @property
            def size(self) -> Size:
                return self._size
        
        return SimpleUIContext(screenshot, size)
    
    def _resolve_replanning_cycle_limit(self, model_config: IModelConfig) -> int:
        """解析重规划周期限制"""
        if self.opts.replanning_cycle_limit is not None:
            return self.opts.replanning_cycle_limit
        
        return DEFAULT_REPLANNING_CYCLE_LIMIT
    
    async def ai_act(
        self,
        task_prompt: str,
        opt: Optional[AiActOptions] = None,
    ) -> Dict[str, Any]:
        """
        执行 AI 动作规划
        
        Args:
            task_prompt: 任务提示
            opt: 可选配置
            
        Returns:
            执行结果
        """
        debug("ai_act:", task_prompt)
        
        model_config_for_planning = self.model_config_manager.get_model_config("planning")
        default_model_config = self.model_config_manager.get_model_config("default")
        
        # 是否在规划中包含 bbox
        include_bbox = (
            model_config_for_planning.model_name == default_model_config.model_name
            and model_config_for_planning.openai_base_url == default_model_config.openai_base_url
        )
        debug("include_bbox in planning:", include_bbox)
        
        replanning_cycle_limit = self._resolve_replanning_cycle_limit(model_config_for_planning)
        
        # 获取动作空间
        action_space = self.interface.action_space()
        
        # 添加断言动作
        assert_action = DeviceAction(
            name="Print_Assert_Result",
            description="Print the result of the assertion",
            param_schema={
                "condition": {"type": "string", "description": "The condition of the assertion"},
                "thought": {"type": "string", "description": "The thought process"},
                "result": {"type": "boolean", "description": "The result, true or false"},
            },
        )
        action_space = [*action_space, assert_action]
        
        # 重规划循环
        cycle_count = 0
        all_actions: List[PlanningAction] = []
        
        while cycle_count < replanning_cycle_limit:
            cycle_count += 1
            debug(f"Planning cycle {cycle_count}/{replanning_cycle_limit}")
            
            # 获取 UI 上下文
            context = await self._get_ui_context()
            
            # 执行规划
            planning_result = plan(
                user_instruction=task_prompt,
                context_screenshot_base64=context.screenshot_base64,
                context_size={"width": context.size.width, "height": context.size.height},
                interface_type=self.interface.interface_type,
                action_space=action_space,
                model_config=model_config_for_planning,
                conversation_history=self._conversation_history,
                include_bbox=include_bbox,
                action_context=self.opts.ai_act_context,
                images_include_count=2,
            )
            
            # 检查错误
            if planning_result.error:
                debug("Planning error:", planning_result.error)
                raise RuntimeError(f"Planning failed: {planning_result.error}")
            
            # 处理动作
            for action in planning_result.actions:
                debug(f"Executing action: {action.type}")
                all_actions.append(action)
                
                # 执行动作
                await self._execute_action(action, action_space)
            
            # 检查是否需要继续
            if not planning_result.more_actions_needed_by_instruction:
                debug("No more actions needed")
                break
            
            # 处理 sleep
            if planning_result.sleep:
                debug(f"Sleeping for {planning_result.sleep}ms")
                await asyncio.sleep(planning_result.sleep / 1000)
        
        return {
            "actions": all_actions,
            "cycle_count": cycle_count,
        }
    
    async def _execute_action(
        self,
        action: PlanningAction,
        action_space: List[DeviceAction],
    ) -> Any:
        """
        执行单个动作
        
        Args:
            action: 规划动作
            action_space: 动作空间
            
        Returns:
            执行结果
        """
        action_type = action.type
        param = action.param
        
        # 查找动作定义
        action_def = next(
            (a for a in action_space if a.name == action_type),
            None
        )
        
        if not action_def:
            raise ValueError(f"Unknown action type: {action_type}")
        
        if not action_def.call:
            debug(f"Action {action_type} has no call function, skipping")
            return None
        
        # 处理 locate 参数，转换为 LocateResultElement
        if param:
            for key in ["locate", "from", "to", "start", "end"]:
                if key in param and param[key]:
                    locate_data = param[key]
                    if isinstance(locate_data, dict) and "bbox" in locate_data:
                        bbox = locate_data["bbox"]
                        param[key] = LocateResultElement(
                            description=locate_data.get("prompt", ""),
                            center=((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2),
                            rect=Rect(
                                left=bbox[0],
                                top=bbox[1],
                                width=bbox[2] - bbox[0],
                                height=bbox[3] - bbox[1],
                            ),
                        )
        
        # 调用动作
        result = action_def.call(param)
        if asyncio.iscoroutine(result):
            result = await result
        
        return result
    
    async def ai_assert(
        self,
        assertion: str,
        msg: Optional[str] = None,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行 AI 断言
        
        Args:
            assertion: 断言文本
            msg: 失败时的消息
            opt: 可选配置
            
        Returns:
            断言结果
        """
        debug("ai_assert:", assertion)
        
        model_config = self.model_config_manager.get_model_config("insight")
        
        result = await self.service.assert_condition(
            assertion=assertion,
            model_config=model_config,
            options=opt,
        )
        
        passed = result["passed"]
        thought = result["thought"]
        
        keep_raw_response = opt.get("keepRawResponse", False) if opt else False
        
        if keep_raw_response:
            message = None if passed else f"Assertion failed: {msg or assertion}\nReason: {thought or '(no_reason)'}"
            return {
                "pass": passed,
                "thought": thought,
                "message": message,
            }
        
        if not passed:
            raise AssertionError(f"Assertion failed: {msg or assertion}\nReason: {thought or '(no_reason)'}")
        
        return {"pass": True}
    
    async def ai(self, task_prompt: str, opt: Optional[AiActOptions] = None) -> Dict[str, Any]:
        """
        aiAct 的别名
        
        Args:
            task_prompt: 任务提示
            opt: 可选配置
            
        Returns:
            执行结果
        """
        return await self.ai_act(task_prompt, opt)
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文"""
        debug("Freezing page context")
        context = await self._get_ui_context()
        context.is_frozen = True
        self._frozen_ui_context = context
        debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        debug("Unfreezing page context")
        self._frozen_ui_context = None
        debug("Page context unfrozen successfully")
    
    async def destroy(self) -> None:
        """销毁智能体"""
        if self.destroyed:
            return
        
        await self.interface.destroy()
        self.dump = self._reset_dump()
        self.destroyed = True


def create_agent(
    interface: AbstractInterface,
    opts: Optional[AgentOpt] = None,
) -> Agent:
    """
    创建智能体
    
    Args:
        interface: 设备接口
        opts: 配置选项
        
    Returns:
        Agent 实例
    """
    return Agent(interface, opts)
