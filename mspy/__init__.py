"""
Midscene Python SDK
AI驱动的UI自动化框架

Midscene 是一个基于AI的UI自动化框架，支持通过自然语言描述来操作Web页面。

主要特性:
- 使用AI模型（如qwen3-vl）进行元素定位和动作规划
- 支持Playwright集成
- 提供简单易用的Agent API

使用示例:
    from mspy import Agent
    from mspy.web import create_playwright_page
    
    async def main():
        web_page, browser, context = await create_playwright_page(
            url="https://example.com",
            headless=False,
        )
        
        agent = Agent(web_page)
        await agent.ai_act("点击登录按钮")
        await agent.ai_assert("页面显示登录表单")
        
        await browser.close()
"""

__version__ = "0.1.0"

# 导入核心模块
from .core import (
    Agent,
    AgentOpt,
    create_agent,
    AbstractInterface,
    DeviceAction,
    define_action,
    Service,
    TaskExecutor,
    TaskExecutionError,
    ExecutionResult,
    ConversationHistory,
)

# 导入共享模块
from .shared import (
    Rect,
    Size,
    Point,
    UIContext,
    IModelConfig,
    ModelConfigManager,
    GlobalConfigManager,
    global_config_manager,
    global_model_config_manager,
    get_logger,
    get_debug,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "Agent",
    "AgentOpt",
    "create_agent",
    "AbstractInterface",
    "DeviceAction",
    "define_action",
    "Service",
    "TaskExecutor",
    "TaskExecutionError",
    "ExecutionResult",
    "ConversationHistory",
    # Shared
    "Rect",
    "Size",
    "Point",
    "UIContext",
    "IModelConfig",
    "ModelConfigManager",
    "GlobalConfigManager",
    "global_config_manager",
    "global_model_config_manager",
    "get_logger",
    "get_debug",
]
