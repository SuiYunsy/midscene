"""YAML脚本执行器"""
import asyncio
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from .parser import parse_yaml_script, load_yaml_file, YamlScript, YamlTask
from ..core.agent import Agent
from ..web.playwright_page import PlaywrightPage, PlaywrightLauncher
from ..shared.config import Config, get_config
from ..shared.logger import get_logger
from ..shared.utils import sleep_ms

logger = get_logger("cli-runner")

class ScriptPlayer:
    """脚本播放器"""
    def __init__(
        self,
        script: YamlScript,
        config: Optional[Config] = None,
    ):
        self.script = script
        self.config = config or get_config()
        self.status = "init"
        self.results: Dict[str, Any] = {}
        self.task_status: List[Dict[str, Any]] = []
        self.error: Optional[Exception] = None
        self._launcher: Optional[PlaywrightLauncher] = None
        self._agent: Optional[Agent] = None
    async def run(self) -> Dict[str, Any]:
        """执行脚本"""
        self.status = "running"
        start_time = time.time()
        try:
            # 初始化浏览器
            await self._setup_browser()
            # 执行任务
            for idx, task in enumerate(self.script.tasks):
                task_result = await self._run_task(task, idx)
                self.task_status.append(task_result)
                if task_result["status"] == "error" and not task.continue_on_error:
                    self.status = "error"
                    break
            if self.status != "error":
                self.status = "done"
        except Exception as e:
            self.status = "error"
            self.error = e
            logger.error(f"脚本执行失败: {e}")
        finally:
            await self._cleanup()
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        return {
            "status": self.status,
            "duration_ms": duration_ms,
            "results": self.results,
            "task_status": self.task_status,
            "error": str(self.error) if self.error else None,
        }
    async def _setup_browser(self) -> None:
        """初始化浏览器"""
        web_config = self.script.web
        if not web_config:
            raise ValueError("缺少web配置")
        self._launcher = PlaywrightLauncher(
            headless=web_config.headless,
            viewport_width=web_config.viewport_width,
            viewport_height=web_config.viewport_height,
            user_data_dir=web_config.user_data_dir,
            cookies=web_config.cookies,
            local_storage=web_config.local_storage,
        )
        page = await self._launcher.launch()
        # 导航到初始URL
        if web_config.url:
            await page.goto(web_config.url)
        # 创建Agent
        ai_act_context = None
        if self.script.agent:
            ai_act_context = self.script.agent.get("aiActContext")
        self._agent = Agent(page, config=self.config, ai_act_context=ai_act_context)
    async def _cleanup(self) -> None:
        """清理资源"""
        if self._agent:
            await self._agent.destroy()
        if self._launcher:
            await self._launcher.close()
    async def _run_task(self, task: YamlTask, idx: int) -> Dict[str, Any]:
        """执行单个任务"""
        logger.info(f"执行任务 [{idx + 1}]: {task.name}")
        task_result = {
            "name": task.name,
            "index": idx,
            "status": "running",
            "error": None,
        }
        try:
            for flow_item in task.flow:
                await self._execute_flow_item(flow_item)
            task_result["status"] = "done"
        except Exception as e:
            task_result["status"] = "error"
            task_result["error"] = str(e)
            logger.error(f"任务 [{task.name}] 失败: {e}")
        return task_result
    async def _execute_flow_item(self, item: Dict[str, Any]) -> None:
        """执行单个流程项"""
        # aiAct / ai / aiAction
        if "aiAct" in item or "ai" in item or "aiAction" in item:
            prompt = item.get("aiAct") or item.get("ai") or item.get("aiAction")
            if not prompt:
                raise ValueError("aiAct需要指令")
            result = await self._agent.ai_act(prompt)
            if "name" in item:
                self.results[item["name"]] = result
            return
        # sleep
        if "sleep" in item:
            ms = item["sleep"]
            if isinstance(ms, str):
                ms = int(ms)
            logger.info(f"等待 {ms}ms")
            await sleep_ms(ms)
            return
        # 其他动作直接调用
        for action_name in ["Tap", "Navigate", "Input", "Scroll", "KeyboardPress"]:
            if action_name.lower() in item or action_name in item:
                # 简化处理 - 直接调用agent的ai_act
                prompt = str(item.get(action_name.lower()) or item.get(action_name))
                await self._agent.ai_act(prompt)
                return
        logger.warning(f"未知的流程项: {item}")

async def run_yaml_string(content: str, config: Optional[Config] = None) -> Dict[str, Any]:
    """运行YAML字符串"""
    script = parse_yaml_script(content)
    player = ScriptPlayer(script, config)
    return await player.run()

async def run_yaml_file(filepath: str, config: Optional[Config] = None) -> Dict[str, Any]:
    """运行YAML文件"""
    script = load_yaml_file(filepath)
    player = ScriptPlayer(script, config)
    return await player.run()

def main():
    """CLI入口"""
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="mspy - Midscene Python CLI")
    parser.add_argument("file", help="YAML脚本文件路径")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    args = parser.parse_args()
    # 修改配置
    if args.headed:
        script = load_yaml_file(args.file)
        if script.web:
            script.web.headless = False
    async def _run():
        result = await run_yaml_file(args.file)
        if result["status"] == "error":
            print(f"执行失败: {result['error']}")
            sys.exit(1)
        print(f"执行完成，耗时: {result['duration_ms']}ms")
    asyncio.run(_run())

if __name__ == "__main__":
    main()
