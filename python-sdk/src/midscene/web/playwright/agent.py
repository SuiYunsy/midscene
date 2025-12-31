"""Playwright Agent for Midscene."""

from typing import Any, Optional

from playwright.async_api import Page

from midscene.core.agent import Agent
from midscene.core.types import AgentOpt
from midscene.web.playwright.page import PlaywrightPage


class PlaywrightAgent(Agent[PlaywrightPage]):
    """
    Agent specialized for Playwright browser automation.
    
    This is the main entry point for using Midscene with Playwright.
    
    Example:
        ```python
        from playwright.async_api import async_playwright
        from midscene.web.playwright import PlaywrightAgent
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://example.com')
            
            agent = PlaywrightAgent(page)
            await agent.ai_tap('click the submit button')
        ```
    """
    
    def __init__(
        self,
        page: Page,
        opts: Optional[AgentOpt] = None,
    ):
        """
        Initialize PlaywrightAgent.
        
        Args:
            page: Playwright Page instance
            opts: Agent options
        """
        playwright_page = PlaywrightPage(page)
        super().__init__(playwright_page, opts)
    
    @property
    def page(self) -> Page:
        """Get the underlying Playwright page."""
        return self.interface.page
    
    async def goto(self, url: str, **kwargs) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            **kwargs: Additional arguments passed to page.goto
        """
        await self.interface.goto(url, **kwargs)
    
    async def wait_for_load_state(
        self,
        state: str = "load",
        timeout: Optional[float] = None,
    ) -> None:
        """
        Wait for page to reach a load state.
        
        Args:
            state: Load state ('load', 'domcontentloaded', 'networkidle')
            timeout: Timeout in milliseconds
        """
        await self.interface.wait_for_load_state(state, timeout=timeout)
