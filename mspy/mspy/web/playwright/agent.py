"""
Playwright Agent

提供基于Playwright的高级Agent封装。
"""

import asyncio
import logging
from typing import Optional, Any, Dict

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from mspy.web.playwright.page import PlaywrightPage
from mspy.core.agent import Agent, AgentOpt
from mspy.shared.logger import get_debug

logger = logging.getLogger("midscene.web")
debug = get_debug("web:agent")


class PlaywrightAgent(Agent):
    """
    Playwright Agent
    
    封装Playwright浏览器操作的Agent。
    """
    
    def __init__(
        self,
        playwright_page: PlaywrightPage,
        opts: Optional[AgentOpt] = None,
        browser: Optional[Browser] = None,
        context: Optional[BrowserContext] = None,
    ):
        """
        初始化Playwright Agent
        
        Args:
            playwright_page: Playwright页面封装
            opts: Agent选项
            browser: Playwright浏览器实例（用于资源管理）
            context: Playwright浏览器上下文（用于资源管理）
        """
        super().__init__(playwright_page, opts)
        
        self._browser = browser
        self._context = context
        self._page = playwright_page.underlying_page
    
    @classmethod
    async def create(
        cls,
        url: str,
        opts: Optional[Dict[str, Any]] = None,
        browser_opts: Optional[Dict[str, Any]] = None,
    ) -> "PlaywrightAgent":
        """
        创建Playwright Agent
        
        Args:
            url: 要访问的URL
            opts: Agent选项
            browser_opts: 浏览器选项
                - headless: 是否无头模式（默认True）
                - viewport_width: 视口宽度
                - viewport_height: 视口高度
                - user_agent: 用户代理
                
        Returns:
            PlaywrightAgent实例
        """
        browser_opts = browser_opts or {}
        
        debug(f"Creating Playwright Agent for URL: {url}")
        
        # 启动Playwright
        pw = await async_playwright().start()
        
        # 启动浏览器
        headless = browser_opts.get("headless", True)
        browser = await pw.chromium.launch(headless=headless)
        
        # 创建上下文
        viewport_width = browser_opts.get("viewport_width", 1280)
        viewport_height = browser_opts.get("viewport_height", 720)
        user_agent = browser_opts.get("user_agent")
        
        context_opts: Dict[str, Any] = {
            "viewport": {"width": viewport_width, "height": viewport_height},
        }
        if user_agent:
            context_opts["user_agent"] = user_agent
        
        context = await browser.new_context(**context_opts)
        
        # 创建页面
        page = await context.new_page()
        
        # 导航到URL
        debug(f"Navigating to {url}")
        await page.goto(url)
        
        # 等待页面加载
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            debug("Network idle timeout, continuing anyway")
        
        # 创建封装
        playwright_page = PlaywrightPage(page)
        
        # 创建Agent选项
        agent_opts = None
        if opts:
            agent_opts = AgentOpt(**opts)
        
        agent = cls(
            playwright_page=playwright_page,
            opts=agent_opts,
            browser=browser,
            context=context,
        )
        
        # 保存playwright实例用于清理
        agent._playwright = pw
        
        return agent
    
    async def goto(self, url: str) -> None:
        """
        导航到URL
        
        Args:
            url: 目标URL
        """
        debug(f"Navigating to {url}")
        await self._page.goto(url)
        
        try:
            await self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            debug("Network idle timeout, continuing anyway")
    
    async def destroy(self) -> None:
        """销毁Agent并释放资源"""
        if self.destroyed:
            return
        
        debug("Destroying Playwright Agent")
        
        # 关闭上下文
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
        
        # 关闭浏览器
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
        
        # 关闭Playwright
        if hasattr(self, "_playwright") and self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        
        await super().destroy()
    
    @property
    def page(self) -> Page:
        """获取底层Playwright页面"""
        return self._page
