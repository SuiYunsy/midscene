"""
Environment loader utility

Provides utility functions for loading .env files.
"""

import os
from pathlib import Path
from typing import Optional


def load_dotenv(
    env_file: Optional[str] = None,
    override: bool = False
) -> bool:
    """Load environment variables from .env file
    
    Args:
        env_file: Path to .env file. If None, searches for .env in current directory
        override: If True, override existing environment variables
        
    Returns:
        True if .env file was loaded successfully
    """
    try:
        from dotenv import load_dotenv as _load_dotenv
        
        if env_file:
            env_path = Path(env_file)
        else:
            # Search for .env in current directory and parent directories
            current = Path.cwd()
            env_path = None
            
            for parent in [current] + list(current.parents):
                candidate = parent / '.env'
                if candidate.exists():
                    env_path = candidate
                    break
        
        if env_path and env_path.exists():
            _load_dotenv(env_path, override=override)
            return True
        
        return False
        
    except ImportError:
        # python-dotenv not installed, try manual loading
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = Path.cwd() / '.env'
        
        if env_path.exists():
            _load_env_file_manual(env_path, override)
            return True
        
        return False


def _load_env_file_manual(path: Path, override: bool = False) -> None:
    """Manually load .env file without python-dotenv
    
    Args:
        path: Path to .env file
        override: If True, override existing environment variables
    """
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                
                # Remove quotes
                if value and value[0] in ('"', "'") and value[-1] == value[0]:
                    value = value[1:-1]
                
                # Set environment variable
                if override or key not in os.environ:
                    os.environ[key] = value


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable value
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    """Get required environment variable
    
    Args:
        key: Environment variable name
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If environment variable is not set
    """
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return os.environ.get('MIDSCENE_DEBUG_MODE', '').lower() in ('true', '1', 'yes')


def is_cache_enabled() -> bool:
    """Check if cache is enabled"""
    return os.environ.get('MIDSCENE_CACHE', '').lower() in ('true', '1', 'yes')
