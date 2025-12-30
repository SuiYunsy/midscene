"""
批量执行器

对应TypeScript源码: packages/cli/src/batch-runner.ts
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from mspy.shared.common import get_midscene_run_sub_dir
from mspy.shared.logger import get_debug
from mspy.core.yaml import parse_yaml_script, ScriptPlayer, MidsceneYamlScript

debug = get_debug('cli:batch-runner')


@dataclass
class BatchRunnerConfig:
    """批量执行器配置"""
    files: List[str] = field(default_factory=list)
    concurrent: int = 1
    continue_on_error: bool = False
    summary: str = "summary.json"
    share_browser_context: bool = False
    global_config: Optional[Dict[str, Any]] = None
    headed: bool = False
    keep_window: bool = False
    dotenv_override: bool = False
    dotenv_debug: bool = False


@dataclass
class BatchResult:
    """批量执行结果"""
    file: str
    success: bool
    executed: bool
    output: Optional[str] = None
    report: Optional[str] = None
    duration: int = 0
    result_type: str = "success"  # success, failed, partialFailed, notExecuted
    error: Optional[str] = None


class BatchRunner:
    """批量执行器
    
    负责执行多个YAML脚本
    """
    
    def __init__(self, config: BatchRunnerConfig):
        """初始化批量执行器
        
        Args:
            config: 执行器配置
        """
        self._config = config
        self._results: List[BatchResult] = []
    
    async def run(self) -> List[BatchResult]:
        """执行所有脚本
        
        Returns:
            执行结果列表
        """
        # 打印执行计划
        self._print_execution_plan()
        
        try:
            # 执行文件
            for file in self._config.files:
                result = await self._execute_file(file)
                self._results.append(result)
                
                # 检查是否需要停止
                if result.result_type == "failed" and not self._config.continue_on_error:
                    # 将剩余文件标记为未执行
                    remaining_files = self._config.files[self._config.files.index(file) + 1:]
                    for remaining_file in remaining_files:
                        self._results.append(BatchResult(
                            file=remaining_file,
                            success=False,
                            executed=False,
                            result_type="notExecuted",
                            error="前一个任务失败",
                        ))
                    break
            
            # 生成输出索引
            await self._generate_output_index()
            
        except Exception as e:
            debug(f"执行过程中发生错误: {e}")
            raise
        
        return self._results
    
    async def _execute_file(self, file: str) -> BatchResult:
        """执行单个文件
        
        Args:
            file: 文件路径
            
        Returns:
            执行结果
        """
        debug(f"执行文件: {file}")
        
        start_time = time.time()
        
        try:
            # 读取并解析脚本
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            script = parse_yaml_script(content, file)
            
            # 合并全局配置
            if self._config.global_config:
                script = self._merge_config(script, self._config.global_config)
            
            # 创建并运行播放器
            player = await self._create_player(file, script)
            await player.run()
            
            duration = int((time.time() - start_time) * 1000)
            
            # 判断结果
            if player.status == "error":
                return BatchResult(
                    file=file,
                    success=False,
                    executed=True,
                    duration=duration,
                    result_type="failed",
                    error=str(player.error_in_setup) if player.error_in_setup else "执行失败",
                    report=player.report_file,
                )
            
            # 检查是否有失败的任务
            has_failed_tasks = any(
                task.status.value == "error" for task in player.task_status_list
            )
            
            if has_failed_tasks:
                return BatchResult(
                    file=file,
                    success=False,
                    executed=True,
                    duration=duration,
                    result_type="partialFailed",
                    error="部分任务失败",
                    report=player.report_file,
                )
            
            return BatchResult(
                file=file,
                success=True,
                executed=True,
                duration=duration,
                result_type="success",
                report=player.report_file,
            )
            
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return BatchResult(
                file=file,
                success=False,
                executed=True,
                duration=duration,
                result_type="failed",
                error=str(e),
            )
    
    async def _create_player(self, file: str, script: MidsceneYamlScript) -> ScriptPlayer:
        """创建脚本播放器
        
        Args:
            file: 文件路径
            script: 解析后的脚本
            
        Returns:
            ScriptPlayer实例
        """
        async def agent_provider():
            # 根据环境配置创建Agent
            if script.web:
                return await self._create_web_agent(script)
            # TODO: 支持Android和iOS
            raise ValueError("未找到有效的环境配置")
        
        return ScriptPlayer(script, agent_provider)
    
    async def _create_web_agent(self, script: MidsceneYamlScript) -> Dict[str, Any]:
        """创建Web Agent
        
        Args:
            script: 脚本配置
            
        Returns:
            包含agent和freeFn的字典
        """
        from playwright.async_api import async_playwright
        from mspy.web.playwright import PlaywrightAgent
        
        web_env = script.web
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=not self._config.headed
        )
        
        page = await browser.new_page()
        
        if web_env and web_env.url:
            await page.goto(web_env.url)
        
        agent = PlaywrightAgent(page)
        
        async def cleanup():
            await browser.close()
            await playwright.stop()
        
        return {
            'agent': agent,
            'freeFn': [cleanup],
        }
    
    def _merge_config(self, script: MidsceneYamlScript, global_config: Dict[str, Any]) -> MidsceneYamlScript:
        """合并全局配置
        
        Args:
            script: 脚本对象
            global_config: 全局配置
            
        Returns:
            合并后的脚本对象
        """
        from mspy.core.yaml.parser import MidsceneYamlScriptWebEnv
        
        # 合并Web配置
        if 'web' in global_config and global_config['web']:
            if script.web is None:
                script.web = MidsceneYamlScriptWebEnv()
            
            web_config = global_config['web']
            if isinstance(web_config, dict):
                if 'url' in web_config and not script.web.url:
                    script.web.url = web_config['url']
                if 'headed' in web_config:
                    script.web.headed = web_config['headed']
                if 'viewport' in web_config and not script.web.viewport:
                    script.web.viewport = web_config['viewport']
        
        return script
    
    def _print_execution_plan(self) -> None:
        """打印执行计划"""
        print("   脚本:")
        for file in self._config.files:
            print(f"     - {file}")
        print("📋 执行计划")
        print(f"   并发数: {self._config.concurrent}")
        print(f"   保持窗口: {self._config.keep_window}")
        print(f"   有头模式: {self._config.headed}")
        print(f"   错误时继续: {self._config.continue_on_error}")
        print(f"   共享浏览器上下文: {self._config.share_browser_context}")
        print(f"   摘要输出: {self._config.summary}")
    
    async def _generate_output_index(self) -> None:
        """生成输出索引"""
        output_dir = get_midscene_run_sub_dir('output')
        index_path = os.path.join(output_dir, self._config.summary)
        
        try:
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            
            summary = self.get_execution_summary()
            
            index_data = {
                'summary': {
                    'total': summary['total'],
                    'successful': summary['successful'],
                    'failed': summary['failed'],
                    'partialFailed': summary['partial_failed'],
                    'notExecuted': summary['not_executed'],
                    'totalDuration': summary['total_duration'],
                    'generatedAt': time.strftime('%Y-%m-%d %H:%M:%S'),
                },
                'results': [
                    {
                        'script': result.file,
                        'success': result.success,
                        'resultType': result.result_type,
                        'output': result.output,
                        'report': result.report,
                        'error': result.error,
                        'duration': result.duration,
                    }
                    for result in self._results
                ],
            }
            
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            print("执行完成:")
            
        except Exception as e:
            print(f"生成输出索引失败: {e}")
    
    def get_execution_summary(self) -> Dict[str, int]:
        """获取执行摘要"""
        successful = sum(1 for r in self._results if r.result_type == "success")
        failed = sum(1 for r in self._results if r.result_type == "failed")
        partial_failed = sum(1 for r in self._results if r.result_type == "partialFailed")
        not_executed = sum(1 for r in self._results if r.result_type == "notExecuted")
        
        return {
            'total': len(self._results),
            'successful': successful,
            'failed': failed,
            'partial_failed': partial_failed,
            'not_executed': not_executed,
            'total_duration': sum(r.duration for r in self._results),
        }
    
    def get_failed_files(self) -> List[str]:
        """获取失败的文件列表"""
        return [r.file for r in self._results if r.result_type == "failed"]
    
    def get_partial_failed_files(self) -> List[str]:
        """获取部分失败的文件列表"""
        return [r.file for r in self._results if r.result_type == "partialFailed"]
    
    def get_not_executed_files(self) -> List[str]:
        """获取未执行的文件列表"""
        return [r.file for r in self._results if r.result_type == "notExecuted"]
    
    def get_successful_files(self) -> List[str]:
        """获取成功的文件列表"""
        return [r.file for r in self._results if r.result_type == "success"]
    
    def get_results(self) -> List[BatchResult]:
        """获取所有结果"""
        return self._results.copy()
    
    def print_execution_summary(self) -> bool:
        """打印执行摘要
        
        Returns:
            是否全部成功
        """
        summary = self.get_execution_summary()
        success = (
            summary['failed'] == 0 and
            summary['partial_failed'] == 0 and
            summary['not_executed'] == 0
        )
        
        print("\n📊 执行摘要:")
        print(f"   总文件数: {summary['total']}")
        print(f"   成功: {summary['successful']}")
        print(f"   失败: {summary['failed']}")
        print(f"   部分失败: {summary['partial_failed']}")
        print(f"   未执行: {summary['not_executed']}")
        print(f"   总耗时: {summary['total_duration'] / 1000:.2f}s")
        
        if summary['successful'] > 0:
            print("\n✅ 成功的文件:")
            for file in self.get_successful_files():
                print(f"   {file}")
        
        if summary['failed'] > 0:
            print("\n❌ 失败的文件:")
            for file in self.get_failed_files():
                print(f"   {file}")
        
        if summary['partial_failed'] > 0:
            print("\n⚠️  部分失败的文件:")
            for file in self.get_partial_failed_files():
                print(f"   {file}")
        
        if summary['not_executed'] > 0:
            print("\n⏸️ 未执行的文件:")
            for file in self.get_not_executed_files():
                print(f"   {file}")
        
        if success:
            print("\n🎉 所有文件执行成功!")
        else:
            print("\n⚠️ 部分文件失败或未执行。")
        
        return success
