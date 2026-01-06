"""
Web模块 - 提供Web自动化集成

对应TypeScript源码: packages/web-integration/src/
"""

from mspy.web.playwright import PlaywrightAgent, WebPage
from mspy.web.web_element import WebElementInfo, WebPageContextParser
from mspy.web.web_page import AbstractWebPage

__all__ = [
    "PlaywrightAgent",
    "WebPage",
    "WebElementInfo",
    "WebPageContextParser",
    "AbstractWebPage",
]
