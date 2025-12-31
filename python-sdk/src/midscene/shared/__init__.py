"""Shared utilities, types, and constants for Midscene Python SDK."""

from midscene.shared.utils import (
    uuid,
    generate_hash_id,
    assert_condition,
    escape_script_tag,
    anti_escape_script_tag,
    replace_illegal_path_chars_and_space,
)
from midscene.shared.logger import get_logger
from midscene.shared.common import (
    get_midscene_run_dir,
    get_midscene_run_base_dir,
    get_midscene_run_sub_dir,
    DEFAULT_RUN_DIR_NAME,
)

__all__ = [
    # Utils
    "uuid",
    "generate_hash_id",
    "assert_condition",
    "escape_script_tag",
    "anti_escape_script_tag",
    "replace_illegal_path_chars_and_space",
    # Logger
    "get_logger",
    # Common
    "get_midscene_run_dir",
    "get_midscene_run_base_dir",
    "get_midscene_run_sub_dir",
    "DEFAULT_RUN_DIR_NAME",
]
