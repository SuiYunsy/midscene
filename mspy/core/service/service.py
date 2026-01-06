"""
服务层实现

从 packages/core/src/service/index.ts 迁移
"""

from typing import Any, Callable, Optional

from mspy.core.ai_model import call_ai_with_object_response
from mspy.core.ai_model.prompt import (
    system_prompt_to_locate_element,
    system_prompt_to_extract_data,
    system_prompt_to_assert,
    element_describer_instruction,
)
from mspy.core.types import (
    AIDescribeElementResponse,
    AIUsageInfo,
    LocateResult,
    ServiceDump,
    ServiceTaskInfo,
    UIContext,
)
from mspy.shared.env.types import ModelConfig
from mspy.shared.img import crop_by_rect
from mspy.shared.logger import get_debug
from mspy.shared.types import Rect
from mspy.shared.utils import assert_condition, uuid


_debug = get_debug("ai:service")


class ServiceError(Exception):
    """服务错误"""
    
    def __init__(self, message: str, dump: Optional[ServiceDump] = None):
        super().__init__(message)
        self.dump = dump


class Service:
    """
    AI服务层
    
    提供定位、提取、描述等AI服务
    """
    
    def __init__(
        self,
        context: UIContext | Callable[[], UIContext],
        ai_vendor_fn: Optional[Callable] = None,
        task_info: Optional[dict[str, Any]] = None,
    ):
        if callable(context):
            self._context_retriever_fn = context
        else:
            self._context_retriever_fn = lambda: context
        
        self._ai_vendor_fn = ai_vendor_fn or call_ai_with_object_response
        self._task_info = task_info
    
    async def _get_context(self) -> UIContext:
        """获取UI上下文"""
        result = self._context_retriever_fn()
        if hasattr(result, '__await__'):
            return await result
        return result
    
    async def locate(
        self,
        query: str | dict[str, Any],
        model_config: ModelConfig,
        context: Optional[UIContext] = None,
    ) -> dict[str, Any]:
        """
        定位元素
        
        Args:
            query: 查询字符串或详细参数
            model_config: 模型配置
            context: 可选的UI上下文
        
        Returns:
            {"element": LocateResultElement或None, "rect": Rect, "dump": ServiceDump}
        """
        query_prompt = query if isinstance(query, str) else query.get("prompt", "")
        assert_condition(query_prompt, "query is required for locate")
        
        if context is None:
            context = await self._get_context()
        
        import time
        start_time = time.time()
        
        # 构建消息
        system_prompt = system_prompt_to_locate_element()
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": context.screenshot_base64,
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": f"Please locate: {query_prompt}",
                    },
                ],
            },
        ]
        
        # 调用AI
        result = await self._ai_vendor_fn(
            messages,
            "locate",
            model_config,
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        # 解析结果
        parse_result = result["content"]
        elements = parse_result.get("elements", [])
        errors = parse_result.get("errors", [])
        
        # 构建任务信息
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response=result.get("content_string"),
            usage=result.get("usage"),
        )
        
        # 构建Dump
        error_log = None
        if errors:
            error_log = f"failed to locate element: \n" + "\n".join(errors)
        
        dump = ServiceDump(
            log_time=int(time.time() * 1000),
            type="locate",
            log_id=uuid(),
            user_query={"element": query_prompt},
            matched_element=[],
            data=None,
            task_info=task_info,
            error=error_log,
        )
        
        if error_log:
            raise ServiceError(error_log, dump)
        
        if len(elements) > 1:
            raise ServiceError(
                f"locate: multiple elements found, length = {len(elements)}",
                dump
            )
        
        if elements:
            element = elements[0]
            bbox = element.get("bbox", [0, 0, 0, 0])
            return {
                "element": {
                    "center": (
                        bbox[0] + bbox[2] // 2,
                        bbox[1] + bbox[3] // 2
                    ),
                    "rect": Rect(
                        left=bbox[0],
                        top=bbox[1],
                        width=bbox[2],
                        height=bbox[3],
                    ),
                    "description": element.get("description", ""),
                },
                "rect": None,
                "dump": dump,
            }
        
        return {
            "element": None,
            "rect": None,
            "dump": dump,
        }
    
    async def extract(
        self,
        data_demand: str | dict[str, Any],
        model_config: ModelConfig,
        dom_included: bool = False,
        screenshot_included: bool = True,
        page_description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        提取数据
        
        Args:
            data_demand: 数据需求
            model_config: 模型配置
            dom_included: 是否包含DOM
            screenshot_included: 是否包含截图
            page_description: 页面描述
        
        Returns:
            {"data": Any, "thought": str, "usage": AIUsageInfo, "dump": ServiceDump}
        """
        context = await self._get_context()
        
        import time
        start_time = time.time()
        
        # 构建消息
        system_prompt = system_prompt_to_extract_data()
        
        user_content = []
        if screenshot_included:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": context.screenshot_base64,
                    "detail": "high",
                },
            })
        
        demand_str = str(data_demand)
        user_content.append({
            "type": "text",
            "text": f"Please extract: {demand_str}",
        })
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        
        # 调用AI
        result = await self._ai_vendor_fn(
            messages,
            "extract",
            model_config,
        )
        
        time_cost = int((time.time() - start_time) * 1000)
        
        # 解析结果
        parse_result = result["content"]
        data = parse_result.get("data")
        thought = parse_result.get("thought", "")
        errors = parse_result.get("errors", [])
        
        # 构建任务信息
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response=result.get("content_string"),
            usage=result.get("usage"),
        )
        
        # 构建Dump
        error_log = None
        if errors:
            error_log = f"AI response error: \n" + "\n".join(errors)
        
        dump = ServiceDump(
            log_time=int(time.time() * 1000),
            type="extract",
            log_id=uuid(),
            user_query={"dataDemand": data_demand},
            matched_element=[],
            data=data,
            task_info=task_info,
            error=error_log,
        )
        
        if error_log and not data:
            raise ServiceError(error_log, dump)
        
        return {
            "data": data,
            "thought": thought,
            "usage": result.get("usage"),
            "dump": dump,
        }
    
    async def describe(
        self,
        target: Rect | tuple[int, int],
        model_config: ModelConfig,
        deep_think: bool = False,
    ) -> dict[str, Any]:
        """
        描述元素
        
        Args:
            target: 目标位置（矩形或中心点）
            model_config: 模型配置
            deep_think: 是否深度思考
        
        Returns:
            {"description": str}
        """
        assert_condition(target, "target is required for describe")
        
        context = await self._get_context()
        screenshot = context.screenshot_base64
        
        # 如果是点，转换为矩形
        default_rect_size = 30
        if isinstance(target, tuple):
            target_rect = Rect(
                left=int(target[0] - default_rect_size / 2),
                top=int(target[1] - default_rect_size / 2),
                width=default_rect_size,
                height=default_rect_size,
            )
        else:
            target_rect = target
        
        # 如果深度思考，裁剪图像
        image_payload = screenshot
        if deep_think:
            # 扩展搜索区域
            crop_result = await crop_by_rect(screenshot, target_rect)
            image_payload = crop_result["imageBase64"]
        
        # 构建消息
        system_prompt = element_describer_instruction()
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
        
        # 调用AI
        result = await self._ai_vendor_fn(
            messages,
            "describe",
            model_config,
        )
        
        content = result["content"]
        description = content.get("description", "")
        error = content.get("error")
        
        assert_condition(not error, f"describe failed: {error}")
        assert_condition(description, "failed to describe the element")
        
        return {"description": description}
