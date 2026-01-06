"""
核心模块 - 提供Agent、Service和AI模型调用等核心功能

对应TypeScript源码: packages/core/src/
"""

from mspy.core.agent import Agent, AgentOpt, AiActOptions
from mspy.core.service import Service
from mspy.core.types import (
    UIContext,
    ServiceError,
    LocateResult,
    LocateResultWithDump,
    ServiceExtractResult,
    ExecutionTask,
    ExecutionDump,
    GroupedActionDump,
    PlanningAction,
    PlanningAIResponse,
)

__all__ = [
    # Agent
    "Agent",
    "AgentOpt",
    "AiActOptions",
    # Service
    "Service",
    # Types
    "UIContext",
    "ServiceError",
    "LocateResult",
    "LocateResultWithDump",
    "ServiceExtractResult",
    "ExecutionTask",
    "ExecutionDump",
    "GroupedActionDump",
    "PlanningAction",
    "PlanningAIResponse",
]
