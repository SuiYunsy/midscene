"""
Midscene Python SDK - Shared Module
共享模块，包含类型定义、日志、环境配置和工具函数
"""

from .types import (
    Rect,
    Size,
    Point,
    BaseElement,
    LocateResultElement,
    AIUsageInfo,
    AIResponseFormat,
    UIContext,
    PlanningAction,
    PlanningAIResponse,
    ServiceAction,
    ServiceTaskInfo,
    ServiceDump,
    ServiceError,
    LocateResult,
    LocateResultWithDump,
    IModelConfig,
    DetailedLocateParam,
    PlanningLocateParam,
)

from .env import (
    GlobalConfigManager,
    ModelConfigManager,
    global_config_manager,
    global_model_config_manager,
    MIDSCENE_MODEL_NAME,
    MIDSCENE_MODEL_API_KEY,
    MIDSCENE_MODEL_BASE_URL,
    MIDSCENE_MODEL_HTTP_PROXY,
    MIDSCENE_MODEL_TIMEOUT,
    MIDSCENE_MODEL_TEMPERATURE,
    MIDSCENE_MODEL_FAMILY,
    MIDSCENE_MODEL_SKIP_CERT_VERIFICATION,
    MIDSCENE_REPLANNING_CYCLE_LIMIT,
)

from .logger import (
    get_logger,
    get_debug,
    log_request_response,
)

from .img import (
    ImageInfo,
    image_info_of_base64,
    resize_img_base64,
    create_img_base64_by_format,
    crop_by_rect,
    composite_element_info_img,
)

from .utils import (
    uuid,
    sleep,
    assert_value,
    current_timestamp_ms,
    escape_script_tag,
    distance_of_two_points,
    included_in_rect,
    overlapped,
    log_msg,
)

__all__ = [
    # Types
    "Rect",
    "Size",
    "Point",
    "BaseElement",
    "LocateResultElement",
    "AIUsageInfo",
    "AIResponseFormat",
    "UIContext",
    "PlanningAction",
    "PlanningAIResponse",
    "ServiceAction",
    "ServiceTaskInfo",
    "ServiceDump",
    "ServiceError",
    "LocateResult",
    "LocateResultWithDump",
    "IModelConfig",
    "DetailedLocateParam",
    "PlanningLocateParam",
    # Env
    "GlobalConfigManager",
    "ModelConfigManager",
    "global_config_manager",
    "global_model_config_manager",
    "MIDSCENE_MODEL_NAME",
    "MIDSCENE_MODEL_API_KEY",
    "MIDSCENE_MODEL_BASE_URL",
    "MIDSCENE_MODEL_HTTP_PROXY",
    "MIDSCENE_MODEL_TIMEOUT",
    "MIDSCENE_MODEL_TEMPERATURE",
    "MIDSCENE_MODEL_FAMILY",
    "MIDSCENE_MODEL_SKIP_CERT_VERIFICATION",
    "MIDSCENE_REPLANNING_CYCLE_LIMIT",
    # Logger
    "get_logger",
    "get_debug",
    "log_request_response",
    # Img
    "ImageInfo",
    "image_info_of_base64",
    "resize_img_base64",
    "create_img_base64_by_format",
    "crop_by_rect",
    "composite_element_info_img",
    # Utils
    "uuid",
    "sleep",
    "assert_value",
    "current_timestamp_ms",
    "escape_script_tag",
    "distance_of_two_points",
    "included_in_rect",
    "overlapped",
    "log_msg",
]
