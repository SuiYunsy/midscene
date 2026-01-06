"""
Playwright Agent封装

从 packages/web-integration/src/puppeteer/agent-launcher.ts 迁移
"""

import time
from typing import Any, Optional, TYPE_CHECKING

from mspy.core.agent import Agent
from mspy.core.types import AgentOpt
from mspy.shared.constants import (
    DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
    DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
)
from mspy.shared.logger import get_debug
from mspy.web.playwright.page import PlaywrightPage

if TYPE_CHECKING:
    from playwright.async_api import Page as PlaywrightPageType


_debug = get_debug("web:playwright:agent")


class PlaywrightAgent(Agent):
    """
    Playwright Agent
    
    封装Playwright页面的AI Agent
    """
    
    def __init__(
        self,
        page: "PlaywrightPageType",
        test_id: Optional[str] = None,
        group_name: str = "Midscene Playwright Report",
        group_description: Optional[str] = None,
        generate_report: bool = True,
        wait_for_navigation_timeout: int = DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
        wait_for_network_idle_timeout: int = DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
        force_same_tab_navigation: bool = True,
        **kwargs
    ):
        # 创建PlaywrightPage封装
        playwright_page = PlaywrightPage(
            page,
            wait_for_navigation_timeout=wait_for_navigation_timeout,
            wait_for_network_idle_timeout=wait_for_network_idle_timeout,
        )
        
        # Agent选项
        opts = AgentOpt(
            test_id=test_id,
            group_name=group_name,
            group_description=group_description,
            generate_report=generate_report,
        )
        
        super().__init__(playwright_page, opts)
        
        self._wait_for_network_idle_timeout = wait_for_network_idle_timeout
        self._force_same_tab_navigation = force_same_tab_navigation
        
        # Dump更新回调
        self.on_dump_update: Optional[Any] = None
        
        # 监听dump更新
        def on_update(dump_string: str, execution: Any) -> None:
            if self.on_dump_update:
                self.on_dump_update(dump_string)
        
        self._remove_listener = self.add_dump_update_listener(on_update)
    
    async def wait_for_network_idle(
        self,
        timeout: Optional[int] = None
    ) -> None:
        """等待网络空闲"""
        timeout = timeout or self._wait_for_network_idle_timeout
        page = self.interface
        if isinstance(page, PlaywrightPage):
            await page.wait_for_network_idle(timeout)
    
    async def destroy(self) -> None:
        """销毁Agent"""
        if self._remove_listener:
            self._remove_listener()
        await super().destroy()


async def create_playwright_agent(
    page: "PlaywrightPageType",
    **kwargs
) -> PlaywrightAgent:
    """
    创建Playwright Agent的便捷函数
    
    Args:
        page: Playwright页面对象
        **kwargs: 传递给PlaywrightAgent的其他参数
    
    Returns:
        PlaywrightAgent实例
    """
    return PlaywrightAgent(page, **kwargs)
