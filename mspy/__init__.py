# -*- coding: utf-8 -*-
"""
Midscene Python SDK
AI驱动的Web自动化框架

用法：
    from mspy import PlaywrightAgent
    
    agent = PlaywrightAgent(page)
    await agent.ai_act("点击登录按钮")
    await agent.ai_assert("登录成功")
"""

# 导入子模块以便能够使用相对导入
from . import shared
from . import core
from . import web

# 导出主要类
from .web import PlaywrightAgent, PlaywrightPage
from .core import Agent, Service, AbstractInterface

__version__ = "1.0.0"
__all__ = [
    'shared',
    'core', 
    'web',
    'PlaywrightAgent',
    'PlaywrightPage',
    'Agent',
    'Service',
    'AbstractInterface',
]
