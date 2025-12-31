"""
Midscene Web - Playwright Integration
"""

from .playwright import (
    PlaywrightPage,
    PlaywrightBrowser,
    create_playwright_page,
)

__all__ = [
    'PlaywrightPage',
    'PlaywrightBrowser',
    'create_playwright_page',
]
