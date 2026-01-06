"""
Midscene Python SDK (mspy)

AI驱动的UI自动化测试框架

从TypeScript版本 (packages/core, packages/shared, packages/web-integration, packages/cli) 迁移
"""

__version__ = "0.1.0"

# 导出主要组件
from mspy.core.agent import Agent
from mspy.core.types import AgentOpt, UIContext, DeviceAction

# Web集成
from mspy.web import PlaywrightPage, PlaywrightAgent

# CLI
from mspy.cli import BatchRunner

__all__ = [
    "__version__",
    # Core
    "Agent",
    "AgentOpt",
    "UIContext",
    "DeviceAction",
    # Web
    "PlaywrightPage",
    "PlaywrightAgent",
    # CLI
    "BatchRunner",
]
