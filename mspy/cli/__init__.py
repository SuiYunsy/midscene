"""
CLI模块

从 packages/cli/src/ 迁移
"""

from mspy.cli.main import main
from mspy.cli.batch_runner import BatchRunner

__all__ = [
    "main",
    "BatchRunner",
]
