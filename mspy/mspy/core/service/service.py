"""
服务层

提供AI服务的高级封装。
"""

import logging
from typing import Optional, Any, Callable, Awaitable, Dict, Union, Tuple

from mspy.core.types import (
    UIContext,
    LocateResult,
    ServiceExtractOption,
    PlanningAIResponse,
)
from mspy.shared.types import Rect, LocateResultElement, AIUsageInfo
from mspy.shared.env import ModelConfig
from mspy.core.ai_model import (
    call_ai_with_object_response,
)
from mspy.core.ai_model.prompt import (
    build_locate_prompt,
    build_assertion_prompt,
    build_extraction_prompt,
    build_describe_prompt,
)
from mspy.shared.logger import get_debug

logger = logging.getLogger("midscene.service")
debug = get_debug("service")


class Service:
    """
    AI服务层
    
    提供元素定位、数据提取、断言验证等高级功能。
    """
    
    def __init__(
        self,
        get_context: Callable[[], Awaitable[UIContext]],
    ):
        """
        初始化服务
        
        Args:
            get_context: 获取UI上下文的异步函数
        """
        self._get_context = get_context
    
    async def _get_ui_context(self) -> UIContext:
        """获取UI上下文"""
        return await self._get_context()
    
    async def locate(
        self,
        prompt: str,
        model_config: ModelConfig,
        deep_think: bool = False,
    ) -> Tuple[LocateResult, Optional[AIUsageInfo], str]:
        """
        定位元素
        
        Args:
            prompt: 元素描述
            model_config: 模型配置
            deep_think: 是否启用深度思考
            
        Returns:
            (定位结果, 使用信息, 原始响应)
        """
        debug(f"Locating element: {prompt}")
        
        context = await self._get_ui_context()
        
        messages = build_locate_prompt(
            prompt,
            context.screenshot_base64,
            model_config.vl_mode,
        )
        
        result, raw_response, usage = await call_ai_with_object_response(
            messages,
            "locate",
            model_config,
        )
        
        bbox = result.get("bbox")
        
        if not bbox:
            debug(f"Element not found: {result.get('reason')}")
            return LocateResult(element=None), usage, raw_response
        
        # 转换bbox为Rect和center
        xmin, ymin, xmax, ymax = bbox
        width = xmax - xmin
        height = ymax - ymin
        center_x = xmin + width / 2
        center_y = ymin + height / 2
        
        rect = Rect(left=xmin, top=ymin, width=width, height=height)
        element = LocateResultElement(
            description=prompt,
            center=(center_x, center_y),
            rect=rect,
        )
        
        debug(f"Element found at {element.center}")
        
        return LocateResult(element=element, rect=rect), usage, raw_response
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: ModelConfig,
        opt: Optional[ServiceExtractOption] = None,
    ) -> Tuple[Any, Optional[str], Optional[AIUsageInfo]]:
        """
        提取数据
        
        Args:
            data_demand: 数据需求
            model_config: 模型配置
            opt: 提取选项
            
        Returns:
            (提取的数据, 思考过程, 使用信息)
        """
        debug(f"Extracting data: {data_demand}")
        
        context = await self._get_ui_context()
        
        messages = build_extraction_prompt(
            data_demand,
            context.screenshot_base64,
        )
        
        result, raw_response, usage = await call_ai_with_object_response(
            messages,
            "extract",
            model_config,
        )
        
        data = result.get("data")
        thought = result.get("thought")
        
        debug(f"Extracted data: {data}")
        
        return data, thought, usage
    
    async def assert_condition(
        self,
        assertion: str,
        model_config: ModelConfig,
    ) -> Tuple[bool, Optional[str], Optional[AIUsageInfo]]:
        """
        验证断言
        
        Args:
            assertion: 断言描述
            model_config: 模型配置
            
        Returns:
            (是否通过, 思考过程, 使用信息)
        """
        debug(f"Asserting: {assertion}")
        
        context = await self._get_ui_context()
        
        messages = build_assertion_prompt(
            assertion,
            context.screenshot_base64,
        )
        
        result, raw_response, usage = await call_ai_with_object_response(
            messages,
            "assert",
            model_config,
        )
        
        passed = result.get("pass", False)
        thought = result.get("thought")
        
        debug(f"Assertion result: {passed}, reason: {thought}")
        
        return passed, thought, usage
    
    async def describe(
        self,
        center: Tuple[int, int],
        model_config: ModelConfig,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Optional[str]]:
        """
        描述元素
        
        Args:
            center: 元素中心点
            model_config: 模型配置
            opt: 选项（如deep_think）
            
        Returns:
            {"description": str, "error": Optional[str]}
        """
        opt = opt or {}
        deep_think = opt.get("deep_think", False)
        
        debug(f"Describing element at {center}")
        
        context = await self._get_ui_context()
        
        messages = build_describe_prompt(
            center,
            context.screenshot_base64,
            deep_think=deep_think,
        )
        
        result, raw_response, usage = await call_ai_with_object_response(
            messages,
            "describe",
            model_config,
        )
        
        debug(f"Description: {result.get('description')}")
        
        return {
            "description": result.get("description"),
            "error": result.get("error"),
        }
