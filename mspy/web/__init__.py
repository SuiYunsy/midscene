# -*- coding: utf-8 -*-
"""
Midscene Web Module
Web模块，提供Playwright集成
"""

from .playwright_page import PlaywrightPage
from .playwright_agent import PlaywrightAgent

__all__ = [
    'PlaywrightPage',
    'PlaywrightAgent',
]
