# -*- coding: utf-8 -*-
"""
Midscene Core Module
核心模块，包含Agent、任务执行器、AI模型调用等
"""

from .agent import Agent, create_agent
from .service import Service
from .task_runner import TaskRunner, TaskExecutionError
from .task_executor import TaskExecutor, ExecutionSession
from .device import (
    AbstractInterface,
    define_action,
    define_action_tap,
    define_action_right_click,
    define_action_double_click,
    define_action_hover,
    define_action_input,
    define_action_keyboard_press,
    define_action_scroll,
    define_action_assert,
)
from .service_caller import call_ai, call_ai_with_object_response
from .conversation_history import ConversationHistory
from .llm_planning import plan
from .common import (
    fill_bbox_param,
    adapt_bbox,
    adapt_bbox_to_rect,
    expand_search_area,
    merge_rects,
    generate_element_by_position,
)

__all__ = [
    # Agent
    'Agent',
    'create_agent',
    # Service
    'Service',
    # Task
    'TaskRunner',
    'TaskExecutionError',
    'TaskExecutor',
    'ExecutionSession',
    # Device
    'AbstractInterface',
    'define_action',
    'define_action_tap',
    'define_action_right_click',
    'define_action_double_click',
    'define_action_hover',
    'define_action_input',
    'define_action_keyboard_press',
    'define_action_scroll',
    'define_action_assert',
    # AI
    'call_ai',
    'call_ai_with_object_response',
    'ConversationHistory',
    'plan',
    # Common
    'fill_bbox_param',
    'adapt_bbox',
    'adapt_bbox_to_rect',
    'expand_search_area',
    'merge_rects',
    'generate_element_by_position',
]
