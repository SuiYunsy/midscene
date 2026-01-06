"""
Midscene Python SDK (mspy)

Python实现的Midscene SDK，提供基于AI的UI自动化测试能力。
包含四个主要模块：
- shared: 共享工具和类型定义
- core: 核心Agent和AI模型调用
- web: Web自动化集成（Playwright）
- cli: 命令行工具
"""

__version__ = "0.1.0"

from mspy.core import Agent, Service
from mspy.web.playwright import PlaywrightAgent

__all__ = [
    "Agent",
    "Service", 
    "PlaywrightAgent",
    "__version__",
]
