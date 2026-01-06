# -*- coding: utf-8 -*-
"""
Service 模块
提供 AI 服务功能，包括元素定位、数据提取等。
"""

import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

from mspy.shared.types import (
    Rect,
    Size,
    LocateResultElement,
    AIUsageInfo,
    ServiceTaskInfo,
    DetailedLocateParam,
)
from mspy.shared.env import IModelConfig
from mspy.shared.env.constants import MIDSCENE_FORCE_DEEP_THINK
from mspy.shared.env import global_config_manager
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition

from ..types import (
    UIContext,
    ServiceDump,
    ServiceError,
    LocateResultWithDump,
    ServiceExtractResult,
)
from ..ai_model import (
    call_ai_with_object_response,
    AIActionType,
)
from ..ai_model.prompt import (
    system_prompt_to_locate_element,
    find_element_prompt,
    system_prompt_to_extract,
    extract_data_query_prompt,
    element_describer_instruction,
)
from ..common import adapt_bbox_to_rect, expand_search_area


debug = get_debug("ai:service")

T = TypeVar("T")


def create_service_dump(
    dump_type: str,
    user_query: Dict[str, Any],
    matched_element: List[LocateResultElement],
    matched_rect: Optional[Rect] = None,
    deep_think: bool = False,
    data: Any = None,
    task_info: Optional[ServiceTaskInfo] = None,
    error: Optional[str] = None,
) -> ServiceDump:
    """
    创建服务转储信息
    
    Args:
        dump_type: 转储类型
        user_query: 用户查询
        matched_element: 匹配的元素列表
        matched_rect: 匹配的矩形区域
        deep_think: 是否深度思考
        data: 数据
        task_info: 任务信息
        error: 错误信息
        
    Returns:
        服务转储信息
    """
    import uuid
    
    return ServiceDump(
        type=dump_type,
        log_id=str(uuid.uuid4()),
        log_time=int(time.time() * 1000),
        user_query=user_query,
        matched_element=matched_element,
        matched_rect=matched_rect,
        deep_think=deep_think,
        data=data,
        task_info=task_info,
        error=error,
    )


def extra_text_from_user_prompt(prompt: Union[str, Dict[str, Any]]) -> str:
    """
    从用户提示中提取文本
    
    Args:
        prompt: 用户提示
        
    Returns:
        文本字符串
    """
    if isinstance(prompt, str):
        return prompt
    return prompt.get("prompt", "")


class Service:
    """
    AI 服务类
    提供元素定位、数据提取等 AI 功能
    """
    
    def __init__(
        self,
        context: Union[UIContext, Callable[[], UIContext]],
        task_info: Optional[ServiceTaskInfo] = None,
    ):
        """
        初始化服务
        
        Args:
            context: UI 上下文或获取上下文的函数
            task_info: 任务信息
        """
        assert_condition(context, "context is required for Service")
        
        if callable(context):
            self._context_retriever_fn = context
        else:
            self._context_retriever_fn = lambda: context
        
        self._task_info = task_info
        self._ai_vendor_fn = call_ai_with_object_response
    
    async def locate(
        self,
        query: Union[str, DetailedLocateParam],
        model_config: IModelConfig,
        context: Optional[UIContext] = None,
    ) -> LocateResultWithDump:
        """
        定位元素
        
        Args:
            query: 查询条件
            model_config: 模型配置
            context: UI 上下文（可选）
            
        Returns:
            定位结果
        """
        if isinstance(query, str):
            query_prompt = query
            deep_think = False
        else:
            query_prompt = query.prompt
            deep_think = query.deep_think
        
        assert_condition(query_prompt, "query is required for locate")
        
        # 检查全局深度思考开关
        global_deep_think = global_config_manager.get_env_config_in_boolean(
            MIDSCENE_FORCE_DEEP_THINK
        )
        if global_deep_think:
            debug(f"globalDeepThinkSwitch: {global_deep_think}")
        
        vl_mode = model_config.vl_mode
        
        ctx = context or self._context_retriever_fn()
        screenshot_base64 = ctx.screenshot_base64
        
        # 构建消息
        system_prompt = system_prompt_to_locate_element(vl_mode)
        user_prompt = find_element_prompt(query_prompt)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": screenshot_base64,
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": user_prompt,
                    },
                ],
            },
        ]
        
        start_time = time.time()
        
        result = await self._ai_vendor_fn(
            messages, AIActionType.INSPECT_ELEMENT, model_config
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        content = result["content"]
        raw_response = result["content_string"]
        usage = result.get("usage")
        
        # 解析结果
        res_rect: Optional[Rect] = None
        matched_elements: List[LocateResultElement] = []
        errors: List[str] = content.get("errors", []) if isinstance(content, dict) else []
        
        try:
            bbox = content.get("bbox", []) if isinstance(content, dict) else []
            if isinstance(bbox, list) and len(bbox) >= 4:
                res_rect = adapt_bbox_to_rect(
                    bbox,
                    ctx.size.width,
                    ctx.size.height,
                    0, 0,
                    ctx.size.width,
                    ctx.size.height,
                    vl_mode,
                )
                
                # 生成元素
                center = (
                    res_rect.left + res_rect.width // 2,
                    res_rect.top + res_rect.height // 2,
                )
                
                element = LocateResultElement(
                    center=center,
                    rect=res_rect,
                    description=query_prompt,
                )
                matched_elements = [element]
                errors = []
        except Exception as e:
            msg = f"Failed to parse bbox: {e}"
            if not errors:
                errors = [msg]
            else:
                errors.append(f"({msg})")
        
        # 创建任务信息
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response=raw_response,
            format_response=str(content),
            usage=usage,
        )
        
        # 构建错误日志
        error_log = None
        if errors:
            error_log = f"failed to locate element: \n{chr(10).join(errors)}"
        
        # 创建 dump
        dump = create_service_dump(
            dump_type="locate",
            user_query={"element": query_prompt},
            matched_element=matched_elements,
            matched_rect=res_rect,
            deep_think=deep_think,
            task_info=task_info,
            error=error_log,
        )
        
        if error_log:
            raise ServiceError(error_log, dump)
        
        if len(matched_elements) > 1:
            raise ServiceError(
                f"locate: multiple elements found, length = {len(matched_elements)}",
                dump
            )
        
        if len(matched_elements) == 1:
            return LocateResultWithDump(
                element=matched_elements[0],
                rect=res_rect,
                dump=dump,
            )
        
        return LocateResultWithDump(
            element=None,
            rect=res_rect,
            dump=dump,
        )
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: IModelConfig,
        screenshot_included: bool = True,
        page_description: str = "",
    ) -> ServiceExtractResult:
        """
        提取数据
        
        Args:
            data_demand: 数据需求
            model_config: 模型配置
            screenshot_included: 是否包含截图
            page_description: 页面描述
            
        Returns:
            提取结果
        """
        assert_condition(
            isinstance(data_demand, (str, dict)),
            f"dataDemand should be object or string, but get {type(data_demand).__name__}"
        )
        
        ctx = self._context_retriever_fn()
        
        system_prompt = system_prompt_to_extract()
        user_prompt = extract_data_query_prompt(page_description, data_demand)
        
        user_content: List[Dict[str, Any]] = []
        
        if screenshot_included:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": ctx.screenshot_base64,
                    "detail": "high",
                },
            })
        
        user_content.append({
            "type": "text",
            "text": user_prompt,
        })
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        
        start_time = time.time()
        
        result = await self._ai_vendor_fn(
            messages, AIActionType.EXTRACT_DATA, model_config
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        content = result["content"]
        usage = result.get("usage")
        
        # 解析结果
        data = content.get("data") if isinstance(content, dict) else content
        thought = content.get("thought") if isinstance(content, dict) else None
        errors = content.get("errors", []) if isinstance(content, dict) else []
        
        error_log = None
        if errors:
            error_log = f"AI response error: \n{chr(10).join(errors)}"
        
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response=str(content),
        )
        
        dump = create_service_dump(
            dump_type="extract",
            user_query={"dataDemand": data_demand},
            matched_element=[],
            data=data,
            task_info=task_info,
            error=error_log,
        )
        
        if error_log and not data:
            raise ServiceError(error_log, dump)
        
        return ServiceExtractResult(
            data=data,
            thought=thought,
            usage=usage,
            dump=dump,
        )
    
    async def describe(
        self,
        target: Union[Rect, Tuple[int, int]],
        model_config: IModelConfig,
        deep_think: bool = False,
    ) -> Dict[str, Any]:
        """
        描述元素
        
        Args:
            target: 目标区域或坐标点
            model_config: 模型配置
            deep_think: 是否深度思考
            
        Returns:
            描述结果
        """
        assert_condition(target, "target is required for service.describe")
        
        ctx = self._context_retriever_fn()
        screenshot_base64 = ctx.screenshot_base64
        
        assert_condition(screenshot_base64, "screenshot is required for service.describe")
        
        vl_mode = model_config.vl_mode
        system_prompt = element_describer_instruction()
        
        # 将坐标点转换为矩形
        default_rect_size = 30
        if isinstance(target, tuple):
            target_rect = Rect(
                left=target[0] - default_rect_size // 2,
                top=target[1] - default_rect_size // 2,
                width=default_rect_size,
                height=default_rect_size,
            )
        else:
            target_rect = target
        
        # 这里简化处理，直接使用截图
        image_payload = screenshot_base64
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_payload,
                            "detail": "high",
                        },
                    },
                ],
            },
        ]
        
        result = await self._ai_vendor_fn(
            messages, AIActionType.DESCRIBE_ELEMENT, model_config
        )
        
        content = result["content"]
        
        assert_condition(
            not content.get("error"),
            f"describe failed: {content.get('error')}"
        )
        assert_condition(
            content.get("description"),
            "failed to describe the element"
        )
        
        return content
