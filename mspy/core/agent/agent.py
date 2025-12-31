"""
Agent主类

从 packages/core/src/agent/agent.ts 迁移
"""

import time
from typing import Any, Callable, Optional, TypeVar

from mspy.core.types import (
    AgentOpt,
    CacheConfig,
    ExecutionDump,
    GroupedActionDump,
    ServiceAction,
    UIContext,
)
from mspy.core.device import AbstractInterface
from mspy.shared.env import (
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
    ModelConfigManager,
    global_config_manager,
    global_model_config_manager,
)
from mspy.shared.img import image_info_of_base64, resize_img_base64
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

_debug = get_debug("agent")


# 默认重规划周期限制
DEFAULT_REPLANNING_CYCLE_LIMIT = 20


T = TypeVar("T")


class Agent:
    """
    AI驱动的自动化测试Agent
    
    主要功能：
    - ai_act: 执行AI驱动的动作
    - ai_query: 查询页面信息
    - ai_locate: 定位元素
    - ai_assert: 断言验证
    - ai_wait_for: 等待条件
    """
    
    def __init__(
        self,
        interface: AbstractInterface,
        opts: Optional[AgentOpt] = None
    ):
        self.interface = interface
        self.opts = opts or AgentOpt()
        
        # 设置默认值
        if not self.opts.group_name:
            self.opts.group_name = "Midscene Report"
        
        # 从环境获取重规划周期限制
        env_limit = global_config_manager.get_env_config_in_number(
            MIDSCENE_REPLANNING_CYCLE_LIMIT
        )
        if self.opts.replanning_cycle_limit is None and env_limit:
            self.opts.replanning_cycle_limit = env_limit
        
        # 模型配置管理器
        self.model_config_manager = global_model_config_manager
        
        # 初始化dump
        self.dump = self._reset_dump()
        
        # 报告文件名
        self.report_file_name = (
            opts.report_file_name if opts else None
        ) or self._get_report_file_name(
            opts.test_id if opts else None
        )
        
        # 状态标志
        self.destroyed = False
        self._frozen_ui_context: Optional[UIContext] = None
        self._screenshot_scale: Optional[float] = None
        self._has_warned_non_vl_model = False
        
        # Dump更新监听器
        self._dump_update_listeners: list[Callable[[str, Optional[ExecutionDump]], None]] = []
    
    def _get_report_file_name(self, test_id: Optional[str] = None) -> str:
        """获取报告文件名"""
        base_name = test_id or self.interface.interface_type or "web"
        timestamp = int(time.time() * 1000)
        return f"{base_name}-{timestamp}"
    
    def _reset_dump(self) -> GroupedActionDump:
        """重置dump"""
        from mspy import __version__
        
        self.dump = GroupedActionDump(
            sdk_version=__version__,
            group_name=self.opts.group_name or "Midscene Report",
            group_description=self.opts.group_description,
            executions=[],
            model_briefs=[],
        )
        return self.dump
    
    def _ensure_vl_model_warning(self) -> None:
        """确保VL模型警告只显示一次"""
        if self._has_warned_non_vl_model:
            return
        
        if self.interface.interface_type not in (
            "puppeteer", "playwright", "static",
            "chrome-extension-proxy", "page-over-chrome-extension-bridge"
        ):
            self.model_config_manager.throw_error_if_non_vl_model()
            self._has_warned_non_vl_model = True
    
    async def _get_screenshot_scale(self, context: UIContext) -> float:
        """计算截图缩放比例"""
        if self._screenshot_scale is not None:
            return self._screenshot_scale
        
        page_width = context.size.width
        assert_condition(
            page_width and page_width > 0,
            f"Invalid page width: {page_width}"
        )
        
        _debug("will get image info of base64")
        image_info = await image_info_of_base64(context.screenshot_base64)
        _debug("image info of base64 done")
        
        screenshot_width = image_info.width
        assert_condition(
            screenshot_width and screenshot_width > 0,
            f"Invalid screenshot width: {screenshot_width}"
        )
        
        computed_scale = screenshot_width / page_width
        assert_condition(
            computed_scale > 0,
            f"Invalid screenshot scale: {computed_scale}"
        )
        
        _debug(
            f"Computed screenshot scale {computed_scale} "
            f"from screenshot width {screenshot_width} and page width {page_width}"
        )
        
        self._screenshot_scale = computed_scale
        return computed_scale
    
    async def get_ui_context(
        self,
        action: Optional[ServiceAction] = None
    ) -> UIContext:
        """
        获取UI上下文
        
        Args:
            action: 服务动作类型
        
        Returns:
            UIContext实例
        """
        # 检查VL模型配置
        self._ensure_vl_model_warning()
        
        # 如果上下文被冻结，返回冻结的上下文
        if self._frozen_ui_context:
            _debug(f"Using frozen page context for action: {action}")
            return self._frozen_ui_context
        
        # 获取原始上下文
        _debug("Getting UI context")
        context = await self.interface.get_context()
        
        # 计算截图缩放
        _debug("will get screenshot scale")
        computed_scale = await self._get_screenshot_scale(context)
        _debug(f"computed screenshot scale: {computed_scale}")
        
        # 如果需要缩放截图
        if computed_scale != 1:
            _debug(
                f"Applying computed screenshot scale: {computed_scale:.4f} "
                "(resize to logical size)"
            )
            target_width = round(context.size.width)
            target_height = round(context.size.height)
            _debug(f"Resizing screenshot to {target_width}x{target_height}")
            context.screenshot_base64 = await resize_img_base64(
                context.screenshot_base64,
                {"width": target_width, "height": target_height}
            )
        else:
            _debug(f"screenshot scale={computed_scale}")
        
        return context
    
    async def freeze_page_context(self) -> None:
        """冻结当前页面上下文"""
        _debug("Freezing page context")
        context = await self.get_ui_context()
        context.is_frozen = True
        self._frozen_ui_context = context
        _debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """解冻页面上下文"""
        _debug("Unfreezing page context")
        self._frozen_ui_context = None
        _debug("Page context unfrozen successfully")
    
    def set_ai_act_context(self, prompt: str) -> None:
        """设置AI动作上下文"""
        if self.opts.ai_act_context:
            print(
                "Warning: aiActContext is already set, "
                "this call will override the previous setting"
            )
        self.opts.ai_act_context = prompt
    
    def append_execution_dump(
        self,
        execution: ExecutionDump
    ) -> None:
        """添加执行dump"""
        self.dump.executions.append(execution)
    
    def dump_data_string(self) -> str:
        """获取dump数据字符串"""
        import json
        
        # 更新dump信息
        self.dump.group_name = self.opts.group_name or ""
        self.dump.group_description = self.opts.group_description
        
        # 转换为字典
        dump_dict = {
            "sdkVersion": self.dump.sdk_version,
            "groupName": self.dump.group_name,
            "groupDescription": self.dump.group_description,
            "modelBriefs": self.dump.model_briefs,
            "executions": [
                {
                    "logTime": e.log_time,
                    "name": e.name,
                    "description": e.description,
                    "tasks": [
                        {
                            "type": t.type,
                            "status": t.status,
                            "subType": t.sub_type,
                            "param": t.param,
                            "thought": t.thought,
                            "errorMessage": t.error_message,
                        }
                        for t in e.tasks
                    ]
                }
                for e in self.dump.executions
            ]
        }
        
        return json.dumps(dump_dict, ensure_ascii=False)
    
    def add_dump_update_listener(
        self,
        listener: Callable[[str, Optional[ExecutionDump]], None]
    ) -> Callable[[], None]:
        """
        添加dump更新监听器
        
        Returns:
            移除监听器的函数
        """
        self._dump_update_listeners.append(listener)
        
        def remove():
            if listener in self._dump_update_listeners:
                self._dump_update_listeners.remove(listener)
        
        return remove
    
    async def ai_act(
        self,
        task_prompt: str,
        cacheable: bool = True
    ) -> Any:
        """
        执行AI驱动的动作
        
        Args:
            task_prompt: 任务描述
            cacheable: 是否可缓存
        
        Returns:
            执行结果
        """
        _debug(f"ai_act: {task_prompt}")
        
        model_config = self.model_config_manager.get_model_config("planning")
        
        # TODO: 实现完整的规划和执行逻辑
        # 这里只是基础框架
        
        return {"status": "ok", "prompt": task_prompt}
    
    async def ai_query(
        self,
        demand: str,
        dom_included: bool = False,
        screenshot_included: bool = True
    ) -> Any:
        """
        查询页面信息
        
        Args:
            demand: 查询需求描述
            dom_included: 是否包含DOM
            screenshot_included: 是否包含截图
        
        Returns:
            查询结果
        """
        _debug(f"ai_query: {demand}")
        
        model_config = self.model_config_manager.get_model_config("insight")
        
        # TODO: 实现完整的提取逻辑
        
        return {"status": "ok", "demand": demand}
    
    async def ai_locate(
        self,
        prompt: str,
        deep_think: bool = False
    ) -> dict[str, Any]:
        """
        定位元素
        
        Args:
            prompt: 元素描述
            deep_think: 是否深度思考
        
        Returns:
            定位结果 {"rect": Rect, "center": (x, y)}
        """
        _debug(f"ai_locate: {prompt}, deep_think={deep_think}")
        
        model_config = self.model_config_manager.get_model_config("insight")
        
        # TODO: 实现完整的定位逻辑
        
        return {"rect": None, "center": None}
    
    async def ai_assert(
        self,
        assertion: str,
        msg: Optional[str] = None,
        keep_raw_response: bool = False
    ) -> Optional[dict[str, Any]]:
        """
        断言验证
        
        Args:
            assertion: 断言描述
            msg: 失败时的自定义消息
            keep_raw_response: 是否保留原始响应
        
        Returns:
            如果keep_raw_response为True，返回结果字典
        
        Raises:
            AssertionError: 断言失败时
        """
        _debug(f"ai_assert: {assertion}")
        
        model_config = self.model_config_manager.get_model_config("insight")
        
        # TODO: 实现完整的断言逻辑
        
        if keep_raw_response:
            return {"pass": True, "thought": ""}
        
        return None
    
    async def ai_wait_for(
        self,
        assertion: str,
        timeout_ms: int = 15000,
        check_interval_ms: int = 3000
    ) -> None:
        """
        等待条件满足
        
        Args:
            assertion: 条件描述
            timeout_ms: 超时时间（毫秒）
            check_interval_ms: 检查间隔（毫秒）
        
        Raises:
            TimeoutError: 超时时
        """
        _debug(f"ai_wait_for: {assertion}, timeout={timeout_ms}ms")
        
        # TODO: 实现完整的等待逻辑
        pass
    
    async def record_to_report(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> None:
        """
        记录截图到报告
        
        Args:
            title: 截图标题
            content: 内容描述
        """
        _debug(f"record_to_report: {title}")
        
        # 截图
        base64_img = await self.interface.screenshot_base64()
        now = int(time.time() * 1000)
        
        # 构建ExecutionDump
        from mspy.core.types import ExecutionRecorderItem, ExecutionTask, ExecutionTaskTiming
        
        recorder = [
            ExecutionRecorderItem(
                type="screenshot",
                ts=now,
                screenshot=base64_img,
            )
        ]
        
        task = ExecutionTask(
            type="Log",
            sub_type="Screenshot",
            status="finished",
            recorder=recorder,
            timing=ExecutionTaskTiming(start=now, end=now, cost=0),
            param={"content": content or ""},
        )
        
        execution_dump = ExecutionDump(
            log_time=now,
            name=f"Log - {title or 'untitled'}",
            description=content,
            tasks=[task],
        )
        
        self.append_execution_dump(execution_dump)
        
        # 触发监听器
        dump_string = self.dump_data_string()
        for listener in self._dump_update_listeners:
            try:
                listener(dump_string, execution_dump)
            except Exception as e:
                print(f"Error in dump update listener: {e}")
    
    async def run_yaml(self, yaml_content: str) -> dict[str, Any]:
        """
        执行YAML脚本
        
        Args:
            yaml_content: YAML脚本内容
        
        Returns:
            执行结果
        """
        _debug("run_yaml")
        
        # TODO: 实现YAML脚本执行
        
        return {"result": {}}
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行JavaScript脚本
        
        Args:
            script: JavaScript代码
        
        Returns:
            执行结果
        
        Raises:
            NotImplementedError: 如果接口不支持
        """
        if not hasattr(self.interface, "evaluate_javascript"):
            raise NotImplementedError(
                "evaluate_javascript is not supported in current agent"
            )
        return await self.interface.evaluate_javascript(script)
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self.destroyed:
            return
        
        if hasattr(self.interface, "destroy"):
            await self.interface.destroy()
        
        self._reset_dump()
        self.destroyed = True


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
