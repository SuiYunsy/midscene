"""
批量运行器

支持并发执行多个YAML脚本。
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from playwright.async_api import async_playwright, Browser

from mspy.cli.yaml_player import create_yaml_player
from mspy.core.yaml import ScriptPlayer
from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug

logger = logging.getLogger("midscene.cli")
debug = get_debug("batch-runner")


@dataclass
class BatchRunnerConfig:
    """批量运行器配置"""
    files: List[str]
    concurrent: int = 1
    continue_on_error: bool = False
    summary: str = "summary.json"
    share_browser_context: bool = False
    headed: bool = False
    keep_window: bool = False


@dataclass
class MidsceneYamlConfigResult:
    """YAML配置执行结果"""
    file: str
    success: bool
    executed: bool
    output: Optional[str]
    report: Optional[str]
    duration: int
    result_type: str  # success, failed, partialFailed, notExecuted
    error: Optional[str]


class BatchRunner:
    """
    批量运行器
    
    支持并发执行多个YAML脚本。
    """
    
    def __init__(self, config: BatchRunnerConfig):
        """
        初始化批量运行器
        
        Args:
            config: 运行配置
        """
        self.config = config
        self.results: List[MidsceneYamlConfigResult] = []
    
    async def run(self) -> List[MidsceneYamlConfigResult]:
        """
        运行所有脚本
        
        Returns:
            执行结果列表
        """
        self._print_execution_plan()
        
        browser: Optional[Browser] = None
        
        try:
            # 如果共享浏览器上下文，先启动浏览器
            if self.config.share_browser_context:
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=not self.config.headed)
            
            # 创建任务
            semaphore = asyncio.Semaphore(self.config.concurrent)
            
            async def run_file(file: str) -> MidsceneYamlConfigResult:
                async with semaphore:
                    return await self._execute_file(file, browser)
            
            if self.config.continue_on_error:
                # 并发执行所有任务
                tasks = [run_file(file) for file in self.config.files]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.results.append(MidsceneYamlConfigResult(
                            file=self.config.files[i],
                            success=False,
                            executed=True,
                            output=None,
                            report=None,
                            duration=0,
                            result_type="failed",
                            error=str(result),
                        ))
                    else:
                        self.results.append(result)
            else:
                # 顺序执行，遇到错误停止
                for file in self.config.files:
                    result = await self._execute_file(file, browser)
                    self.results.append(result)
                    
                    if not result.success:
                        # 标记剩余文件为未执行
                        remaining_files = self.config.files[self.config.files.index(file) + 1:]
                        for remaining in remaining_files:
                            self.results.append(MidsceneYamlConfigResult(
                                file=remaining,
                                success=False,
                                executed=False,
                                output=None,
                                report=None,
                                duration=0,
                                result_type="notExecuted",
                                error="Not executed (previous task failed)",
                            ))
                        break
        
        finally:
            if browser and not self.config.keep_window:
                await browser.close()
            
            await self._generate_output_index()
        
        return self.results
    
    async def _execute_file(
        self,
        file: str,
        browser: Optional[Browser] = None,
    ) -> MidsceneYamlConfigResult:
        """执行单个文件"""
        start_time = time.time()
        
        try:
            print(f"  执行: {file}")
            
            player = await create_yaml_player(
                file,
                options={
                    "headed": self.config.headed,
                    "keep_window": self.config.keep_window,
                    "browser": browser,
                },
            )
            
            await player.run()
            
            duration = int((time.time() - start_time) * 1000)
            
            # 检查结果
            has_failed_tasks = any(
                task.status == "error"
                for task in player.task_status_list
            )
            has_player_error = player.status == "error"
            
            if has_player_error:
                success = False
                result_type = "failed"
            elif has_failed_tasks:
                success = False
                result_type = "partialFailed"
            else:
                success = True
                result_type = "success"
            
            error_msg = None
            if player.error_in_setup:
                error_msg = str(player.error_in_setup)
            elif has_player_error:
                error_msg = "Execution failed"
            elif has_failed_tasks:
                error_msg = "Some tasks failed"
            
            return MidsceneYamlConfigResult(
                file=file,
                success=success,
                executed=True,
                output=player.output,
                report=player.report_file,
                duration=duration,
                result_type=result_type,
                error=error_msg,
            )
        
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            logger.error(f"Error executing {file}: {e}")
            
            return MidsceneYamlConfigResult(
                file=file,
                success=False,
                executed=True,
                output=None,
                report=None,
                duration=duration,
                result_type="failed",
                error=str(e),
            )
    
    def _print_execution_plan(self) -> None:
        """打印执行计划"""
        print("📋 执行计划")
        print(f"   脚本:")
        for file in self.config.files:
            print(f"     - {file}")
        print(f"   并发数: {self.config.concurrent}")
        print(f"   保持窗口: {self.config.keep_window}")
        print(f"   有头模式: {self.config.headed}")
        print(f"   出错继续: {self.config.continue_on_error}")
        print(f"   摘要输出: {self.config.summary}")
    
    async def _generate_output_index(self) -> None:
        """生成输出索引"""
        output_dir = get_midscene_run_sub_dir("output")
        index_path = Path(output_dir) / self.config.summary
        
        try:
            index_data = {
                "summary": self.get_execution_summary(),
                "results": [
                    {
                        "script": result.file,
                        "success": result.success,
                        "resultType": result.result_type,
                        "output": result.output,
                        "report": result.report,
                        "error": result.error,
                        "duration": result.duration,
                    }
                    for result in self.results
                ],
            }
            
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            print(f"执行完成: {index_path}")
        
        except Exception as e:
            logger.error(f"Failed to generate output index: {e}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        successful = len([r for r in self.results if r.result_type == "success"])
        failed = len([r for r in self.results if r.result_type == "failed"])
        partial_failed = len([r for r in self.results if r.result_type == "partialFailed"])
        not_executed = len([r for r in self.results if r.result_type == "notExecuted"])
        total_duration = sum(r.duration for r in self.results)
        
        return {
            "total": len(self.results),
            "successful": successful,
            "failed": failed,
            "partialFailed": partial_failed,
            "notExecuted": not_executed,
            "totalDuration": total_duration,
            "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    def print_execution_summary(self) -> bool:
        """打印执行摘要，返回是否全部成功"""
        summary = self.get_execution_summary()
        
        success = (
            summary["failed"] == 0 and
            summary["partialFailed"] == 0 and
            summary["notExecuted"] == 0
        )
        
        print("\n📊 执行摘要:")
        print(f"   总数: {summary['total']}")
        print(f"   成功: {summary['successful']}")
        print(f"   失败: {summary['failed']}")
        print(f"   部分失败: {summary['partialFailed']}")
        print(f"   未执行: {summary['notExecuted']}")
        print(f"   耗时: {summary['totalDuration'] / 1000:.2f}s")
        
        if summary["successful"] > 0:
            print("\n✅ 成功的文件:")
            for result in self.results:
                if result.result_type == "success":
                    print(f"   {result.file}")
        
        if summary["failed"] > 0:
            print("\n❌ 失败的文件:")
            for result in self.results:
                if result.result_type == "failed":
                    print(f"   {result.file}: {result.error}")
        
        if summary["partialFailed"] > 0:
            print("\n⚠️ 部分失败的文件:")
            for result in self.results:
                if result.result_type == "partialFailed":
                    print(f"   {result.file}")
        
        if summary["notExecuted"] > 0:
            print("\n⏸️ 未执行的文件:")
            for result in self.results:
                if result.result_type == "notExecuted":
                    print(f"   {result.file}")
        
        if success:
            print("\n🎉 所有文件执行成功!")
        else:
            print("\n⚠️ 部分文件执行失败或未执行。")
        
        return success
