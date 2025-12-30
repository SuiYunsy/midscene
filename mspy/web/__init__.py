"""
Midscene Python - Web Module
Web 模块：提供 Playwright 集成
"""

from .playwright_page import PlaywrightWebPage
from .playwright_agent import PlaywrightAgent

__all__ = [
    "PlaywrightWebPage",
    "PlaywrightAgent",
]
