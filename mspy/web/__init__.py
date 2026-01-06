# -*- coding: utf-8 -*-
"""
mspy web 模块
提供 Playwright 集成，用于 Web 自动化测试。
"""

from .page import PlaywrightPage
from .agent import PlaywrightAgent, create_playwright_agent

__all__ = [
    "PlaywrightPage",
    "PlaywrightAgent",
    "create_playwright_agent",
]
