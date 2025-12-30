# -*- coding: utf-8 -*-
"""
Playwright Agent 封装
提供基于 Playwright 的 AI Agent。
"""

from typing import Any, Dict, Optional

from playwright.async_api import Page as PlaywrightPageType, Browser

from mspy.core.agent import Agent, AgentOpt
from .page import PlaywrightPage


class PlaywrightAgent(Agent):
    """
    Playwright Agent
    封装了 Playwright 页面的 AI Agent
    """
    
    def __init__(
        self,
        page: PlaywrightPageType,
        opts: Optional[AgentOpt] = None,
        headless: bool = True
    ):
        """
        初始化 Playwright Agent
        
        Args:
            page: Playwright Page 对象
            opts: Agent 配置选项
            headless: 是否为无头模式
        """
        playwright_page = PlaywrightPage(page, headless)
        super().__init__(playwright_page, opts)
        self._playwright_page = playwright_page
    
    @property
    def page(self) -> PlaywrightPageType:
        """获取原始 Playwright Page 对象"""
        return self._playwright_page.page
    
    async def navigate(self, url: str) -> None:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
        """
        await self._playwright_page.navigate(url)
    
    async def reload(self) -> None:
        """重新加载页面"""
        await self._playwright_page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        await self._playwright_page.go_back()
    
    async def go_forward(self) -> None:
        """前进到下一页"""
        await self._playwright_page.go_forward()
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行 JavaScript
        
        Args:
            script: JavaScript 代码
            
        Returns:
            执行结果
        """
        return await self._playwright_page.evaluate_javascript(script)


def create_playwright_agent(
    page: PlaywrightPageType,
    opts: Optional[AgentOpt] = None,
    headless: bool = True
) -> PlaywrightAgent:
    """
    创建 Playwright Agent
    
    Args:
        page: Playwright Page 对象
        opts: Agent 配置选项
        headless: 是否为无头模式
        
    Returns:
        PlaywrightAgent 实例
    """
    return PlaywrightAgent(page, opts, headless)


async def launch_playwright_agent(
    url: str,
    opts: Optional[AgentOpt] = None,
    headless: bool = True
) -> PlaywrightAgent:
    """
    启动 Playwright Agent 并导航到指定 URL
    
    Args:
        url: 目标 URL
        opts: Agent 配置选项
        headless: 是否为无头模式
        
    Returns:
        PlaywrightAgent 实例
    """
    from playwright.async_api import async_playwright
    
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    page = await browser.new_page()
    await page.goto(url)
    
    agent = PlaywrightAgent(page, opts, headless)
    # 保存引用以便后续清理
    agent._browser = browser
    agent._playwright = pw
    
    return agent
