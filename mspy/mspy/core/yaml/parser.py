"""
YAML脚本解析器
"""

import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict


class MidsceneYamlTask(BaseModel):
    """YAML任务定义"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    name: str
    flow: Optional[List[Dict[str, Any]]] = None
    continue_on_error: bool = Field(default=False, alias="continueOnError")


class MidsceneYamlScriptWebEnv(BaseModel):
    """Web环境配置"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    url: Optional[str] = None
    user_agent: Optional[str] = Field(default=None, alias="userAgent")
    viewport_width: Optional[int] = Field(default=None, alias="viewportWidth")
    viewport_height: Optional[int] = Field(default=None, alias="viewportHeight")
    viewport_scale: Optional[float] = Field(default=None, alias="viewportScale")
    wait_for_network_idle: bool = Field(default=True, alias="waitForNetworkIdle")
    cookie: Optional[str] = None
    headless: bool = True
    output: Optional[str] = None


class MidsceneYamlScriptAgentOpt(BaseModel):
    """Agent选项"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    test_id: Optional[str] = Field(default=None, alias="testId")
    cache: Optional[Any] = None
    ai_act_context: Optional[str] = Field(default=None, alias="aiActContext")


class MidsceneYamlScript(BaseModel):
    """YAML脚本定义"""
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    web: Optional[MidsceneYamlScriptWebEnv] = None
    target: Optional[MidsceneYamlScriptWebEnv] = None  # 兼容旧配置
    tasks: List[MidsceneYamlTask] = []
    agent: Optional[MidsceneYamlScriptAgentOpt] = None


def parse_yaml_script(content: str, source: str = "yaml") -> MidsceneYamlScript:
    """
    解析YAML脚本
    
    Args:
        content: YAML内容字符串
        source: 来源标识
        
    Returns:
        解析后的脚本对象
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML from {source}: {e}")
    
    if not isinstance(data, dict):
        raise ValueError(f"YAML content must be a dict, got {type(data)}")
    
    # 处理tasks
    tasks_data = data.get("tasks", [])
    tasks = []
    for task_data in tasks_data:
        if isinstance(task_data, dict):
            tasks.append(MidsceneYamlTask(**task_data))
    
    # 处理web配置
    web_data = data.get("web") or data.get("target")
    web = MidsceneYamlScriptWebEnv(**web_data) if web_data else None
    
    # 处理agent配置
    agent_data = data.get("agent")
    agent = MidsceneYamlScriptAgentOpt(**agent_data) if agent_data else None
    
    return MidsceneYamlScript(
        web=web,
        target=data.get("target"),
        tasks=tasks,
        agent=agent,
    )
