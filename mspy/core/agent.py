"""
Agent模块
Agent for Midscene Python SDK
"""
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
import time

from ..shared import (
    get_debug,
    assert_value,
    image_info_of_base64,
    resize_img_base64,
    UIContext,
    IModelConfig,
    ModelConfigManager,
    global_model_config_manager,
    LocateResultElement,
    Rect,
    Size,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
)
from .device import AbstractInterface, DeviceAction, define_action_assert
from .service import Service
from .task_executor import TaskExecutor, ExecutionResult, TaskExecutionError

debug = get_debug("agent")

# 默认重规划周期限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20


def distance_of_two_points(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    """计算两点之间的距离"""
    x1, y1 = p1
    x2, y2 = p2
    return round(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5)


def included_in_rect(point: Tuple[int, int], rect: Rect) -> bool:
    """检查点是否在矩形内"""
    x, y = point
    return (
        rect.left <= x <= rect.left + rect.width and
        rect.top <= y <= rect.top + rect.height
    )


@dataclass
class AgentOpt:
    """Agent选项"""
    test_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: str = ""
    generate_report: bool = True
    auto_print_report_msg: bool = True
    ai_act_context: Optional[str] = None
    report_file_name: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    replanning_cycle_limit: Optional[int] = None


class Agent:
    """
    Midscene Agent
    提供AI驱动的UI自动化能力
    """
    
    def __init__(
        self,
        interface: AbstractInterface,
        opts: Optional[AgentOpt] = None,
    ):
        """
        初始化Agent
        
        Args:
            interface: 设备接口
            opts: Agent选项
        """
        self.interface = interface
        self.opts = opts or AgentOpt()
        
        # 初始化模型配置管理器
        if self.opts.model_config:
            self.model_config_manager = ModelConfigManager(self.opts.model_config)
        else:
            self.model_config_manager = global_model_config_manager
        
        # 初始化服务
        self.service = Service(self.get_ui_context)
        
        # 获取动作空间
        base_action_space = self.interface.action_space()
        full_action_space = [*base_action_space, define_action_assert()]
        
        # 确定重规划周期限制
        replanning_limit = self.opts.replanning_cycle_limit or DEFAULT_REPLANNING_CYCLE_LIMIT
        
        # 初始化任务执行器
        self.task_executor = TaskExecutor(
            interface=self.interface,
            service=self.service,
            action_space=full_action_space,
            replanning_cycle_limit=replanning_limit,
        )
        
        self._screenshot_scale: Optional[float] = None
        self._frozen_ui_context: Optional[UIContext] = None
        self.destroyed = False
    
    async def get_ui_context(self) -> UIContext:
        """
        获取UI上下文
        
        Returns:
            UIContext对象
        """
        # 如果有冻结的上下文，直接返回
        if self._frozen_ui_context:
            debug("Using frozen page context")
            return self._frozen_ui_context
        
        # 获取原始上下文
        if hasattr(self.interface, 'get_context') and self.interface.get_context:
            context = await self.interface.get_context()
        else:
            context = await self._common_context_parser()
        
        # 计算截图缩放比例
        screenshot_scale = await self._get_screenshot_scale(context)
        
        if screenshot_scale != 1:
            debug(f"Applying screenshot scale: {screenshot_scale}")
            target_width = round(context.size.width)
            target_height = round(context.size.height)
            context.screenshot_base64 = resize_img_base64(
                context.screenshot_base64,
                {"width": target_width, "height": target_height}
            )
        
        return context
    
    async def _common_context_parser(self) -> UIContext:
        """通用上下文解析器"""
        screenshot_base64 = await self.interface.screenshot_base64()
        size = await self.interface.size()
        
        return UIContext(
            screenshot_base64=screenshot_base64,
            size=size,
        )
    
    async def _get_screenshot_scale(self, context: UIContext) -> float:
        """计算截图缩放比例"""
        if self._screenshot_scale is not None:
            return self._screenshot_scale
        
        page_width = context.size.width
        assert_value(
            page_width and page_width > 0,
            f"Invalid page width: {page_width}"
        )
        
        debug("Getting image info of base64")
        image_info = image_info_of_base64(context.screenshot_base64)
        screenshot_width = image_info.width
        debug("Image info done")
        
        assert_value(
            screenshot_width and screenshot_width > 0,
            f"Invalid screenshot width: {screenshot_width}"
        )
        
        computed_scale = screenshot_width / page_width
        assert_value(
            computed_scale > 0,
            f"Invalid computed screenshot scale: {computed_scale}"
        )
        
        debug(f"Computed screenshot scale: {computed_scale}")
        self._screenshot_scale = computed_scale
        
        return computed_scale
    
    async def ai_act(
        self,
        task_prompt: str,
        cacheable: bool = True,
    ) -> Any:
        """
        执行AI动作
        
        Args:
            task_prompt: 任务提示
            cacheable: 是否可缓存
            
        Returns:
            执行结果
        """
        model_config_for_planning = self.model_config_manager.get_model_config("planning")
        default_intent_model_config = self.model_config_manager.get_model_config("default")
        
        # 检查是否包含bbox
        include_bbox_in_planning = (
            model_config_for_planning.model_name == default_intent_model_config.model_name and
            model_config_for_planning.openai_base_url == default_intent_model_config.openai_base_url
        )
        debug(f"Setting includeBboxInPlanning to {include_bbox_in_planning}")
        
        replanning_limit = self.opts.replanning_cycle_limit or DEFAULT_REPLANNING_CYCLE_LIMIT
        
        result = await self.task_executor.action(
            user_prompt=task_prompt,
            model_config_for_planning=model_config_for_planning,
            model_config_for_default_intent=default_intent_model_config,
            include_bbox_in_planning=include_bbox_in_planning,
            ai_act_context=self.opts.ai_act_context,
            cacheable=cacheable,
            replanning_cycle_limit_override=replanning_limit,
        )
        
        return result.output
    
    async def ai_assert(
        self,
        assertion: str,
        msg: Optional[str] = None,
    ) -> bool:
        """
        执行AI断言
        
        Args:
            assertion: 断言内容
            msg: 失败消息
            
        Returns:
            断言是否通过
            
        Raises:
            AssertionError: 断言失败时
        """
        model_config = self.model_config_manager.get_model_config("insight")
        
        try:
            result = await self.service.extract(
                {"StatementIsTruthy": f"Boolean, whether the following statement is true: {assertion}"},
                model_config,
            )
            
            data = result.get("data", {})
            pass_result = bool(data.get("StatementIsTruthy"))
            thought = result.get("thought", "")
            
            if not pass_result:
                message = f"Assertion failed: {msg or assertion}\nReason: {thought or '(no_reason)'}"
                raise AssertionError(message)
            
            return True
            
        except Exception as e:
            if isinstance(e, AssertionError):
                raise
            raise AssertionError(f"Assertion failed: {msg or assertion}\nReason: {str(e)}")
    
    async def ai_wait_for(
        self,
        assertion: str,
        timeout_ms: int = 15000,
        check_interval_ms: int = 3000,
    ) -> None:
        """
        等待断言成立
        
        Args:
            assertion: 断言内容
            timeout_ms: 超时时间（毫秒）
            check_interval_ms: 检查间隔（毫秒）
        """
        model_config = self.model_config_manager.get_model_config("insight")
        
        await self.task_executor.wait_for(
            assertion=assertion,
            timeout_ms=timeout_ms,
            check_interval_ms=check_interval_ms,
            model_config=model_config,
        )
    
    async def ai_locate(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        AI定位元素
        
        Args:
            prompt: 定位提示
            
        Returns:
            包含rect和center的字典
        """
        model_config = self.model_config_manager.get_model_config("default")
        
        context = await self.get_ui_context()
        
        result = await self.service.locate(
            prompt,
            {"context": context},
            model_config,
        )
        
        if result.element:
            return {
                "rect": result.element.rect,
                "center": result.element.center,
            }
        
        raise ValueError(f"Element not found: {prompt}")
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文"""
        debug("Freezing page context")
        context = await self.get_ui_context()
        context._is_frozen = True
        self._frozen_ui_context = context
        debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        debug("Unfreezing page context")
        self._frozen_ui_context = None
        debug("Page context unfrozen successfully")
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self.destroyed:
            return
        
        if hasattr(self.interface, 'destroy') and self.interface.destroy:
            await self.interface.destroy()
        
        self.destroyed = True


def create_agent(
    interface: AbstractInterface,
    opts: Optional[AgentOpt] = None,
) -> Agent:
    """
    创建Agent实例
    
    Args:
        interface: 设备接口
        opts: Agent选项
        
    Returns:
        Agent实例
    """
    return Agent(interface, opts)
