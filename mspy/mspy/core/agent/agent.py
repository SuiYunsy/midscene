"""
Agent实现

提供AI驱动的UI自动化Agent。
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List, Callable, Awaitable, Union, Tuple, TypeVar

from mspy.core.types import (
    UIContext,
    WebUIContext,
    ExecutionDump,
    ExecutionTask,
    GroupedActionDump,
    ServiceExtractOption,
    LocateOption,
    DetailedLocateParam,
    ScrollParam,
    CacheConfig,
)
from mspy.core.common import TUserPrompt
from mspy.core.device import AbstractInterface, DeviceAction
from mspy.core.service import Service
from mspy.shared.env import (
    ModelConfig,
    ModelConfigManager,
    global_model_config_manager,
    global_config_manager,
    CreateOpenAIClientFn,
)
from mspy.shared.env.types import MIDSCENE_REPLANNING_CYCLE_LIMIT
from mspy.shared.types import Rect, Size, LocateResultElement
from mspy.shared.img import image_info_of_base64, resize_img_base64
from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

logger = logging.getLogger("midscene.agent")
debug = get_debug("agent")

T = TypeVar("T")


def get_version() -> str:
    """获取SDK版本"""
    return "0.1.0"  # Python版本


class AgentOpt:
    """Agent选项"""
    
    def __init__(
        self,
        test_id: Optional[str] = None,
        group_name: str = "Midscene Report",
        group_description: str = "",
        generate_report: bool = True,
        auto_print_report_msg: bool = True,
        report_file_name: Optional[str] = None,
        model_config: Optional[Dict[str, str | int]] = None,
        cache: Optional[Union[bool, CacheConfig]] = None,
        replanning_cycle_limit: Optional[int] = None,
        ai_act_context: Optional[str] = None,
        create_openai_client: Optional[CreateOpenAIClientFn] = None,
        on_task_start_tip: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        self.test_id = test_id
        self.group_name = group_name
        self.group_description = group_description
        self.generate_report = generate_report
        self.auto_print_report_msg = auto_print_report_msg
        self.report_file_name = report_file_name
        self.model_config = model_config
        self.cache = cache
        self.replanning_cycle_limit = replanning_cycle_limit
        self.ai_act_context = ai_act_context
        self.create_openai_client = create_openai_client
        self.on_task_start_tip = on_task_start_tip


def build_detailed_locate_param(
    prompt: TUserPrompt,
    opt: Optional[LocateOption] = None,
) -> DetailedLocateParam:
    """
    构建详细定位参数
    
    Args:
        prompt: 用户提示
        opt: 定位选项
        
    Returns:
        详细定位参数
    """
    if isinstance(prompt, str):
        text_prompt = prompt
    else:
        text_prompt = prompt.prompt if hasattr(prompt, "prompt") else str(prompt)
    
    return DetailedLocateParam(
        prompt=text_prompt,
        deep_think=opt.deep_think if opt else False,
        cacheable=opt.cacheable if opt else True,
    )


class Agent:
    """
    AI驱动的UI自动化Agent
    
    提供aiAct、aiLocate、aiAssert等方法进行AI驱动的UI操作。
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
        
        self.dump = GroupedActionDump(
            sdk_version=get_version(),
            group_name=self.opts.group_name,
            group_description=self.opts.group_description,
        )
        
        self.report_file: Optional[str] = None
        self.destroyed = False
        
        # 模型配置管理器
        has_custom_config = self.opts.model_config or self.opts.create_openai_client
        self.model_config_manager = (
            ModelConfigManager(self.opts.model_config, self.opts.create_openai_client)
            if has_custom_config
            else global_model_config_manager
        )
        
        # 服务层
        self.service = Service(self.get_ui_context)
        
        # 截图缩放比例
        self._screenshot_scale: Optional[float] = None
        
        # 冻结的UI上下文
        self._frozen_ui_context: Optional[UIContext] = None
        
        # VL模型警告标志
        self._has_warned_non_vl_model = False
        
        # 回调
        self.on_task_start_tip = self.opts.on_task_start_tip
    
    async def get_ui_context(self, action: Optional[str] = None) -> UIContext:
        """
        获取UI上下文
        
        Args:
            action: 操作类型（可选）
            
        Returns:
            UI上下文
        """
        # 检查VL模型配置
        self._ensure_vl_model_warning()
        
        # 如果有冻结的上下文，直接返回
        if self._frozen_ui_context:
            debug(f"Using frozen page context for action: {action}")
            return self._frozen_ui_context
        
        # 获取上下文
        if hasattr(self.interface, "get_context"):
            context = await self.interface.get_context()
            if context:
                return context
        
        # 构建上下文
        debug("Building UI context from interface")
        screenshot_base64 = await self.interface.screenshot_base64()
        size_dict = await self.interface.size()
        size = Size(width=size_dict["width"], height=size_dict["height"])
        
        context = WebUIContext(screenshot_base64=screenshot_base64, size=size)
        
        # 计算截图缩放比例
        screenshot_scale = await self._get_screenshot_scale(context)
        
        if screenshot_scale != 1:
            debug(f"Applying screenshot scale: {screenshot_scale}")
            target_width = int(size.width)
            target_height = int(size.height)
            context.screenshot_base64 = await resize_img_base64(
                context.screenshot_base64,
                {"width": target_width, "height": target_height},
            )
        
        return context
    
    async def _get_screenshot_scale(self, context: UIContext) -> float:
        """计算截图缩放比例"""
        if self._screenshot_scale is not None:
            return self._screenshot_scale
        
        page_width = context.size.width
        assert_condition(
            page_width and page_width > 0,
            f"Invalid page width: {page_width}"
        )
        
        debug("Getting image info")
        info = await image_info_of_base64(context.screenshot_base64)
        screenshot_width = info.width
        
        assert_condition(
            screenshot_width > 0,
            f"Invalid screenshot width: {screenshot_width}"
        )
        
        self._screenshot_scale = screenshot_width / page_width
        debug(f"Screenshot scale: {self._screenshot_scale}")
        
        return self._screenshot_scale
    
    def _ensure_vl_model_warning(self) -> None:
        """确保VL模型警告只显示一次"""
        if not self._has_warned_non_vl_model:
            # 对于Web类型接口，允许非VL模型
            if self.interface.interface_type in (
                "puppeteer", "playwright", "static", 
                "chrome-extension-proxy", "page-over-chrome-extension-bridge"
            ):
                return
            
            self.model_config_manager.throw_error_if_non_vl_model()
            self._has_warned_non_vl_model = True
    
    async def ai_tap(
        self,
        locate_prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        AI点击操作
        
        Args:
            locate_prompt: 元素定位描述
            opt: 定位选项
        """
        assert_condition(locate_prompt, "Missing locate prompt for tap")
        
        locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("Tap", {
            "locate": locate_param.model_dump(),
        })
    
    async def ai_input(
        self,
        locate_prompt: TUserPrompt,
        value: Union[str, int],
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        AI输入操作
        
        Args:
            locate_prompt: 元素定位描述
            value: 输入值
            opt: 定位选项
        """
        assert_condition(
            isinstance(value, (str, int)),
            "Input value must be string or number"
        )
        assert_condition(locate_prompt, "Missing locate prompt for input")
        
        locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("Input", {
            "value": str(value),
            "locate": locate_param.model_dump(),
        })
    
    async def ai_hover(
        self,
        locate_prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        AI悬停操作
        
        Args:
            locate_prompt: 元素定位描述
            opt: 定位选项
        """
        assert_condition(locate_prompt, "Missing locate prompt for hover")
        
        locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("Hover", {
            "locate": locate_param.model_dump(),
        })
    
    async def ai_scroll(
        self,
        locate_prompt: Optional[TUserPrompt] = None,
        opt: Optional[ScrollParam] = None,
    ) -> Any:
        """
        AI滚动操作
        
        Args:
            locate_prompt: 元素定位描述（可选）
            opt: 滚动选项
        """
        locate_param = None
        if locate_prompt:
            locate_param = build_detailed_locate_param(locate_prompt)
        
        params: Dict[str, Any] = {}
        if locate_param:
            params["locate"] = locate_param.model_dump()
        if opt:
            params.update(opt.model_dump(exclude_none=True))
        
        return await self._call_action_in_action_space("Scroll", params)
    
    async def ai_act(
        self,
        task_prompt: str,
        cacheable: bool = True,
    ) -> Any:
        """
        AI自动操作
        
        根据任务描述自动规划并执行操作。
        
        Args:
            task_prompt: 任务描述
            cacheable: 是否缓存结果
        """
        debug(f"AI act: {task_prompt}")
        
        # TODO: 实现规划和执行逻辑
        # 这里需要调用planning模型进行操作规划，然后执行
        
        logger.info(f"Executing AI action: {task_prompt}")
        
        return None
    
    async def ai_query(
        self,
        demand: Union[str, Dict[str, str]],
        opt: Optional[ServiceExtractOption] = None,
    ) -> Any:
        """
        AI查询
        
        从页面提取数据。
        
        Args:
            demand: 数据需求描述
            opt: 提取选项
        """
        model_config = self.model_config_manager.get_model_config("insight")
        data, thought, usage = await self.service.extract(demand, model_config, opt)
        return data
    
    async def ai_assert(
        self,
        assertion: TUserPrompt,
        msg: Optional[str] = None,
        opt: Optional[ServiceExtractOption] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        AI断言
        
        验证页面状态。
        
        Args:
            assertion: 断言描述
            msg: 失败消息
            opt: 选项
        """
        model_config = self.model_config_manager.get_model_config("insight")
        
        assertion_text = assertion if isinstance(assertion, str) else assertion.prompt
        
        passed, thought, usage = await self.service.assert_condition(
            assertion_text, model_config
        )
        
        message = None if passed else f"Assertion failed: {msg or assertion_text}\nReason: {thought or '(no reason)'}"
        
        if not passed:
            raise AssertionError(message)
        
        return None
    
    async def ai_wait_for(
        self,
        assertion: TUserPrompt,
        timeout_ms: int = 15000,
        check_interval_ms: int = 3000,
    ) -> None:
        """
        AI等待条件满足
        
        Args:
            assertion: 条件描述
            timeout_ms: 超时时间（毫秒）
            check_interval_ms: 检查间隔（毫秒）
        """
        import asyncio
        
        model_config = self.model_config_manager.get_model_config("insight")
        assertion_text = assertion if isinstance(assertion, str) else assertion.prompt
        
        start_time = time.time()
        timeout_sec = timeout_ms / 1000
        interval_sec = check_interval_ms / 1000
        
        while True:
            try:
                passed, thought, usage = await self.service.assert_condition(
                    assertion_text, model_config
                )
                if passed:
                    return
            except Exception:
                pass
            
            elapsed = time.time() - start_time
            if elapsed >= timeout_sec:
                raise TimeoutError(
                    f"Timeout waiting for condition: {assertion_text}"
                )
            
            await asyncio.sleep(interval_sec)
    
    async def ai_locate(
        self,
        prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Dict[str, Any]:
        """
        AI定位元素
        
        Args:
            prompt: 元素描述
            opt: 定位选项
        """
        locate_param = build_detailed_locate_param(prompt, opt)
        model_config = self.model_config_manager.get_model_config("insight")
        
        result, usage, raw_response = await self.service.locate(
            locate_param.prompt,
            model_config,
            deep_think=locate_param.deep_think,
        )
        
        if result.element:
            return {
                "rect": result.element.rect.model_dump(),
                "center": result.element.center,
            }
        
        return {"rect": None, "center": None}
    
    async def _call_action_in_action_space(
        self,
        action_type: str,
        params: Dict[str, Any],
    ) -> Any:
        """
        调用操作空间中的操作
        
        Args:
            action_type: 操作类型
            params: 操作参数
        """
        debug(f"Calling action: {action_type} with params: {params}")
        
        # 查找匹配的操作
        action_space = self.interface.action_space()
        matched_action = None
        
        for action in action_space:
            if action.name == action_type:
                matched_action = action
                break
        
        if not matched_action:
            raise ValueError(f"Action not found: {action_type}")
        
        # 如果有locate参数，先进行定位
        locate_param = params.get("locate")
        if locate_param:
            prompt = locate_param.get("prompt", "")
            model_config = self.model_config_manager.get_model_config("insight")
            result, usage, raw_response = await self.service.locate(
                prompt, model_config
            )
            
            if result.element:
                # 将定位结果添加到参数中
                params["_element"] = result.element
                params["_rect"] = result.rect
        
        # 执行操作
        result = await matched_action.call(params, None)
        
        return result
    
    async def freeze_page_context(self) -> None:
        """冻结页面上下文"""
        debug("Freezing page context")
        context = await self.get_ui_context()
        context.is_frozen = True
        self._frozen_ui_context = context
        debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        debug("Unfreezing page context")
        self._frozen_ui_context = None
        debug("Page context unfrozen successfully")
    
    def dump_data_string(self) -> str:
        """获取dump数据字符串"""
        self.dump.group_name = self.opts.group_name
        self.dump.group_description = self.opts.group_description
        return self.dump.model_dump_json(indent=2)
    
    def write_out_action_dumps(self) -> None:
        """写出操作dump"""
        if self.destroyed:
            raise RuntimeError("Agent has been destroyed")
        
        if not self.opts.generate_report:
            return
        
        dump_dir = get_midscene_run_sub_dir("dump")
        file_name = self.opts.report_file_name or f"midscene-{int(time.time())}"
        file_path = Path(dump_dir) / f"{file_name}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.dump_data_string())
        
        self.report_file = str(file_path)
        debug(f"Wrote action dumps to {self.report_file}")
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self.destroyed:
            return
        
        await self.interface.destroy()
        self.dump = GroupedActionDump(
            sdk_version=get_version(),
            group_name=self.opts.group_name,
        )
        self.destroyed = True


def create_agent(
    interface: AbstractInterface,
    opts: Optional[AgentOpt] = None,
) -> Agent:
    """
    创建Agent
    
    Args:
        interface: 设备接口
        opts: Agent选项
        
    Returns:
        Agent实例
    """
    return Agent(interface, opts)
