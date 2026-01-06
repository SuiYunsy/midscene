"""
Web集成模块

从 packages/web-integration/src/ 迁移
只保留Playwright集成，移除Puppeteer、Chrome扩展等
"""

from mspy.web.web_page import (
    AbstractWebPage,
    MouseAction,
    KeyboardAction,
    get_key_commands,
)
from mspy.web.playwright import (
    PlaywrightPage,
    PlaywrightAgent,
)

__all__ = [
    # 抽象类
    "AbstractWebPage",
    "MouseAction",
    "KeyboardAction",
    "get_key_commands",
    # Playwright
    "PlaywrightPage",
    "PlaywrightAgent",
]
