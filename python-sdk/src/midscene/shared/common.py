"""Common path utilities for Midscene."""

import os
import tempfile
from pathlib import Path
from typing import Literal, Optional

from midscene.shared.env import get_basic_env_value, MIDSCENE_RUN_DIR

DEFAULT_RUN_DIR_NAME = "midscene_run"

# Subdirectory types
SubDirType = Literal["dump", "cache", "report", "tmp", "log", "output"]


def get_midscene_run_dir() -> str:
    """
    Get the midscene run directory name from environment or default.
    
    Returns:
        The run directory name
    """
    return get_basic_env_value(MIDSCENE_RUN_DIR) or DEFAULT_RUN_DIR_NAME


def get_midscene_run_base_dir() -> str:
    """
    Get the base path to the midscene run directory.
    Creates the directory if it doesn't exist.
    
    Returns:
        Absolute path to the run directory
    """
    run_dir = get_midscene_run_dir()
    base_path = Path.cwd() / run_dir
    
    # Create directory if it doesn't exist
    if not base_path.exists():
        try:
            base_path.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Fallback to temp directory
            base_path = Path(tempfile.gettempdir()) / DEFAULT_RUN_DIR_NAME
            base_path.mkdir(parents=True, exist_ok=True)
    
    return str(base_path)


def get_midscene_run_sub_dir(subdir: SubDirType) -> str:
    """
    Get the path to a subdirectory within the midscene run directory.
    Creates the directory if it doesn't exist.
    
    Args:
        subdir: The subdirectory name ('dump', 'cache', 'report', 'tmp', 'log', 'output')
        
    Returns:
        Absolute path to the subdirectory
    """
    base_path = Path(get_midscene_run_base_dir())
    sub_path = base_path / subdir
    
    if not sub_path.exists():
        sub_path.mkdir(parents=True, exist_ok=True)
    
    return str(sub_path)


# Error code constants
ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED = "NOT_IMPLEMENTED_AS_DESIGNED"
