"""
Playwright集成模块

从 packages/web-integration/src/playwright/ 迁移
"""

from mspy.web.playwright.page import PlaywrightPage
from mspy.web.playwright.agent import PlaywrightAgent

__all__ = [
    "PlaywrightPage",
    "PlaywrightAgent",
]
