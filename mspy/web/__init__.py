"""
Web 模块 - Playwright 集成
Web module - Playwright integration
"""
from .playwright_page import (
    PlaywrightWebPage,
    DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
    DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
)

__all__ = [
    "PlaywrightWebPage",
    "DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT",
    "DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT",
]
