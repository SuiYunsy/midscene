"""
Midscene Python - AI驱动的UI自动化框架

这是Midscene的Python实现版本，提供了以下核心功能：
- ai_act: 使用自然语言描述执行UI操作
- ai_assert: 使用自然语言进行UI断言

示例:
    from mspy import Agent
    from mspy.web import create_playwright_page

    async def main():
        browser, page = await create_playwright_page(headless=False)
        agent = Agent(page)
        
        await page.navigate("https://example.com")
        await agent.ai_act("点击按钮")
        await agent.ai_assert("页面显示成功消息")
        
        await browser.close()
"""

__version__ = "0.1.0"

from .core import (
    Agent,
    create_agent,
    AbstractInterface,
    Service,
    TaskRunner,
    TaskExecutionError,
)
from .shared import (
    get_debug,
    set_log_level,
    IModelConfig,
    ModelConfigManager,
    UIContext,
    Size,
    Rect,
    LocateResultElement,
    AgentOpt,
)

__all__ = [
    # Version
    '__version__',
    # Core
    'Agent',
    'create_agent',
    'AbstractInterface',
    'Service',
    'TaskRunner',
    'TaskExecutionError',
    # Shared
    'get_debug',
    'set_log_level',
    'IModelConfig',
    'ModelConfigManager',
    'UIContext',
    'Size',
    'Rect',
    'LocateResultElement',
    'AgentOpt',
]
