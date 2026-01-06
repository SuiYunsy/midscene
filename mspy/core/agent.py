"""
Agent模块 - 核心代理类
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..shared import (
    get_debug,
    IModelConfig,
    ModelConfigManager,
    global_model_config_manager,
    UIContext,
    Size,
    Rect,
    LocateResultElement,
    PlanningAction,
    PlanningAIResponse,
    DeviceAction,
    AgentOpt,
    ExecutionDump,
    GroupedActionDump,
    assert_condition,
    image_info_of_base64,
    resize_img_base64,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
    get_env_int,
)
from .device import AbstractInterface, define_action_assert
from .service import Service
from .task_runner import TaskRunner, TaskExecutionError
from .ai_model import ConversationHistory, plan, fill_bbox_param, find_all_locate_fields

debug = get_debug('agent')

# 默认重规划周期限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20


class Agent:
    """Midscene Agent - 核心代理类"""
    
    def __init__(
        self,
        interface: AbstractInterface,
        opts: Optional[AgentOpt] = None
    ):
        """
        初始化Agent
        
        Args:
            interface: 设备接口
            opts: Agent选项
        """
        self.interface = interface
        self.opts = opts or AgentOpt()
        
        # 处理重规划周期限制
        env_limit = get_env_int(MIDSCENE_REPLANNING_CYCLE_LIMIT)
        if self.opts.replanning_cycle_limit is None and env_limit:
            self.opts.replanning_cycle_limit = env_limit
        
        # 创建模型配置管理器
        if self.opts.model_config:
            self.model_config_manager = ModelConfigManager(self.opts.model_config)
        else:
            self.model_config_manager = global_model_config_manager
        
        # 创建服务
        self.service = Service(self._get_ui_context)
        
        # 对话历史
        self._conversation_history = ConversationHistory()
        
        # 截图缩放比例
        self._screenshot_scale: Optional[float] = None
        
        # 冻结的UI上下文
        self._frozen_ui_context: Optional[UIContext] = None
        
        # 销毁标志
        self.destroyed = False
        
        debug("Agent initialized")
    
    async def _get_ui_context(self) -> UIContext:
        """获取UI上下文"""
        # 如果有冻结的上下文，使用它
        if self._frozen_ui_context:
            debug("Using frozen page context")
            return self._frozen_ui_context
        
        # 获取原始上下文
        if hasattr(self.interface, 'get_context'):
            context = await self.interface.get_context()
        else:
            screenshot = await self.interface.screenshot_base64()
            size = await self.interface.size()
            context = UIContext(
                screenshot_base64=screenshot,
                size=size,
            )
        
        # 计算截图缩放比例
        screenshot_scale = await self._get_screenshot_scale(context)
        
        if screenshot_scale != 1:
            debug(f"Applying screenshot scale: {screenshot_scale:.4f}")
            target_width = round(context.size.width)
            target_height = round(context.size.height)
            debug(f"Resizing screenshot to {target_width}x{target_height}")
            context.screenshot_base64 = await resize_img_base64(
                context.screenshot_base64,
                {'width': target_width, 'height': target_height}
            )
        
        return context
    
    async def _get_screenshot_scale(self, context: UIContext) -> float:
        """获取截图缩放比例"""
        if self._screenshot_scale is not None:
            return self._screenshot_scale
        
        page_width = context.size.width
        assert_condition(
            page_width and page_width > 0,
            f"Invalid page width: {page_width}"
        )
        
        debug("Getting image info from base64")
        image_info = await image_info_of_base64(context.screenshot_base64)
        screenshot_width = image_info['width']
        debug("Image info retrieved")
        
        assert_condition(
            screenshot_width and screenshot_width > 0,
            f"Invalid screenshot width: {screenshot_width}"
        )
        
        computed_scale = screenshot_width / page_width
        assert_condition(
            computed_scale > 0,
            f"Invalid computed screenshot scale: {computed_scale}"
        )
        
        debug(
            f"Computed screenshot scale {computed_scale:.4f} "
            f"from screenshot width {screenshot_width} and page width {page_width}"
        )
        
        self._screenshot_scale = computed_scale
        return computed_scale
    
    def _get_action_space(self) -> List[DeviceAction]:
        """获取动作空间"""
        base_actions = self.interface.action_space()
        assertion_action = define_action_assert()
        return base_actions + [assertion_action]
    
    def _resolve_replanning_cycle_limit(self, model_config: IModelConfig) -> int:
        """解析重规划周期限制"""
        if self.opts.replanning_cycle_limit is not None:
            return self.opts.replanning_cycle_limit
        return DEFAULT_REPLANNING_CYCLE_LIMIT
    
    async def ai_act(self, task_prompt: str) -> Optional[Dict[str, Any]]:
        """
        执行AI动作
        
        Args:
            task_prompt: 任务提示
        
        Returns:
            执行结果
        """
        debug(f"ai_act: {task_prompt}")
        
        # 重置对话历史
        self._conversation_history.reset()
        
        model_config_for_planning = self.model_config_manager.get_model_config('planning')
        default_model_config = self.model_config_manager.get_model_config('default')
        
        # 判断是否在planning中包含bbox
        include_bbox_in_planning = (
            model_config_for_planning.model_name == default_model_config.model_name and
            model_config_for_planning.openai_base_url == default_model_config.openai_base_url
        )
        debug(f"includeBboxInPlanning: {include_bbox_in_planning}")
        
        replanning_cycle_limit = self._resolve_replanning_cycle_limit(model_config_for_planning)
        replan_count = 0
        error_count_in_loop = 0
        max_error_count = 5
        
        ai_act_context = self.opts.ai_act_context
        
        # 主规划循环
        while True:
            # 获取UI上下文
            context = await self._get_ui_context()
            
            # 调用规划
            try:
                plan_result = await plan(
                    user_instruction=task_prompt,
                    context=context,
                    interface_type=self.interface.interface_type,
                    action_space=self._get_action_space(),
                    model_config=model_config_for_planning,
                    conversation_history=self._conversation_history,
                    include_bbox=include_bbox_in_planning,
                    action_context=ai_act_context,
                    images_include_count=2,
                )
            except Exception as e:
                debug(f"Planning error: {e}")
                error_count_in_loop += 1
                if error_count_in_loop > max_error_count:
                    raise RuntimeError(f"Too many errors in planning loop: {e}")
                self._conversation_history.pending_feedback_message = f"Error in planning: {e}"
                continue
            
            debug(f"Plan result: {plan_result}")
            
            # 检查错误
            if plan_result.error:
                raise RuntimeError(f"Planning failed: {plan_result.error}")
            
            # 执行规划的动作
            actions = plan_result.actions or []
            
            for action in actions:
                try:
                    await self._execute_action(action, context)
                except Exception as e:
                    debug(f"Action execution error: {e}")
                    error_count_in_loop += 1
                    self._conversation_history.pending_feedback_message = f"Error executing action: {e}"
                    if error_count_in_loop > max_error_count:
                        raise RuntimeError(f"Too many errors in one planning loop: {e}")
                    break
            
            # 处理睡眠
            if plan_result.sleep and plan_result.sleep > 0:
                debug(f"Sleeping for {plan_result.sleep}ms")
                await asyncio.sleep(plan_result.sleep / 1000)
            
            # 检查是否完成
            if not plan_result.more_actions_needed_by_instruction:
                if error_count_in_loop == 0:
                    break
                debug("more_actions_needed is false but there were errors, continuing")
            
            # 增加重规划计数
            replan_count += 1
            
            if replan_count > replanning_cycle_limit:
                raise RuntimeError(
                    f"Replanned {replanning_cycle_limit} times, exceeding the limit. "
                    "Please configure a larger value for replanning_cycle_limit."
                )
            
            # 设置反馈消息
            if not self._conversation_history.pending_feedback_message:
                self._conversation_history.pending_feedback_message = \
                    "I have finished the action previously planned."
        
        debug("ai_act completed")
        return {'success': True}
    
    async def _execute_action(self, action: PlanningAction, context: UIContext) -> None:
        """
        执行单个动作
        
        Args:
            action: 规划动作
            context: UI上下文
        """
        action_type = action.type
        param = action.param
        
        debug(f"Executing action: {action_type} with param: {param}")
        
        # 查找动作定义
        action_space = self._get_action_space()
        action_def = None
        for a in action_space:
            if a.name == action_type:
                action_def = a
                break
        
        if not action_def:
            raise ValueError(f"Action type '{action_type}' not found")
        
        # 处理定位参数
        locate_fields = find_all_locate_fields(action_def)
        for field in locate_fields:
            locate_param = param.get(field)
            if locate_param:
                # 如果有bbox，转换为LocateResultElement
                if isinstance(locate_param, dict) and locate_param.get('bbox'):
                    bbox = locate_param['bbox']
                    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                        x1, y1, x2, y2 = bbox[:4]
                        center = ((x1 + x2) // 2, (y1 + y2) // 2)
                        rect = Rect(left=x1, top=y1, width=x2-x1, height=y2-y1)
                        param[field] = LocateResultElement(
                            center=center,
                            rect=rect,
                            description=locate_param.get('prompt', ''),
                        )
        
        # 调用动作
        if action_def.call:
            await self.interface.before_invoke_action(action_type, param)
            
            result = action_def.call(param)
            if hasattr(result, '__await__'):
                await result
            
            # 延迟
            if action_def.delay_after_runner > 0:
                await asyncio.sleep(action_def.delay_after_runner / 1000)
            
            await self.interface.after_invoke_action(action_type, param)
    
    async def ai_assert(self, assertion: str, msg: Optional[str] = None) -> None:
        """
        AI断言
        
        Args:
            assertion: 断言内容
            msg: 失败时的消息
        
        Raises:
            AssertionError: 断言失败时
        """
        debug(f"ai_assert: {assertion}")
        
        model_config = self.model_config_manager.get_model_config('insight')
        context = await self._get_ui_context()
        
        # 构建断言提示
        system_prompt = '''You are an AI assistant that helps verify assertions about a UI screenshot.

Given a screenshot and an assertion statement, determine if the assertion is true or false.

Return format:
{
  "result": true/false,  // whether the assertion is true
  "thought": "explanation of your reasoning"
}
'''
        
        from .ai_model import call_ai_with_object_response
        
        msgs = [
            {'role': 'system', 'content': system_prompt},
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f'Please verify this assertion: {assertion}',
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': context.screenshot_base64,
                            'detail': 'high',
                        },
                    },
                ],
            },
        ]
        
        response = await call_ai_with_object_response(msgs, model_config)
        result = response['content']
        
        is_pass = result.get('result', False)
        thought = result.get('thought', '')
        
        if not is_pass:
            error_msg = msg or assertion
            raise AssertionError(
                f"Assertion failed: {error_msg}\nReason: {thought or '(no reason)'}"
            )
        
        debug(f"ai_assert passed: {assertion}")
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文"""
        debug("Freezing page context")
        context = await self._get_ui_context()
        context._is_frozen = True
        self._frozen_ui_context = context
        debug("Page context frozen")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        debug("Unfreezing page context")
        self._frozen_ui_context = None
        debug("Page context unfrozen")
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self.destroyed:
            return
        
        if self.interface:
            await self.interface.destroy()
        
        self.destroyed = True
        debug("Agent destroyed")


def create_agent(
    interface: AbstractInterface,
    opts: Optional[AgentOpt] = None
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
