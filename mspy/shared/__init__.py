# -*- coding: utf-8 -*-
"""
Midscene Shared Module
共享模块，包含日志、环境配置、工具函数等
"""

from .logger import get_logger, get_debug
from .env import (
    get_env_config,
    get_model_config,
    ModelConfig,
    ModelConfigManager,
    GlobalConfigManager,
    global_config_manager,
    global_model_config_manager,
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_BASE_URL,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_HTTP_PROXY,
    MIDSCENE_MODEL_TIMEOUT,
    MIDSCENE_MODEL_TEMPERATURE,
    MIDSCENE_MODEL_FAMILY,
    MIDSCENE_MODEL_SKIP_CERT_VERIFICATION,
    MIDSCENE_MODEL_MAX_TOKENS,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
    MIDSCENE_FORCE_DEEP_THINK,
    get_env_bool,
    get_env_int,
)
from .utils import assert_condition, sleep_ms, distance_of_two_points, included_in_rect
from .types import (
    Size, 
    Rect, 
    Point, 
    UIContext, 
    LocateResultElement,
    AIUsageInfo,
    PlanningAction,
    PlanningAIResponse,
    DetailedLocateParam,
    ServiceDump,
    ServiceError,
    ExecutionTask,
    ExecutionDump,
    GroupedActionDump,
    ExecutionTaskTiming,
    TUserPrompt,
)
from .img import (
    image_info_of_base64,
    resize_img_base64,
    create_img_base64_by_format,
    parse_base64,
    crop_by_rect,
)

__all__ = [
    # Logger
    'get_logger',
    'get_debug',
    # Environment
    'get_env_config',
    'get_model_config',
    'ModelConfig',
    'ModelConfigManager',
    'GlobalConfigManager',
    'global_config_manager',
    'global_model_config_manager',
    'MIDSCENE_MODEL_NAME',
    'MIDSCENE_MODEL_BASE_URL',
    'MIDSCENE_MODEL_API_KEY',
    'MIDSCENE_MODEL_HTTP_PROXY',
    'MIDSCENE_MODEL_TIMEOUT',
    'MIDSCENE_MODEL_TEMPERATURE',
    'MIDSCENE_MODEL_FAMILY',
    'MIDSCENE_MODEL_SKIP_CERT_VERIFICATION',
    'MIDSCENE_MODEL_MAX_TOKENS',
    'MIDSCENE_REPLANNING_CYCLE_LIMIT',
    'MIDSCENE_FORCE_DEEP_THINK',
    'get_env_bool',
    'get_env_int',
    # Utils
    'assert_condition',
    'sleep_ms',
    'distance_of_two_points',
    'included_in_rect',
    # Types
    'Size',
    'Rect',
    'Point',
    'UIContext',
    'LocateResultElement',
    'AIUsageInfo',
    'PlanningAction',
    'PlanningAIResponse',
    'DetailedLocateParam',
    'ServiceDump',
    'ServiceError',
    'ExecutionTask',
    'ExecutionDump',
    'GroupedActionDump',
    'ExecutionTaskTiming',
    'TUserPrompt',
    # Image
    'image_info_of_base64',
    'resize_img_base64',
    'create_img_base64_by_format',
    'parse_base64',
    'crop_by_rect',
]
