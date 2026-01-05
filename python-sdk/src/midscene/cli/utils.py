"""CLI utility functions."""

import glob
import os
from pathlib import Path
from typing import List


def match_yaml_files(path: str) -> List[str]:
    """
    Find all YAML files in a path.
    
    Args:
        path: File path or directory path
        
    Returns:
        List of YAML file paths
    """
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix in (".yaml", ".yml"):
            return [str(path_obj)]
        return []
    
    if path_obj.is_dir():
        yaml_files = []
        for ext in ("*.yaml", "*.yml"):
            yaml_files.extend(glob.glob(str(path_obj / "**" / ext), recursive=True))
        return sorted(yaml_files)
    
    # Try as glob pattern
    return sorted(glob.glob(path, recursive=True))
