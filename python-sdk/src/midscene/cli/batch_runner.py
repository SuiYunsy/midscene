"""Batch runner for executing multiple YAML scripts."""

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from midscene.shared.logger import get_logger
from midscene.shared.common import get_midscene_run_sub_dir
from midscene.core.yaml import parse_yaml_script, ScriptPlayer

logger = get_logger("cli:batch_runner")
console = Console()


@dataclass
class BatchRunnerConfig:
    """Configuration for the batch runner."""
    
    files: List[str]
    concurrent: int = 1
    continue_on_error: bool = False
    summary: str = "summary.json"
    share_browser_context: bool = False
    global_config: Dict[str, Any] = field(default_factory=dict)
    headed: bool = False
    keep_window: bool = False
    dotenv_override: bool = False
    dotenv_debug: bool = False


@dataclass
class ExecutionResult:
    """Result of executing a single file."""
    
    file: str
    success: bool
    executed: bool
    result_type: str  # 'success', 'failed', 'partialFailed', 'notExecuted'
    duration: float = 0
    error: Optional[str] = None
    output: Optional[str] = None
    report: Optional[str] = None


class BatchRunner:
    """Executes multiple YAML scripts with concurrency control."""
    
    def __init__(self, config: BatchRunnerConfig):
        """
        Initialize the batch runner.
        
        Args:
            config: Batch runner configuration
        """
        self.config = config
        self._results: List[ExecutionResult] = []
    
    async def run(self) -> List[ExecutionResult]:
        """
        Execute all configured files.
        
        Returns:
            List of execution results
        """
        self._print_execution_plan()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.concurrent)
        
        async def run_with_semaphore(file: str) -> ExecutionResult:
            async with semaphore:
                return await self._execute_file(file)
        
        # Execute files
        if self.config.continue_on_error:
            # Run all files regardless of errors
            tasks = [run_with_semaphore(f) for f in self.config.files]
            self._results = await asyncio.gather(*tasks)
        else:
            # Stop on first error
            for file in self.config.files:
                result = await self._execute_file(file)
                self._results.append(result)
                
                if result.result_type == "failed":
                    # Mark remaining as not executed
                    remaining_files = self.config.files[len(self._results):]
                    for remaining in remaining_files:
                        self._results.append(ExecutionResult(
                            file=remaining,
                            success=False,
                            executed=False,
                            result_type="notExecuted",
                            error="Previous task failed",
                        ))
                    break
        
        # Generate summary
        await self._generate_summary()
        
        return self._results
    
    async def _execute_file(self, file: str) -> ExecutionResult:
        """
        Execute a single YAML file.
        
        Args:
            file: Path to YAML file
            
        Returns:
            Execution result
        """
        console.print(f"  Running: {file}")
        start_time = time.time()
        
        try:
            # Read and parse the YAML file
            with open(file, "r") as f:
                content = f.read()
            
            script = parse_yaml_script(content, file)
            
            # Create agent factory
            async def agent_factory():
                from playwright.async_api import async_playwright
                
                p = await async_playwright().start()
                browser = await p.chromium.launch(headless=not self.config.headed)
                page = await browser.new_page()
                
                # Navigate to URL if specified
                web_config = script.web or self.config.global_config.get("web")
                if web_config and web_config.url:
                    await page.goto(web_config.url)
                    if web_config.wait_for_network_idle:
                        await page.wait_for_load_state("networkidle")
                
                from midscene.web.playwright import PlaywrightAgent
                from midscene.core.types import AgentOpt
                
                agent = PlaywrightAgent(page, AgentOpt())
                
                async def cleanup():
                    if not self.config.keep_window:
                        await browser.close()
                        await p.stop()
                
                return {"agent": agent, "free_fn": [cleanup]}
            
            # Run the script
            player = ScriptPlayer(script, agent_factory)
            await player.run()
            
            duration = time.time() - start_time
            
            # Determine result
            has_errors = any(
                task.status == "error" 
                for task in player.task_status_list
            )
            
            if player.status == "error":
                return ExecutionResult(
                    file=file,
                    success=False,
                    executed=True,
                    result_type="failed",
                    duration=duration,
                    error=str(player.error_in_setup) if player.error_in_setup else "Execution failed",
                )
            elif has_errors:
                return ExecutionResult(
                    file=file,
                    success=False,
                    executed=True,
                    result_type="partialFailed",
                    duration=duration,
                    error="Some tasks failed",
                )
            else:
                return ExecutionResult(
                    file=file,
                    success=True,
                    executed=True,
                    result_type="success",
                    duration=duration,
                )
            
        except Exception as e:
            logger.error("Error executing %s: %s", file, str(e))
            return ExecutionResult(
                file=file,
                success=False,
                executed=True,
                result_type="failed",
                duration=time.time() - start_time,
                error=str(e),
            )
    
    def _print_execution_plan(self) -> None:
        """Print the execution plan."""
        console.print("   Scripts:")
        for file in self.config.files:
            console.print(f"     - {file}")
        console.print("📋 Execution plan")
        console.print(f"   Concurrency: {self.config.concurrent}")
        console.print(f"   Keep window: {self.config.keep_window}")
        console.print(f"   Headed: {self.config.headed}")
        console.print(f"   Continue on error: {self.config.continue_on_error}")
        console.print(f"   Summary output: {self.config.summary}")
    
    async def _generate_summary(self) -> None:
        """Generate the execution summary file."""
        output_dir = Path(get_midscene_run_sub_dir("output"))
        summary_path = output_dir / self.config.summary
        
        summary_data = {
            "summary": {
                "total": len(self._results),
                "successful": sum(1 for r in self._results if r.result_type == "success"),
                "failed": sum(1 for r in self._results if r.result_type == "failed"),
                "partialFailed": sum(1 for r in self._results if r.result_type == "partialFailed"),
                "notExecuted": sum(1 for r in self._results if r.result_type == "notExecuted"),
                "totalDuration": sum(r.duration for r in self._results),
            },
            "results": [
                {
                    "script": r.file,
                    "success": r.success,
                    "resultType": r.result_type,
                    "duration": r.duration,
                    "error": r.error,
                }
                for r in self._results
            ],
        }
        
        with open(summary_path, "w") as f:
            json.dump(summary_data, f, indent=2)
        
        console.print(f"Execution finished. Summary: {summary_path}")
    
    def print_execution_summary(self) -> bool:
        """
        Print the execution summary.
        
        Returns:
            True if all executions were successful
        """
        successful = sum(1 for r in self._results if r.result_type == "success")
        failed = sum(1 for r in self._results if r.result_type == "failed")
        partial_failed = sum(1 for r in self._results if r.result_type == "partialFailed")
        not_executed = sum(1 for r in self._results if r.result_type == "notExecuted")
        total_duration = sum(r.duration for r in self._results)
        
        console.print("\n📊 Execution Summary:")
        console.print(f"   Total files: {len(self._results)}")
        console.print(f"   Successful: {successful}")
        console.print(f"   Failed: {failed}")
        console.print(f"   Partial failed: {partial_failed}")
        console.print(f"   Not executed: {not_executed}")
        console.print(f"   Duration: {total_duration:.2f}s")
        
        if successful > 0:
            console.print("\n✅ Successful files:")
            for r in self._results:
                if r.result_type == "success":
                    console.print(f"   {r.file}")
        
        if failed > 0:
            console.print("\n❌ Failed files:")
            for r in self._results:
                if r.result_type == "failed":
                    console.print(f"   {r.file}")
        
        if partial_failed > 0:
            console.print("\n⚠️  Partial failed files:")
            for r in self._results:
                if r.result_type == "partialFailed":
                    console.print(f"   {r.file}")
        
        if not_executed > 0:
            console.print("\n⏸️ Not executed files:")
            for r in self._results:
                if r.result_type == "notExecuted":
                    console.print(f"   {r.file}")
        
        success = failed == 0 and partial_failed == 0 and not_executed == 0
        
        if success:
            console.print("\n🎉 All files executed successfully!")
        else:
            console.print("\n⚠️ Some files failed or were not executed.")
        
        return success
    
    def get_results(self) -> List[ExecutionResult]:
        """Get the execution results."""
        return self._results.copy()
