"""Web模块 - Playwright集成"""
from .interface import AbstractInterface
from .playwright_page import PlaywrightPage
from .actions import get_web_action_space
__all__ = [
    "AbstractInterface",
    "PlaywrightPage",
    "get_web_action_space",
]
