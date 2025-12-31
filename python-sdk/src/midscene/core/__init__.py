"""Core module for Midscene AI automation."""

from midscene.core.agent import Agent
from midscene.core.service import Service
from midscene.core.types import (
    UIContext,
    ServiceError,
    AgentOpt,
    LocateOption,
    LocateResult,
    PlanningAction,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "Agent",
    "Service",
    "UIContext",
    "ServiceError",
    "AgentOpt",
    "LocateOption",
    "LocateResult",
    "PlanningAction",
]
