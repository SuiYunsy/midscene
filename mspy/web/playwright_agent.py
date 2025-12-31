# -*- coding: utf-8 -*-
"""
Midscene Playwright Agent Module
Playwright Agent模块，封装Agent用于Playwright页面
"""

from typing import Dict, Any, Optional

from playwright.async_api import Page as PlaywrightPageType

from ..shared import get_logger
from ..core.agent import Agent
from .playwright_page import PlaywrightPage

logger = get_logger("playwright:agent")


class PlaywrightAgent(Agent):
    """
    Playwright Agent类
    封装Agent，专门用于Playwright页面的AI驱动自动化
    """
    
    def __init__(
        self,
        page: PlaywrightPageType,
        opts: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Playwright Agent
        
        Args:
            page: Playwright Page对象
            opts: 选项配置
        """
        # 创建PlaywrightPage包装器
        web_page = PlaywrightPage(page, opts)
        
        # 调用父类初始化
        super().__init__(web_page, opts)
        
        # 保存原始page引用
        self._playwright_page = page
        self._web_page = web_page
    
    @property
    def page(self) -> PlaywrightPage:
        """获取PlaywrightPage对象"""
        return self._web_page
    
    @property
    def underlying_page(self) -> PlaywrightPageType:
        """获取底层Playwright Page"""
        return self._playwright_page
    
    async def wait_for_network_idle(self, timeout: int = 1000) -> None:
        """
        等待网络空闲
        
        Args:
            timeout: 超时时间（毫秒）
        """
        await self._web_page.wait_for_network_idle(timeout)
    
    async def navigate(self, url: str) -> None:
        """
        导航到URL
        
        Args:
            url: 目标URL
        """
        await self._web_page.navigate(url)
    
    async def reload(self) -> None:
        """刷新页面"""
        await self._web_page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        await self._web_page.go_back()
    
    async def url(self) -> str:
        """获取当前URL"""
        return await self._web_page.url()
