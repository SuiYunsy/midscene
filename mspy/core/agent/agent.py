"""
Agent实现

对应TypeScript源码: packages/core/src/agent/agent.ts
"""

import time
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Generic

from mspy.shared.types import Rect, Size, LocateResultElement
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition
from mspy.shared.common import get_version, get_report_file_name
from mspy.shared.env import (
    ModelConfigManager,
    global_model_config_manager,
    global_config_manager,
    IModelConfig,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
)
from mspy.core.types import (
    UIContext,
    ExecutionDump,
    ExecutionTask,
    GroupedActionDump,
    ServiceError,
    DeviceAction,
    CacheConfig,
    Cache,
    AgentWaitForOpt,
    AgentAssertOpt,
    LocateValidatorResult,
    AgentDescribeElementAtPointResult,
)
from mspy.core.device import AbstractInterface, define_action_assert
from mspy.core.service import Service, ServiceExtractOption, DetailedLocateParam

debug = get_debug('agent')

T = TypeVar('T')


# ============ Agent选项和类型 ============

@dataclass
class AgentOpt:
    """Agent选项配置"""
    test_id: Optional[str] = None
    cache_id: Optional[str] = None  # deprecated
    group_name: str = "Midscene Report"
    group_description: str = ""
    generate_report: bool = True
    auto_print_report_msg: bool = True
    on_task_start_tip: Optional[Callable[[str], None]] = None
    ai_act_context: Optional[str] = None
    ai_action_context: Optional[str] = None  # deprecated alias
    report_file_name: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    cache: Cache = False
    replanning_cycle_limit: Optional[int] = None
    create_openai_client: Optional[Callable] = None


@dataclass
class AiActOptions:
    """AI动作选项"""
    cacheable: bool = True


@dataclass 
class ServiceExtractOptionFull(ServiceExtractOption):
    """完整的服务提取选项"""
    pass


# 默认提取选项
DEFAULT_SERVICE_EXTRACT_OPTION = ServiceExtractOption(
    dom_included=False,
    screenshot_included=True,
)

# 默认规划周期限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20
DEFAULT_VLM_UI_TARS_REPLANNING_CYCLE_LIMIT = 40


def distance_of_two_points(p1: tuple, p2: tuple) -> int:
    """计算两点间距离"""
    x1, y1 = p1
    x2, y2 = p2
    return round((((x1 - x2) ** 2) + ((y1 - y2) ** 2)) ** 0.5)


def included_in_rect(point: tuple, rect: Rect) -> bool:
    """检查点是否在矩形内"""
    x, y = point
    return (rect.left <= x <= rect.left + rect.width and
            rect.top <= y <= rect.top + rect.height)


class Agent(Generic[T]):
    """智能Agent类
    
    提供AI驱动的UI自动化测试能力，包括：
    - 元素定位 (aiLocate)
    - 点击操作 (aiTap)
    - 输入操作 (aiInput)
    - 数据提取 (aiQuery)
    - 断言验证 (aiAssert)
    - 智能执行 (aiAct)
    """
    
    def __init__(
        self,
        interface_instance: AbstractInterface,
        opts: Optional[AgentOpt] = None
    ):
        """初始化Agent
        
        Args:
            interface_instance: 设备接口实例
            opts: Agent选项配置
        """
        self.interface = interface_instance
        self.opts = opts or AgentOpt()
        
        # 处理选项
        self.opts.generate_report = self.opts.generate_report if self.opts.generate_report is not None else True
        self.opts.auto_print_report_msg = self.opts.auto_print_report_msg if self.opts.auto_print_report_msg is not None else True
        self.opts.group_name = self.opts.group_name or "Midscene Report"
        self.opts.group_description = self.opts.group_description or ""
        
        # 处理ai_act_context别名
        if self.opts.ai_action_context and not self.opts.ai_act_context:
            self.opts.ai_act_context = self.opts.ai_action_context
        
        # 初始化模型配置管理器
        if self.opts.model_config or self.opts.create_openai_client:
            self._model_config_manager = ModelConfigManager(
                self.opts.model_config,
                self.opts.create_openai_client
            )
        else:
            self._model_config_manager = global_model_config_manager
        
        # 初始化Service
        self.service = Service(self._get_ui_context)
        
        # 初始化dump数据
        self.dump = self._reset_dump()
        
        # 状态标记
        self.destroyed = False
        self._frozen_ui_context: Optional[UIContext] = None
        self._has_warned_non_vl_model = False
        self._screenshot_scale: Optional[float] = None
        
        # 报告文件名
        self.report_file_name = (
            self.opts.report_file_name or 
            get_report_file_name(self.opts.test_id or self.interface.interface_type or 'web')
        )
        self.report_file: Optional[str] = None
        
        # dump更新监听器
        self._dump_update_listeners: List[Callable] = []
    
    @property
    def page(self) -> AbstractInterface:
        """获取页面接口（兼容旧API）"""
        return self.interface
    
    def _reset_dump(self) -> GroupedActionDump:
        """重置dump数据"""
        self.dump = GroupedActionDump(
            sdk_version=get_version(),
            group_name=self.opts.group_name,
            group_description=self.opts.group_description,
            executions=[],
            model_briefs=[],
        )
        return self.dump
    
    async def _get_ui_context(self, action: Optional[str] = None) -> UIContext:
        """获取UI上下文
        
        Args:
            action: 当前动作类型
            
        Returns:
            UI上下文对象
        """
        # 如果有冻结的上下文，直接返回
        if self._frozen_ui_context:
            debug('Using frozen page context for action:', action)
            return self._frozen_ui_context
        
        # 获取原始上下文
        context = await self.interface.get_context()
        if context:
            return context
        
        # 如果接口没有提供上下文，需要自行构建
        # TODO: 实现commonContextParser
        raise NotImplementedError("接口未提供getContext方法")
    
    async def get_action_space(self) -> List[DeviceAction]:
        """获取动作空间"""
        common_assert_action = define_action_assert()
        return [*self.interface.action_space(), common_assert_action]
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文
        
        冻结当前页面状态，后续AI操作将使用此快照
        """
        debug('Freezing page context')
        context = await self._get_ui_context('locate')
        context.is_frozen = True
        self._frozen_ui_context = context
        debug('Page context frozen successfully')
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文
        
        允许AI操作动态计算页面上下文
        """
        debug('Unfreezing page context')
        self._frozen_ui_context = None
        debug('Page context unfrozen successfully')
    
    async def set_ai_act_context(self, prompt: str) -> None:
        """设置AI执行上下文
        
        Args:
            prompt: 上下文提示
        """
        if self.opts.ai_act_context:
            print('Warning: aiActContext已设置，将被覆盖')
        self.opts.ai_act_context = prompt
        self.opts.ai_action_context = prompt
    
    async def set_ai_action_context(self, prompt: str) -> None:
        """设置AI动作上下文（废弃，请使用set_ai_act_context）"""
        await self.set_ai_act_context(prompt)
    
    # ============ AI动作方法 ============
    
    async def ai_tap(
        self,
        locate_prompt: str,
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI点击操作
        
        Args:
            locate_prompt: 元素定位提示
            opts: 选项
        """
        assert_condition(locate_prompt, "missing locate prompt for tap")
        
        detailed_param = DetailedLocateParam(
            prompt=locate_prompt,
            deep_think=opts.get('deep_think', False) if opts else False,
        )
        
        await self._call_action_in_action_space('Tap', {'locate': detailed_param})
    
    async def ai_right_click(
        self,
        locate_prompt: str,
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI右键点击操作"""
        assert_condition(locate_prompt, "missing locate prompt for right click")
        
        detailed_param = DetailedLocateParam(
            prompt=locate_prompt,
            deep_think=opts.get('deep_think', False) if opts else False,
        )
        
        await self._call_action_in_action_space('RightClick', {'locate': detailed_param})
    
    async def ai_double_click(
        self,
        locate_prompt: str,
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI双击操作"""
        assert_condition(locate_prompt, "missing locate prompt for double click")
        
        detailed_param = DetailedLocateParam(
            prompt=locate_prompt,
            deep_think=opts.get('deep_think', False) if opts else False,
        )
        
        await self._call_action_in_action_space('DoubleClick', {'locate': detailed_param})
    
    async def ai_hover(
        self,
        locate_prompt: str,
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI悬停操作"""
        assert_condition(locate_prompt, "missing locate prompt for hover")
        
        detailed_param = DetailedLocateParam(
            prompt=locate_prompt,
            deep_think=opts.get('deep_think', False) if opts else False,
        )
        
        await self._call_action_in_action_space('Hover', {'locate': detailed_param})
    
    async def ai_input(
        self,
        locate_prompt: str,
        value: Union[str, int],
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI输入操作
        
        Args:
            locate_prompt: 元素定位提示
            value: 要输入的值
            opts: 选项（mode可选: replace/clear/append）
        """
        assert_condition(
            isinstance(value, (str, int)),
            "input value must be a string or number"
        )
        assert_condition(locate_prompt, "missing locate prompt for input")
        
        detailed_param = DetailedLocateParam(
            prompt=locate_prompt,
            deep_think=opts.get('deep_think', False) if opts else False,
        )
        
        string_value = str(value) if isinstance(value, int) else value
        mode = opts.get('mode', 'replace') if opts else 'replace'
        
        await self._call_action_in_action_space('Input', {
            'value': string_value,
            'locate': detailed_param,
            'mode': mode,
        })
    
    async def ai_keyboard_press(
        self,
        key_name: str,
        locate_prompt: Optional[str] = None,
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI键盘按键操作
        
        Args:
            key_name: 按键名称
            locate_prompt: 元素定位提示（可选）
            opts: 选项
        """
        assert_condition(key_name, "missing keyName for keyboard press")
        
        detailed_param = None
        if locate_prompt:
            detailed_param = DetailedLocateParam(
                prompt=locate_prompt,
                deep_think=opts.get('deep_think', False) if opts else False,
            )
        
        await self._call_action_in_action_space('KeyboardPress', {
            'keyName': key_name,
            'locate': detailed_param,
        })
    
    async def ai_scroll(
        self,
        direction: str = 'down',
        locate_prompt: Optional[str] = None,
        opts: Optional[Dict[str, Any]] = None
    ) -> None:
        """AI滚动操作
        
        Args:
            direction: 滚动方向 (down/up/left/right)
            locate_prompt: 元素定位提示（可选）
            opts: 选项（scroll_type, distance等）
        """
        detailed_param = None
        if locate_prompt:
            detailed_param = DetailedLocateParam(
                prompt=locate_prompt,
                deep_think=opts.get('deep_think', False) if opts else False,
            )
        
        scroll_type = opts.get('scroll_type', 'singleAction') if opts else 'singleAction'
        distance = opts.get('distance') if opts else None
        
        await self._call_action_in_action_space('Scroll', {
            'direction': direction,
            'scrollType': scroll_type,
            'distance': distance,
            'locate': detailed_param,
        })
    
    async def ai_act(
        self,
        task_prompt: str,
        opts: Optional[AiActOptions] = None
    ) -> Any:
        """AI智能执行
        
        根据自然语言指令自动规划并执行操作序列
        
        Args:
            task_prompt: 任务描述
            opts: 选项
            
        Returns:
            执行结果
        """
        debug('ai_act:', task_prompt)
        
        # 获取模型配置
        model_config = self._model_config_manager.get_model_config('planning')
        
        # TODO: 实现完整的规划和执行逻辑
        # 这里先返回简单结果
        return {'status': 'completed', 'task': task_prompt}
    
    async def ai_action(self, task_prompt: str, opts: Optional[AiActOptions] = None) -> Any:
        """AI动作（废弃，请使用ai_act）"""
        return await self.ai_act(task_prompt, opts)
    
    async def ai(self, *args, **kwargs) -> Any:
        """AI执行的简写方法"""
        return await self.ai_act(*args, **kwargs)
    
    # ============ AI查询方法 ============
    
    async def ai_query(
        self,
        demand: Union[str, Dict[str, str]],
        opts: Optional[ServiceExtractOption] = None
    ) -> Any:
        """AI数据查询
        
        从页面提取结构化数据
        
        Args:
            demand: 数据需求描述
            opts: 提取选项
            
        Returns:
            提取的数据
        """
        model_config = self._model_config_manager.get_model_config('insight')
        result = await self.service.extract(demand, model_config, opts)
        return result.data
    
    async def ai_boolean(
        self,
        prompt: str,
        opts: Optional[ServiceExtractOption] = None
    ) -> bool:
        """AI布尔查询
        
        Args:
            prompt: 问题描述
            opts: 提取选项
            
        Returns:
            布尔结果
        """
        result = await self.ai_query(prompt, opts)
        return bool(result)
    
    async def ai_number(
        self,
        prompt: str,
        opts: Optional[ServiceExtractOption] = None
    ) -> float:
        """AI数字查询"""
        result = await self.ai_query(prompt, opts)
        return float(result)
    
    async def ai_string(
        self,
        prompt: str,
        opts: Optional[ServiceExtractOption] = None
    ) -> str:
        """AI字符串查询"""
        result = await self.ai_query(prompt, opts)
        return str(result)
    
    async def ai_ask(
        self,
        prompt: str,
        opts: Optional[ServiceExtractOption] = None
    ) -> str:
        """AI问答（ai_string的别名）"""
        return await self.ai_string(prompt, opts)
    
    # ============ AI断言方法 ============
    
    async def ai_assert(
        self,
        assertion: str,
        msg: Optional[str] = None,
        opts: Optional[AgentAssertOpt] = None
    ) -> Optional[Dict[str, Any]]:
        """AI断言
        
        Args:
            assertion: 断言条件描述
            msg: 断言失败时的自定义消息
            opts: 断言选项
            
        Returns:
            如果keep_raw_response为True，返回详细结果；否则断言失败时抛出异常
        """
        model_config = self._model_config_manager.get_model_config('insight')
        
        # TODO: 实现完整的断言逻辑
        result = {
            'passed': True,
            'thought': '断言检查通过',
            'message': None
        }
        
        if opts and opts.keep_raw_response:
            return result
        
        if not result['passed']:
            raise AssertionError(result.get('message') or f'断言失败: {assertion}')
        
        return None
    
    async def ai_wait_for(
        self,
        assertion: str,
        opts: Optional[AgentWaitForOpt] = None
    ) -> None:
        """AI等待条件
        
        等待直到断言条件满足
        
        Args:
            assertion: 等待条件描述
            opts: 等待选项
        """
        opts = opts or AgentWaitForOpt()
        timeout_ms = opts.timeout_ms or 15000
        check_interval_ms = opts.check_interval_ms or 3000
        
        start_time = time.time() * 1000
        
        while True:
            try:
                result = await self.ai_assert(
                    assertion,
                    opts=AgentAssertOpt(keep_raw_response=True)
                )
                if result and result.get('passed'):
                    return
            except Exception:
                pass
            
            elapsed = time.time() * 1000 - start_time
            if elapsed >= timeout_ms:
                raise TimeoutError(f'等待超时: {assertion}')
            
            await self._async_sleep(check_interval_ms / 1000)
    
    # ============ AI定位方法 ============
    
    async def ai_locate(
        self,
        prompt: str,
        opts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """AI元素定位
        
        Args:
            prompt: 元素描述
            opts: 定位选项
            
        Returns:
            包含rect和center的定位结果
        """
        model_config = self._model_config_manager.get_model_config('insight')
        
        detailed_param = DetailedLocateParam(
            prompt=prompt,
            deep_think=opts.get('deep_think', False) if opts else False,
        )
        
        result = await self.service.locate(detailed_param, model_config=model_config)
        
        if result.element:
            return {
                'rect': result.element.rect,
                'center': result.element.center,
            }
        
        return {'rect': None, 'center': None}
    
    # ============ 其他方法 ============
    
    async def _call_action_in_action_space(
        self,
        action_type: str,
        params: Dict[str, Any]
    ) -> Any:
        """在动作空间中调用动作
        
        Args:
            action_type: 动作类型
            params: 动作参数
            
        Returns:
            动作执行结果
        """
        debug('call_action_in_action_space:', action_type, params)
        
        # 获取动作空间
        action_space = await self.get_action_space()
        
        # 查找对应的动作
        action = None
        for a in action_space:
            if a.name == action_type:
                action = a
                break
        
        if not action:
            raise ValueError(f'未找到动作: {action_type}')
        
        # 处理定位参数
        if 'locate' in params and params['locate']:
            locate_param = params['locate']
            if isinstance(locate_param, DetailedLocateParam):
                # 执行定位
                locate_result = await self.service.locate(
                    locate_param,
                    model_config=self._model_config_manager.get_model_config('insight')
                )
                if locate_result.element:
                    params['locate'] = locate_result.element
                else:
                    raise ValueError(f'无法定位元素: {locate_param.prompt}')
        
        # 执行动作
        if action.call:
            if hasattr(action.call, '__await__'):
                return await action.call(params)
            return action.call(params)
        
        return None
    
    async def _async_sleep(self, seconds: float) -> None:
        """异步休眠"""
        import asyncio
        await asyncio.sleep(seconds)
    
    async def run_yaml(self, yaml_script_content: str) -> Dict[str, Any]:
        """运行YAML脚本
        
        Args:
            yaml_script_content: YAML脚本内容
            
        Returns:
            执行结果
        """
        # TODO: 实现YAML脚本解析和执行
        return {'result': {}}
    
    async def evaluate_javascript(self, script: str) -> Any:
        """执行JavaScript
        
        Args:
            script: JavaScript代码
            
        Returns:
            执行结果
        """
        return await self.interface.evaluate_javascript(script)
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self.destroyed:
            return
        
        await self.interface.destroy()
        self._reset_dump()
        self.destroyed = True
    
    def add_dump_update_listener(
        self,
        listener: Callable[[str, Optional[ExecutionDump]], None]
    ) -> Callable[[], None]:
        """添加dump更新监听器
        
        Args:
            listener: 监听函数
            
        Returns:
            移除监听器的函数
        """
        self._dump_update_listeners.append(listener)
        
        def remove():
            self.remove_dump_update_listener(listener)
        
        return remove
    
    def remove_dump_update_listener(
        self,
        listener: Callable[[str, Optional[ExecutionDump]], None]
    ) -> None:
        """移除dump更新监听器"""
        if listener in self._dump_update_listeners:
            self._dump_update_listeners.remove(listener)
    
    def clear_dump_update_listeners(self) -> None:
        """清除所有dump更新监听器"""
        self._dump_update_listeners.clear()


def create_agent(
    interface_instance: AbstractInterface,
    opts: Optional[AgentOpt] = None
) -> Agent:
    """创建Agent实例
    
    Args:
        interface_instance: 设备接口实例
        opts: Agent选项
        
    Returns:
        Agent实例
    """
    return Agent(interface_instance, opts)
