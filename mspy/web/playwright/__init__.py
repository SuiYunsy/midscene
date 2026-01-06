"""
Playwright集成模块

对应TypeScript源码: packages/web-integration/src/playwright/
"""

from mspy.web.playwright.page import WebPage
from mspy.web.playwright.agent import PlaywrightAgent

__all__ = [
    "WebPage",
    "PlaywrightAgent",
]
