# -*- coding: utf-8 -*-
"""
Midscene Service Module
服务模块，提供定位、提取等AI服务
"""

import time
from typing import Dict, Any, Optional, Tuple, List, Union
import uuid

from ..shared import (
    get_logger,
    ModelConfig,
    UIContext,
    Rect,
    LocateResultElement,
    DetailedLocateParam,
    ServiceDump,
    ServiceError,
    AIUsageInfo,
    assert_condition,
)
from .service_caller import call_ai_with_object_response
from .common import adapt_bbox_to_rect

logger = get_logger("ai:service")


class Service:
    """AI服务类，提供定位、提取等功能"""
    
    def __init__(
        self,
        context_retriever_fn: callable,
    ):
        """
        初始化服务
        
        Args:
            context_retriever_fn: 获取UI上下文的函数
        """
        self.context_retriever_fn = context_retriever_fn
    
    async def locate(
        self,
        query: Union[str, Dict[str, Any]],
        opt: Optional[Dict[str, Any]] = None,
        model_config: Optional[ModelConfig] = None,
    ) -> Dict[str, Any]:
        """
        定位元素
        
        Args:
            query: 定位查询，可以是字符串或DetailedLocateParam
            opt: 选项
            model_config: 模型配置
        
        Returns:
            包含element和dump的结果
        """
        opt = opt or {}
        query_prompt = query if isinstance(query, str) else query.get("prompt", "")
        
        assert_condition(query_prompt, "query is required for locate")
        assert_condition(model_config, "model_config is required for locate")
        
        context = opt.get("context") or await self.context_retriever_fn()
        
        start_time = time.time()
        
        # 构建定位请求
        system_prompt = """You are a UI element locator. Given a screenshot and a description of an element, 
find the element and return its bounding box coordinates.

Return format:
{
    "elements": [
        {
            "bbox": [xmin, ymin, xmax, ymax], // bounding box in 0-1000 normalized coordinates
            "description": string, // brief description of the element
            "confidence": number // confidence score 0-1
        }
    ],
    "errors": [] // any error messages
}

If no element is found, return empty elements array.
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Find the element: {query_prompt}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": context.screenshot_base64,
                            "detail": "high",
                        },
                    },
                ],
            },
        ]
        
        result = await call_ai_with_object_response(messages, model_config)
        
        time_cost = int((time.time() - start_time) * 1000)
        
        parse_result = result["content"]
        raw_response = result["contentString"]
        usage = result["usage"]
        
        # 解析结果
        elements = parse_result.get("elements", [])
        errors = parse_result.get("errors", [])
        
        # 转换元素
        located_elements = []
        matched_rect = None
        
        for elem in elements:
            bbox = elem.get("bbox")
            if bbox:
                rect = adapt_bbox_to_rect(
                    bbox,
                    context.size.width,
                    context.size.height,
                    vl_mode=model_config.vl_mode,
                )
                center = (
                    rect.left + rect.width // 2,
                    rect.top + rect.height // 2,
                )
                located_elements.append(LocateResultElement(
                    center=center,
                    rect=rect,
                    description=elem.get("description"),
                ))
                if matched_rect is None:
                    matched_rect = rect
        
        # 构建dump
        task_info = {
            "durationMs": time_cost,
            "rawResponse": raw_response,
            "formatResponse": str(parse_result),
            "usage": usage.to_dict() if usage else None,
        }
        
        error_log = None
        if errors:
            error_log = f"failed to locate element: \n" + "\n".join(errors)
        
        dump = ServiceDump(
            type="locate",
            log_id=str(uuid.uuid4()),
            log_time=int(time.time() * 1000),
            user_query={"element": query_prompt},
            matched_element=located_elements,
            matched_rect=matched_rect,
            data=None,
            task_info=task_info,
            error=error_log,
        )
        
        if error_log:
            raise ServiceError(error_log, dump)
        
        if len(located_elements) > 1:
            raise ServiceError(
                f"locate: multiple elements found, length = {len(located_elements)}",
                dump,
            )
        
        element = located_elements[0] if located_elements else None
        
        return {
            "element": element,
            "rect": matched_rect,
            "dump": dump,
        }
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: ModelConfig,
        opt: Optional[Dict[str, Any]] = None,
        page_description: Optional[str] = None,
        multimodal_prompt: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        提取数据
        
        Args:
            data_demand: 数据需求
            model_config: 模型配置
            opt: 选项
            page_description: 页面描述
            multimodal_prompt: 多模态提示
        
        Returns:
            包含data、thought、usage和dump的结果
        """
        opt = opt or {}
        context = await self.context_retriever_fn()
        
        start_time = time.time()
        
        # 构建提取请求
        demand_str = data_demand if isinstance(data_demand, str) else str(data_demand)
        
        system_prompt = """You are a data extractor. Given a screenshot and a data demand, 
extract the requested information.

Return format:
{
    "data": <extracted data matching the demand format>,
    "thought": string, // your reasoning process
    "errors": [] // any error messages
}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Extract the following data: {demand_str}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": context.screenshot_base64,
                            "detail": "high",
                        },
                    },
                ],
            },
        ]
        
        result = await call_ai_with_object_response(messages, model_config)
        
        time_cost = int((time.time() - start_time) * 1000)
        
        parse_result = result["content"]
        raw_response = result["contentString"]
        usage = result["usage"]
        
        data = parse_result.get("data")
        thought = parse_result.get("thought")
        errors = parse_result.get("errors", [])
        
        # 构建dump
        task_info = {
            "durationMs": time_cost,
            "rawResponse": raw_response,
        }
        
        error_log = None
        if errors:
            error_log = f"AI response error: \n" + "\n".join(errors)
        
        dump = ServiceDump(
            type="extract",
            log_id=str(uuid.uuid4()),
            log_time=int(time.time() * 1000),
            user_query={"dataDemand": data_demand},
            matched_element=[],
            data=data,
            task_info=task_info,
            error=error_log,
        )
        
        if error_log and data is None:
            raise ServiceError(error_log, dump)
        
        return {
            "data": data,
            "thought": thought,
            "usage": usage,
            "dump": dump,
        }
