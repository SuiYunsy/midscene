"""Midscene CLI for running automation scripts."""

import click
import asyncio
import sys
from typing import Optional

from midscene.cli.batch_runner import BatchRunner, BatchRunnerConfig
from midscene.cli.config_factory import create_config, create_files_config
from midscene.cli.utils import match_yaml_files


@click.command()
@click.argument("path", required=False)
@click.option("--config", "-c", help="Configuration file path")
@click.option("--files", "-f", multiple=True, help="YAML files to execute")
@click.option("--concurrent", default=1, type=int, help="Number of concurrent executions")
@click.option("--headed", is_flag=True, help="Run browser in headed mode")
@click.option("--keep-window", is_flag=True, help="Keep browser window open after execution")
@click.option("--continue-on-error", is_flag=True, help="Continue execution on error")
@click.option("--summary", default="summary.json", help="Summary output file name")
@click.version_option(package_name="midscene")
def main(
    path: Optional[str],
    config: Optional[str],
    files: tuple,
    concurrent: int,
    headed: bool,
    keep_window: bool,
    continue_on_error: bool,
    summary: str,
) -> None:
    """
    Midscene CLI - AI-powered UI automation.
    
    Run YAML automation scripts using natural language commands.
    
    Examples:
    
        midscene script.yaml
        
        midscene ./scripts/
        
        midscene --config config.yaml
        
        midscene --files script1.yaml --files script2.yaml
    """
    from midscene import __version__
    
    click.echo(f"\nWelcome to @midscene/cli v{__version__}\n")
    
    asyncio.run(_run(
        path=path,
        config_file=config,
        files=list(files),
        concurrent=concurrent,
        headed=headed,
        keep_window=keep_window,
        continue_on_error=continue_on_error,
        summary=summary,
    ))


async def _run(
    path: Optional[str],
    config_file: Optional[str],
    files: list,
    concurrent: int,
    headed: bool,
    keep_window: bool,
    continue_on_error: bool,
    summary: str,
) -> None:
    """Run the CLI command."""
    
    config_options = {
        "concurrent": concurrent,
        "headed": headed,
        "keep_window": keep_window,
        "continue_on_error": continue_on_error,
        "summary": summary,
    }
    
    config = None
    
    if config_file:
        config = await create_config(config_file, config_options)
        click.echo(f"   Config file: {config_file}")
    elif files:
        click.echo("   Executing YAML files from --files argument...")
        config = await create_files_config(list(files), config_options)
    elif path:
        yaml_files = match_yaml_files(path)
        if not yaml_files:
            click.echo(f"No yaml files found in {path}", err=True)
            sys.exit(1)
        click.echo("   Executing YAML files...")
        config = await create_files_config(yaml_files, config_options)
    
    if not config:
        click.echo("No script path, files, or config provided", err=True)
        sys.exit(1)
    
    runner = BatchRunner(config)
    await runner.run()
    
    success = runner.print_execution_summary()
    
    if keep_window:
        click.echo("Browser is still running, use Ctrl+C to stop it")
        try:
            while True:
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            pass
    else:
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
