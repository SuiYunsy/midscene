# -*- coding: utf-8 -*-
"""
mspy shared 模块
提供基础工具函数、类型定义、环境配置和日志功能。
"""

from .utils import (
    uuid,
    generate_hash_id,
    assert_condition,
    escape_script_tag,
    anti_escape_script_tag,
    replace_illegal_path_chars,
    log_msg,
)
from .types import (
    BaseElement,
    Rect,
    Size,
    Point,
    LocateResultElement,
    ElementTreeNode,
)
from .env import (
    GlobalConfigManager,
    ModelConfigManager,
    global_config_manager,
    global_model_config_manager,
    get_preferred_language,
    IModelConfig,
    TModelConfig,
    TVlModeTypes,
)
from .logger import get_debug, enable_debug, cleanup_log_streams
from .common import (
    get_midscene_run_dir,
    get_midscene_run_base_dir,
    get_midscene_run_sub_dir,
    DEFAULT_RUN_DIR_NAME,
)

__all__ = [
    # utils
    "uuid",
    "generate_hash_id",
    "assert_condition",
    "escape_script_tag",
    "anti_escape_script_tag",
    "replace_illegal_path_chars",
    "log_msg",
    # types
    "BaseElement",
    "Rect",
    "Size",
    "Point",
    "LocateResultElement",
    "ElementTreeNode",
    # env
    "GlobalConfigManager",
    "ModelConfigManager",
    "global_config_manager",
    "global_model_config_manager",
    "get_preferred_language",
    "IModelConfig",
    "TModelConfig",
    "TVlModeTypes",
    # logger
    "get_debug",
    "enable_debug",
    "cleanup_log_streams",
    # common
    "get_midscene_run_dir",
    "get_midscene_run_base_dir",
    "get_midscene_run_sub_dir",
    "DEFAULT_RUN_DIR_NAME",
]
