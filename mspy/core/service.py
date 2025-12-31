"""
服务模块
Service module for Midscene Python SDK
"""
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass

from ..shared import (
    get_debug,
    assert_value,
    uuid,
    current_timestamp_ms,
    UIContext,
    IModelConfig,
    ServiceDump,
    ServiceError,
    ServiceTaskInfo,
    LocateResult,
    LocateResultWithDump,
    LocateResultElement,
    Rect,
    DetailedLocateParam,
)
from .service_caller import call_ai_with_object_response


class AIActionType:
    """AI动作类型常量"""
    PLAN = "plan"
    LOCATE = "locate"
    EXTRACT = "extract"
    ASSERT = "assert"
    DESCRIBE_ELEMENT = "describe_element"


debug = get_debug("ai:service")


def create_service_dump(data: Dict[str, Any]) -> ServiceDump:
    """
    创建服务转储对象
    
    Args:
        data: 转储数据
        
    Returns:
        ServiceDump对象
    """
    return ServiceDump(
        type=data.get("type", "locate"),
        log_id=uuid(),
        log_time=current_timestamp_ms(),
        user_query=data.get("user_query", {}),
        matched_element=data.get("matched_element", []),
        matched_rect=data.get("matched_rect"),
        deep_think=data.get("deep_think", False),
        data=data.get("data"),
        assertion_pass=data.get("assertion_pass"),
        assertion_thought=data.get("assertion_thought"),
        task_info=data.get("task_info"),
        error=data.get("error"),
        output=data.get("output"),
    )


class Service:
    """
    Midscene服务类
    处理定位、提取、断言等操作
    """
    
    def __init__(
        self,
        context: Union[UIContext, Callable[[], Awaitable[UIContext]]],
    ):
        """
        初始化服务
        
        Args:
            context: UI上下文或获取上下文的函数
        """
        assert_value(context, "Context is required for Service")
        
        if callable(context):
            self.context_retriever_fn = context
        else:
            async def get_context():
                return context
            self.context_retriever_fn = get_context
    
    async def locate(
        self,
        query: Union[str, DetailedLocateParam],
        opt: Dict[str, Any],
        model_config: IModelConfig,
    ) -> LocateResultWithDump:
        """
        定位元素
        
        Args:
            query: 查询字符串或详细定位参数
            opt: 选项
            model_config: 模型配置
            
        Returns:
            LocateResultWithDump对象
        """
        # 获取查询提示词
        if isinstance(query, str):
            query_prompt = query
        else:
            query_prompt = query.prompt
        
        assert_value(query_prompt, "Query is required for locate")
        
        # 获取上下文
        context = opt.get("context")
        if not context:
            context = await self.context_retriever_fn()
        
        # 构建定位提示词
        system_prompt = """You are an expert at locating UI elements on screenshots.
Given a screenshot and a description of the target element, return the bounding box of the element.

Return in JSON format:
{
  "bbox": [xmin, ymin, xmax, ymax], // 2d bounding box as [xmin, ymin, xmax, ymax]
  "description": string, // brief description of the found element
  "errors": string[] // any errors encountered
}

If the element is not found, return:
{
  "bbox": null,
  "description": null,
  "errors": ["Element not found: <reason>"]
}
"""
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Please locate: {query_prompt}",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": context.screenshot_base64,
                        "detail": "high",
                    },
                },
            ],
        }
        
        msgs = [
            {"role": "system", "content": system_prompt},
            user_message,
        ]
        
        start_time = current_timestamp_ms()
        
        try:
            response = await call_ai_with_object_response(
                msgs,
                AIActionType.LOCATE,
                model_config,
            )
            
            time_cost = current_timestamp_ms() - start_time
            
            parse_result = response.content
            raw_response = response.content_string
            usage = response.usage
            
            # 构建任务信息
            task_info = ServiceTaskInfo(
                duration_ms=time_cost,
                raw_response=raw_response,
                format_response=str(parse_result),
                usage=usage,
            )
            
            # 检查错误
            error_log = None
            if parse_result.get("errors"):
                error_log = f"Failed to locate element: \n{chr(10).join(parse_result['errors'])}"
            
            # 构建元素列表
            elements = []
            bbox = parse_result.get("bbox")
            if bbox and len(bbox) == 4:
                xmin, ymin, xmax, ymax = bbox
                rect = Rect(
                    left=xmin,
                    top=ymin,
                    width=xmax - xmin,
                    height=ymax - ymin,
                )
                center = (
                    int((xmin + xmax) / 2),
                    int((ymin + ymax) / 2),
                )
                element = LocateResultElement(
                    center=center,
                    rect=rect,
                    description=parse_result.get("description", ""),
                )
                elements.append(element)
            
            # 创建转储
            dump_data = {
                "type": "locate",
                "user_query": {"element": query_prompt},
                "matched_element": elements,
                "matched_rect": elements[0].rect if elements else None,
                "data": None,
                "task_info": task_info,
                "error": error_log,
            }
            
            dump = create_service_dump(dump_data)
            
            if error_log:
                raise ServiceError(error_log, dump)
            
            if len(elements) > 1:
                raise ServiceError(
                    f"Locate: multiple elements found, length = {len(elements)}",
                    dump
                )
            
            if len(elements) == 1:
                return LocateResultWithDump(
                    element=elements[0],
                    rect=elements[0].rect,
                    dump=dump,
                )
            
            return LocateResultWithDump(
                element=None,
                rect=None,
                dump=dump,
            )
            
        except Exception as e:
            time_cost = current_timestamp_ms() - start_time
            task_info = ServiceTaskInfo(
                duration_ms=time_cost,
            )
            
            dump_data = {
                "type": "locate",
                "user_query": {"element": query_prompt},
                "matched_element": [],
                "data": None,
                "task_info": task_info,
                "error": str(e),
            }
            dump = create_service_dump(dump_data)
            
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e), dump)
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: IModelConfig,
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
            包含data、thought、usage、dump的字典
        """
        assert_value(
            isinstance(data_demand, (str, dict)),
            f"dataDemand should be string or dict, but got {type(data_demand)}"
        )
        
        context = await self.context_retriever_fn()
        
        # 构建提取提示词
        if isinstance(data_demand, str):
            demand_text = data_demand
        else:
            demand_text = "\n".join([f"- {k}: {v}" for k, v in data_demand.items()])
        
        system_prompt = """You are an expert at extracting information from screenshots.
Given a screenshot and a data extraction request, analyze the screenshot and return the requested data.

Return in JSON format:
{
  "data": <extracted_data>, // The extracted data matching the request format
  "thought": string, // Your reasoning process
  "errors": string[] // Any errors encountered
}
"""
        
        user_content = [
            {
                "type": "text",
                "text": f"Please extract the following information:\n{demand_text}",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": context.screenshot_base64,
                    "detail": "high",
                },
            },
        ]
        
        if page_description:
            user_content.insert(0, {
                "type": "text",
                "text": f"Page context: {page_description}",
            })
        
        user_message = {
            "role": "user",
            "content": user_content,
        }
        
        msgs = [
            {"role": "system", "content": system_prompt},
            user_message,
        ]
        
        start_time = current_timestamp_ms()
        
        try:
            response = await call_ai_with_object_response(
                msgs,
                AIActionType.EXTRACT,
                model_config,
            )
            
            time_cost = current_timestamp_ms() - start_time
            
            parse_result = response.content
            usage = response.usage
            
            task_info = ServiceTaskInfo(
                duration_ms=time_cost,
                raw_response=response.content_string,
            )
            
            error_log = None
            if parse_result.get("errors"):
                error_log = f"AI response error: \n{chr(10).join(parse_result['errors'])}"
            
            data = parse_result.get("data")
            thought = parse_result.get("thought")
            
            dump_data = {
                "type": "extract",
                "user_query": {"dataDemand": data_demand},
                "matched_element": [],
                "data": data,
                "task_info": task_info,
                "error": error_log,
            }
            dump = create_service_dump(dump_data)
            
            if error_log and not data:
                raise ServiceError(error_log, dump)
            
            return {
                "data": data,
                "thought": thought,
                "usage": usage,
                "dump": dump,
            }
            
        except Exception as e:
            time_cost = current_timestamp_ms() - start_time
            task_info = ServiceTaskInfo(duration_ms=time_cost)
            
            dump_data = {
                "type": "extract",
                "user_query": {"dataDemand": data_demand},
                "matched_element": [],
                "data": None,
                "task_info": task_info,
                "error": str(e),
            }
            dump = create_service_dump(dump_data)
            
            if isinstance(e, ServiceError):
                raise
            raise ServiceError(str(e), dump)
