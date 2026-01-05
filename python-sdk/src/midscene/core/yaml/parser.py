"""YAML script parser."""

from typing import Any, Dict, List, Optional, Union
import yaml

from pydantic import BaseModel


class MidsceneYamlFlowItem(BaseModel):
    """A flow item in a YAML script."""
    
    ai_tap: Optional[str] = None
    ai_hover: Optional[str] = None
    ai_input: Optional[Dict[str, str]] = None
    ai_keyboard_press: Optional[str] = None
    ai_scroll: Optional[Dict[str, Any]] = None
    ai_assert: Optional[str] = None
    ai_wait_for: Optional[str] = None
    ai_query: Optional[Union[str, Dict[str, str]]] = None
    sleep: Optional[int] = None


class MidsceneYamlTask(BaseModel):
    """A task in a YAML script."""
    
    name: str
    flow: List[Dict[str, Any]] = []
    continue_on_error: bool = False


class MidsceneYamlWebEnv(BaseModel):
    """Web environment configuration."""
    
    url: Optional[str] = None
    viewport: Optional[Dict[str, int]] = None
    headless: bool = True
    wait_for_network_idle: bool = True
    user_agent: Optional[str] = None


class MidsceneYamlScript(BaseModel):
    """A complete YAML script."""
    
    tasks: List[MidsceneYamlTask] = []
    web: Optional[MidsceneYamlWebEnv] = None
    output: Optional[str] = None
    cache: Optional[Dict[str, Any]] = None


def parse_yaml_script(
    content: str,
    source: str = "yaml",
) -> MidsceneYamlScript:
    """
    Parse a YAML script string into a MidsceneYamlScript.
    
    Args:
        content: YAML content string
        source: Source identifier for error messages
        
    Returns:
        Parsed script object
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {source}: {e}")
    
    if not isinstance(data, dict):
        raise ValueError(f"YAML must be a dictionary, got {type(data)}")
    
    # Parse tasks
    tasks = []
    for task_data in data.get("tasks", []):
        if isinstance(task_data, dict):
            tasks.append(MidsceneYamlTask(
                name=task_data.get("name", "Unnamed Task"),
                flow=task_data.get("flow", []),
                continue_on_error=task_data.get("continueOnError", False),
            ))
    
    # Parse web environment
    web = None
    web_data = data.get("web") or data.get("target")
    if web_data:
        web = MidsceneYamlWebEnv(
            url=web_data.get("url"),
            viewport=web_data.get("viewport"),
            headless=web_data.get("headless", True),
            wait_for_network_idle=web_data.get("waitForNetworkIdle", True),
            user_agent=web_data.get("userAgent"),
        )
    
    return MidsceneYamlScript(
        tasks=tasks,
        web=web,
        output=data.get("output"),
        cache=data.get("cache"),
    )
