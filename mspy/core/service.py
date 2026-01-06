"""
服务模块 - 处理元素定位和数据提取
Service module - handles element locating and data extraction
"""
import time
from typing import Any, Dict, List, Optional, Callable, Tuple

from ..shared import (
    get_debug,
    uuid,
    assert_condition,
    ModelConfig,
    UIContext,
    Rect,
    LocateResultElement,
    LocateResultWithDump,
    ServiceDump,
    ServiceError,
    DetailedLocateParam,
    AIUsageInfo,
)

from .service_caller import call_ai_with_object_response

debug = get_debug("ai:service")


def create_service_dump(
    dump_type: str,
    user_query: Dict[str, Any],
    matched_element: List[LocateResultElement],
    matched_rect: Optional[Rect],
    data: Any,
    task_info: Dict[str, Any],
    deep_think: bool = False,
    error: Optional[str] = None,
) -> ServiceDump:
    """
    Create a service dump.
    创建服务dump
    """
    return ServiceDump(
        log_time=int(time.time() * 1000),
        log_id=uuid(),
        type=dump_type,
        user_query=user_query,
        matched_element=matched_element,
        matched_rect=matched_rect,
        data=data,
        task_info=task_info,
        deep_think=deep_think,
        error=error,
    )


class Service:
    """
    Service for AI-based element location and data extraction.
    基于AI的元素定位和数据提取服务
    """
    
    def __init__(
        self,
        context_retriever: Callable[[], UIContext],
    ):
        self.context_retriever_fn = context_retriever
    
    async def locate(
        self,
        query: DetailedLocateParam,
        context: Optional[UIContext],
        model_config: ModelConfig,
    ) -> LocateResultWithDump:
        """
        Locate an element on the page.
        在页面上定位元素
        
        Args:
            query: Locate query with prompt
            context: UI context (optional, will be fetched if not provided)
            model_config: Model configuration
            
        Returns:
            Locate result with element and dump
        """
        query_prompt = query.prompt
        assert_condition(query_prompt, "Query is required for locate")
        
        if context is None:
            context = self.context_retriever_fn()
        
        vl_mode = model_config.vl_mode
        
        start_time = time.time()
        
        # Build locate prompt
        system_prompt = self._build_locate_system_prompt(vl_mode)
        
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
        
        try:
            result = call_ai_with_object_response(messages, model_config)
            parse_result = result["content"]
            raw_response = result["content_string"]
            usage = result.get("usage")
        except Exception as e:
            error_dump = create_service_dump(
                dump_type="locate",
                user_query={"element": query_prompt},
                matched_element=[],
                matched_rect=None,
                data=None,
                task_info={"durationMs": int((time.time() - start_time) * 1000)},
                error=str(e),
            )
            raise ServiceError(str(e), error_dump) from e
        
        time_cost = int((time.time() - start_time) * 1000)
        
        task_info = {
            "durationMs": time_cost,
            "rawResponse": raw_response,
            "formatResponse": str(parse_result),
            "usage": usage,
        }
        
        # Parse bbox from response
        bbox = parse_result.get("bbox")
        element = None
        matched_rect = None
        
        if bbox and len(bbox) >= 4:
            # Convert bbox to rect
            rect = self._bbox_to_rect(
                bbox,
                context.size.width,
                context.size.height,
                vl_mode,
            )
            matched_rect = rect
            
            center = (
                rect.left + rect.width // 2,
                rect.top + rect.height // 2,
            )
            
            element = LocateResultElement(
                center=center,
                rect=rect,
                description=query_prompt,
            )
        
        error_log = None
        if parse_result.get("errors"):
            error_log = f"Failed to locate element: {parse_result['errors']}"
        
        dump = create_service_dump(
            dump_type="locate",
            user_query={"element": query_prompt},
            matched_element=[element] if element else [],
            matched_rect=matched_rect,
            data=None,
            task_info=task_info,
            deep_think=query.deep_think,
            error=error_log,
        )
        
        if error_log:
            raise ServiceError(error_log, dump)
        
        return LocateResultWithDump(
            element=element,
            rect=matched_rect,
            dump=dump,
        )
    
    def _build_locate_system_prompt(self, vl_mode: Optional[str]) -> str:
        """Build system prompt for locate."""
        if vl_mode == "gemini":
            bbox_desc = "Return box_2d as [ymin, xmin, ymax, xmax] normalized to 0-1000"
        elif vl_mode in ("qwen3-vl", "qwen2.5-vl"):
            bbox_desc = "Return bbox as [xmin, ymin, xmax, ymax] normalized to 0-1000"
        else:
            bbox_desc = "Return bbox as [xmin, ymin, xmax, ymax] in pixels"
        
        return f"""You are an element locator. Given an image and element description, find the element and return its bounding box.

{bbox_desc}

Return in JSON format:
{{
  "bbox": [number, number, number, number],
  "reason": string
}}

If the element is not found, return:
{{
  "bbox": null,
  "errors": ["Element not found: <reason>"]
}}
"""
    
    def _bbox_to_rect(
        self,
        bbox: List[int],
        width: int,
        height: int,
        vl_mode: Optional[str],
    ) -> Rect:
        """Convert bbox to Rect."""
        # Adapt based on VL mode
        if vl_mode == "gemini":
            # [ymin, xmin, ymax, xmax] normalized to 0-1000
            left = round((bbox[1] * width) / 1000)
            top = round((bbox[0] * height) / 1000)
            right = round((bbox[3] * width) / 1000)
            bottom = round((bbox[2] * height) / 1000)
        elif vl_mode in ("qwen3-vl", "qwen2.5-vl", "doubao-vision", "vlm-ui-tars"):
            # [xmin, ymin, xmax, ymax] normalized to 0-1000
            left = round((bbox[0] * width) / 1000)
            top = round((bbox[1] * height) / 1000)
            right = round((bbox[2] * width) / 1000)
            bottom = round((bbox[3] * height) / 1000)
        else:
            # Direct pixel values
            left, top, right, bottom = bbox[0], bbox[1], bbox[2], bbox[3]
        
        return Rect(
            left=left,
            top=top,
            width=right - left,
            height=bottom - top,
        )
    
    async def extract(
        self,
        data_demand: Any,
        model_config: ModelConfig,
        context: Optional[UIContext] = None,
    ) -> Dict[str, Any]:
        """
        Extract data from the page.
        从页面提取数据
        """
        if context is None:
            context = self.context_retriever_fn()
        
        start_time = time.time()
        
        # Build extract prompt
        system_prompt = """You are a data extractor. Given an image and data requirements, extract the requested data.

Return in JSON format with the requested fields.
"""
        
        if isinstance(data_demand, str):
            demand_text = data_demand
        else:
            demand_text = str(data_demand)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Extract the following data: {demand_text}",
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
        
        result = call_ai_with_object_response(messages, model_config)
        parse_result = result["content"]
        usage = result.get("usage")
        
        time_cost = int((time.time() - start_time) * 1000)
        
        dump = create_service_dump(
            dump_type="extract",
            user_query={"dataDemand": data_demand},
            matched_element=[],
            matched_rect=None,
            data=parse_result,
            task_info={
                "durationMs": time_cost,
                "rawResponse": result["content_string"],
            },
        )
        
        return {
            "data": parse_result,
            "thought": parse_result.get("thought"),
            "usage": usage,
            "dump": dump,
        }
