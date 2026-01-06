"""
Playwright Agent - Playwright 智能体
封装 Playwright 页面的 AI 智能体
"""

from typing import Any, Dict, Optional

from playwright.async_api import Page as PlaywrightPage

from mspy.shared.logger import get_debug
from mspy.core.agent import Agent, AgentOpt, AiActOptions
from mspy.web.playwright_page import PlaywrightWebPage


debug = get_debug("playwright:agent")


class PlaywrightAgent(Agent):
    """
    Playwright 智能体
    基于 Playwright 页面的 AI 智能体实现
    """
    
    def __init__(
        self,
        page: PlaywrightPage,
        opts: Optional[AgentOpt] = None,
    ):
        """
        初始化 Playwright 智能体
        
        Args:
            page: Playwright 页面对象
            opts: Agent 配置选项
        """
        web_page = PlaywrightWebPage(page)
        super().__init__(web_page, opts)
        
        self._playwright_page = page
    
    @property
    def page(self) -> PlaywrightWebPage:
        """获取 PlaywrightWebPage 实例"""
        return self.interface
    
    @property
    def playwright_page(self) -> PlaywrightPage:
        """获取底层 Playwright 页面"""
        return self._playwright_page
    
    async def wait_for_network_idle(self, timeout: int = 1000) -> None:
        """
        等待网络空闲
        
        Args:
            timeout: 超时时间（毫秒）
        """
        await self._playwright_page.wait_for_load_state("networkidle", timeout=timeout)
    
    async def navigate(self, url: str) -> None:
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
        """
        await self.page.navigate(url)
    
    async def reload(self) -> None:
        """重新加载页面"""
        await self.page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        await self.page.go_back()
    
    async def get_url(self) -> str:
        """获取当前 URL"""
        return await self.page.url()
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行 JavaScript 代码
        
        Args:
            script: JavaScript 代码
            
        Returns:
            执行结果
        """
        return await self.page.evaluate_javascript(script)
