"""
Midscene Python SDK - Web Module
Web模块，包含Playwright集成
"""

from .playwright_page import (
    PlaywrightWebPage,
    WebPageOpt,
    create_playwright_page,
    close_playwright,
    DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
    DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
)

__all__ = [
    "PlaywrightWebPage",
    "WebPageOpt",
    "create_playwright_page",
    "close_playwright",
    "DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT",
    "DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT",
]
