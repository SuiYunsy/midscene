# -*- coding: utf-8 -*-
"""
mspy - Python implementation of Midscene
一个基于 AI 的 UI 自动化测试框架。
"""

from mspy.shared import (
    uuid,
    assert_condition,
    get_debug,
    global_config_manager,
    global_model_config_manager,
    get_preferred_language,
)
from mspy.core import (
    Agent,
    AgentOpt,
    Service,
    call_ai,
)
from mspy.core.yaml import (
    parse_yaml_script,
    ScriptPlayer,
)
from mspy.web import (
    PlaywrightPage,
    PlaywrightAgent,
    create_playwright_agent,
)

__version__ = "1.0.0"

__all__ = [
    # 版本
    "__version__",
    # shared
    "uuid",
    "assert_condition",
    "get_debug",
    "global_config_manager",
    "global_model_config_manager",
    "get_preferred_language",
    # core
    "Agent",
    "AgentOpt",
    "Service",
    "call_ai",
    # yaml
    "parse_yaml_script",
    "ScriptPlayer",
    # web
    "PlaywrightPage",
    "PlaywrightAgent",
    "create_playwright_agent",
]
