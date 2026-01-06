"""
批量运行器

从 packages/cli/src/batch-runner.ts 迁移
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mspy.cli.config import BatchRunnerConfig
from mspy.core.yaml import parse_yaml_script, ScriptPlayer
from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug


_debug = get_debug("cli:batch-runner")


@dataclass
class ExecutionResult:
    """执行结果"""
    file: str
    success: bool
    executed: bool
    output: Optional[str] = None
    report: Optional[str] = None
    duration: int = 0
    result_type: str = "success"  # success | failed | partialFailed | notExecuted
    error: Optional[str] = None


class BatchRunner:
    """
    批量运行器
    
    负责批量执行YAML脚本文件
    """
    
    def __init__(self, config: BatchRunnerConfig):
        self.config = config
        self.results: List[ExecutionResult] = []
    
    async def run(self) -> List[ExecutionResult]:
        """运行所有脚本"""
        # 打印执行计划
        self._print_execution_plan()
        
        # 执行文件
        for file in self.config.files:
            result = await self._execute_file(file)
            self.results.append(result)
            
            # 如果不是继续执行模式且有失败，停止执行
            if not self.config.continue_on_error and not result.success:
                # 标记剩余文件为未执行
                remaining_files = self.config.files[self.config.files.index(file) + 1:]
                for remaining_file in remaining_files:
                    self.results.append(ExecutionResult(
                        file=remaining_file,
                        success=False,
                        executed=False,
                        result_type="notExecuted",
                        error="Not executed (previous task failed)",
                    ))
                break
        
        # 生成输出索引
        await self._generate_output_index()
        
        return self.results
    
    async def _execute_file(self, file: str) -> ExecutionResult:
        """执行单个文件"""
        print(f"\n执行: {file}")
        start_time = time.time()
        
        try:
            # 读取并解析YAML
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            
            script = parse_yaml_script(content)
            
            # 创建播放器
            player = ScriptPlayer(script, file)
            
            # 设置配置
            if self.config.headed:
                player.headed = True
            
            # 运行
            await player.run()
            
            duration = int((time.time() - start_time) * 1000)
            
            # 检查状态
            has_failed_tasks = any(
                task.status == "error"
                for task in player.task_status_list
            )
            has_player_error = player.status == "error"
            
            if has_player_error:
                return ExecutionResult(
                    file=file,
                    success=False,
                    executed=True,
                    duration=duration,
                    result_type="failed",
                    error=str(player.error_in_setup) if player.error_in_setup else "Execution failed",
                    report=player.report_file,
                )
            elif has_failed_tasks:
                return ExecutionResult(
                    file=file,
                    success=False,
                    executed=True,
                    duration=duration,
                    result_type="partialFailed",
                    error="Some tasks failed",
                    report=player.report_file,
                )
            else:
                return ExecutionResult(
                    file=file,
                    success=True,
                    executed=True,
                    duration=duration,
                    result_type="success",
                    report=player.report_file,
                )
                
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                file=file,
                success=False,
                executed=True,
                duration=duration,
                result_type="failed",
                error=str(e),
            )
    
    def _print_execution_plan(self) -> None:
        """打印执行计划"""
        print("   脚本:")
        for file in self.config.files:
            print(f"     - {file}")
        print("📋 执行计划")
        print(f"   并发数: {self.config.concurrent}")
        print(f"   保持窗口: {self.config.keep_window}")
        print(f"   有头模式: {self.config.headed}")
        print(f"   错误时继续: {self.config.continue_on_error}")
        print(f"   摘要输出: {self.config.summary}")
    
    async def _generate_output_index(self) -> None:
        """生成输出索引"""
        try:
            output_dir = get_midscene_run_sub_dir("output")
            index_path = Path(output_dir) / self.config.summary
            
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            successful = len([r for r in self.results if r.result_type == "success"])
            failed = len([r for r in self.results if r.result_type == "failed"])
            partial_failed = len([r for r in self.results if r.result_type == "partialFailed"])
            not_executed = len([r for r in self.results if r.result_type == "notExecuted"])
            total_duration = sum(r.duration for r in self.results)
            
            index_data = {
                "summary": {
                    "total": len(self.results),
                    "successful": successful,
                    "failed": failed,
                    "partialFailed": partial_failed,
                    "notExecuted": not_executed,
                    "totalDuration": total_duration,
                    "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "results": [
                    {
                        "script": r.file,
                        "success": r.success,
                        "resultType": r.result_type,
                        "output": r.output,
                        "report": r.report,
                        "error": r.error,
                        "duration": r.duration,
                    }
                    for r in self.results
                ],
            }
            
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            print("执行完成:")
            
        except Exception as e:
            print(f"生成输出索引失败: {e}")
    
    def get_execution_summary(self) -> Dict[str, int]:
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
            "partial_failed": partial_failed,
            "not_executed": not_executed,
            "total_duration": total_duration,
        }
    
    def get_failed_files(self) -> List[str]:
        """获取失败的文件"""
        return [r.file for r in self.results if r.result_type == "failed"]
    
    def get_partial_failed_files(self) -> List[str]:
        """获取部分失败的文件"""
        return [r.file for r in self.results if r.result_type == "partialFailed"]
    
    def get_not_executed_files(self) -> List[str]:
        """获取未执行的文件"""
        return [r.file for r in self.results if r.result_type == "notExecuted"]
    
    def get_successful_files(self) -> List[str]:
        """获取成功的文件"""
        return [r.file for r in self.results if r.result_type == "success"]
    
    def print_execution_summary(self) -> bool:
        """打印执行摘要，返回是否全部成功"""
        summary = self.get_execution_summary()
        success = (
            summary["failed"] == 0 and
            summary["partial_failed"] == 0 and
            summary["not_executed"] == 0
        )
        
        print("\n📊 执行摘要:")
        print(f"   总文件数: {summary['total']}")
        print(f"   成功: {summary['successful']}")
        print(f"   失败: {summary['failed']}")
        print(f"   部分失败: {summary['partial_failed']}")
        print(f"   未执行: {summary['not_executed']}")
        print(f"   耗时: {summary['total_duration'] / 1000:.2f}s")
        print(f"   摘要: {self._get_summary_absolute_path()}")
        
        if summary["successful"] > 0:
            print("\n✅ 成功的文件:")
            for file in self.get_successful_files():
                print(f"   {file}")
        
        if summary["failed"] > 0:
            print("\n❌ 失败的文件:")
            for file in self.get_failed_files():
                print(f"   {file}")
        
        if summary["partial_failed"] > 0:
            print("\n⚠️ 部分失败的文件 (部分任务失败，continue_on_error):")
            for file in self.get_partial_failed_files():
                print(f"   {file}")
        
        if summary["not_executed"] > 0:
            print("\n⏸️ 未执行的文件:")
            for file in self.get_not_executed_files():
                print(f"   {file}")
        
        if success:
            print("\n🎉 所有文件执行成功!")
        else:
            print("\n⚠️ 部分文件失败或未执行。")
        
        return success
    
    def _get_summary_absolute_path(self) -> str:
        """获取摘要文件的绝对路径"""
        output_dir = get_midscene_run_sub_dir("output")
        return str(Path(output_dir) / self.config.summary)
