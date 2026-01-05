"""Configuration factory for CLI."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from midscene.cli.batch_runner import BatchRunnerConfig


async def create_config(
    config_file: str,
    options: Dict[str, Any],
) -> BatchRunnerConfig:
    """
    Create a BatchRunnerConfig from a configuration file.
    
    Args:
        config_file: Path to configuration file
        options: CLI options to merge
        
    Returns:
        BatchRunnerConfig
    """
    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)
    
    # Get files from config
    files = config_data.get("files", [])
    if isinstance(files, str):
        files = [files]
    
    # Convert relative paths to absolute
    config_dir = Path(config_file).parent
    files = [
        str((config_dir / f).resolve()) if not os.path.isabs(f) else f
        for f in files
    ]
    
    # Merge global config
    global_config = {}
    if "web" in config_data or "target" in config_data:
        global_config["web"] = config_data.get("web") or config_data.get("target")
    
    return BatchRunnerConfig(
        files=files,
        concurrent=options.get("concurrent", config_data.get("concurrent", 1)),
        continue_on_error=options.get("continue_on_error", config_data.get("continueOnError", False)),
        summary=options.get("summary", config_data.get("summary", "summary.json")),
        share_browser_context=config_data.get("shareBrowserContext", False),
        global_config=global_config,
        headed=options.get("headed", config_data.get("headed", False)),
        keep_window=options.get("keep_window", config_data.get("keepWindow", False)),
        dotenv_override=config_data.get("dotenvOverride", False),
        dotenv_debug=config_data.get("dotenvDebug", False),
    )


async def create_files_config(
    files: List[str],
    options: Dict[str, Any],
) -> BatchRunnerConfig:
    """
    Create a BatchRunnerConfig from a list of files.
    
    Args:
        files: List of YAML file paths
        options: CLI options
        
    Returns:
        BatchRunnerConfig
    """
    return BatchRunnerConfig(
        files=files,
        concurrent=options.get("concurrent", 1),
        continue_on_error=options.get("continue_on_error", False),
        summary=options.get("summary", "summary.json"),
        share_browser_context=False,
        global_config={},
        headed=options.get("headed", False),
        keep_window=options.get("keep_window", False),
        dotenv_override=False,
        dotenv_debug=False,
    )
