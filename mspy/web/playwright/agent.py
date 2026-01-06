"""
Playwright Agent封装

对应TypeScript源码: packages/web-integration/src/playwright/index.ts
"""

from typing import Any, Optional

from mspy.core.agent import Agent, AgentOpt
from mspy.web.playwright.page import WebPage, WebPageOpt


class PlaywrightAgent(Agent):
    """Playwright Agent
    
    基于Playwright的Web自动化Agent
    
    Example:
        ```python
        from playwright.async_api import async_playwright
        from mspy.web import PlaywrightAgent
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://example.com')
            
            agent = PlaywrightAgent(page)
            await agent.ai_tap('登录按钮')
            await agent.ai_input('用户名输入框', 'test@example.com')
            
            await browser.close()
        ```
    """
    
    def __init__(
        self,
        page: Any,
        page_opts: Optional[WebPageOpt] = None,
        agent_opts: Optional[AgentOpt] = None
    ):
        """初始化PlaywrightAgent
        
        Args:
            page: Playwright Page对象
            page_opts: 页面选项
            agent_opts: Agent选项
        """
        web_page = WebPage(page, page_opts)
        super().__init__(web_page, agent_opts)
        
        self._playwright_page = page
    
    @property
    def playwright_page(self) -> Any:
        """获取原始Playwright Page对象"""
        return self._playwright_page


async def create_playwright_agent(
    page: Any,
    page_opts: Optional[WebPageOpt] = None,
    agent_opts: Optional[AgentOpt] = None
) -> PlaywrightAgent:
    """创建PlaywrightAgent
    
    Args:
        page: Playwright Page对象
        page_opts: 页面选项
        agent_opts: Agent选项
        
    Returns:
        PlaywrightAgent实例
    """
    return PlaywrightAgent(page, page_opts, agent_opts)
