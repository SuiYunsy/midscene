"""Agent模块 - 主入口"""
import time
import json
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, TYPE_CHECKING
from .types import UIContext, ActionResult, ExecutionDump, Size
from .executor import TaskExecutor
from ..shared.config import Config, get_config
from ..shared.logger import get_logger
from ..shared.utils import create_image_base64_from_bytes

if TYPE_CHECKING:
    from ..web.interface import AbstractInterface

logger = get_logger("agent")

class Agent:
    """
    Midscene Agent - 仅支持aiAct自动规划
    """
    def __init__(
        self,
        interface: "AbstractInterface",
        config: Optional[Config] = None,
        ai_act_context: Optional[str] = None,
        report_dir: Optional[str] = None,
    ):
        self.interface = interface
        self.config = config or get_config()
        self.ai_act_context = ai_act_context
        self.report_dir = report_dir or "./midscene_run/report"
        self._screenshots: List[Dict[str, Any]] = []
        self._execution_dumps: List[ExecutionDump] = []
        # 初始化任务执行器
        self.executor = TaskExecutor(
            get_context=self._get_ui_context,
            action_handlers=self._build_action_handlers(),
            config=self.config,
        )
    async def _get_ui_context(self) -> UIContext:
        """获取当前UI上下文"""
        screenshot = await self.interface.screenshot_base64()
        size = await self.interface.size()
        url = ""
        if hasattr(self.interface, "url"):
            url = await self.interface.url()
        return UIContext(
            screenshot_base64=screenshot,
            size=size,
            url=url,
        )
    def _build_action_handlers(self) -> Dict[str, Callable[..., Coroutine[Any, Any, Any]]]:
        """构建动作处理器映射"""
        handlers = {}
        for action in self.interface.action_space():
            handlers[action.name] = action.call
        return handlers
    async def ai_act(
        self,
        instruction: str,
        action_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行AI自动规划
        Args:
            instruction: 用户指令
            action_context: 额外的上下文信息
        Returns:
            执行结果，包含yaml_flow、usage、duration_ms、assert_results
        """
        logger.info(f"开始执行: {instruction}")
        ctx = action_context or self.ai_act_context
        start_time = time.time()
        try:
            result = await self.executor.ai_act(instruction, action_context=ctx)
            # 记录截图
            await self._capture_screenshot(f"完成: {instruction}")
            logger.info(f"执行完成，耗时: {result.get('duration_ms', 0)}ms")
            return result
        except Exception as e:
            logger.error(f"执行失败: {e}")
            await self._capture_screenshot(f"失败: {instruction}")
            raise
    async def _capture_screenshot(self, title: str) -> None:
        """捕获截图"""
        try:
            screenshot = await self.interface.screenshot_base64()
            self._screenshots.append({
                "title": title,
                "timestamp": int(time.time() * 1000),
                "screenshot": screenshot,
            })
        except Exception as e:
            logger.warning(f"截图失败: {e}")
    async def save_report(self, filename: Optional[str] = None) -> str:
        """保存报告（简化版，仅保存截图）"""
        report_path = Path(self.report_dir)
        report_path.mkdir(parents=True, exist_ok=True)
        if not filename:
            filename = f"report_{int(time.time() * 1000)}.json"
        filepath = report_path / filename
        report_data = {
            "generated_at": int(time.time() * 1000),
            "screenshots": self._screenshots,
            "total_screenshots": len(self._screenshots),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存: {filepath}")
        return str(filepath)
    async def destroy(self) -> None:
        """销毁Agent，释放资源"""
        try:
            await self.interface.destroy()
        except Exception as e:
            logger.warning(f"销毁接口时出错: {e}")
