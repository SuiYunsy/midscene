"""
Service服务层

对应TypeScript源码: packages/core/src/service/index.ts
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
import time
import uuid

from mspy.shared.types import Rect, LocateResultElement, AIUsageInfo
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition
from mspy.shared.env import IModelConfig
from mspy.core.types import (
    UIContext,
    ServiceDump,
    ServiceError,
    ServiceTaskInfo,
    LocateResultWithDump,
    ServiceExtractResult,
)

debug = get_debug('ai:service')

T = TypeVar('T')


@dataclass
class LocateOpts:
    """定位选项"""
    context: Optional[UIContext] = None


@dataclass
class DetailedLocateParam:
    """详细定位参数"""
    prompt: str
    deep_think: bool = False


@dataclass
class ServiceExtractOption:
    """服务提取选项"""
    dom_included: bool = False
    screenshot_included: bool = True


def create_service_dump(
    dump_type: str,
    user_query: Dict[str, Any],
    matched_element: List[LocateResultElement],
    data: Any = None,
    task_info: Optional[ServiceTaskInfo] = None,
    error: Optional[str] = None,
    matched_rect: Optional[Rect] = None,
    deep_think: bool = False,
) -> ServiceDump:
    """创建服务Dump对象"""
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


class Service:
    """AI服务类
    
    提供元素定位、数据提取、断言等AI驱动的功能
    """
    
    def __init__(
        self,
        context: Union[UIContext, Callable[[], UIContext]],
        ai_vendor_fn: Optional[Callable] = None,
        task_info: Optional[ServiceTaskInfo] = None,
    ):
        """初始化Service
        
        Args:
            context: UI上下文对象或获取上下文的函数
            ai_vendor_fn: AI调用函数（可选，用于测试）
            task_info: 任务信息（可选）
        """
        assert_condition(context, "context is required for Service")
        
        if callable(context):
            self._context_retriever_fn = context
        else:
            self._context_retriever_fn = lambda: context
        
        self._ai_vendor_fn = ai_vendor_fn
        self._task_info = task_info
    
    async def _get_context(self) -> UIContext:
        """获取UI上下文"""
        result = self._context_retriever_fn()
        if hasattr(result, '__await__'):
            return await result
        return result
    
    async def locate(
        self,
        query: Union[str, DetailedLocateParam],
        opts: Optional[LocateOpts] = None,
        model_config: Optional[IModelConfig] = None,
    ) -> LocateResultWithDump:
        """定位元素
        
        使用AI模型在页面上定位符合描述的元素
        
        Args:
            query: 元素描述字符串或详细定位参数
            opts: 定位选项
            model_config: 模型配置
            
        Returns:
            带Dump的定位结果
        """
        # 解析查询参数
        if isinstance(query, str):
            query_prompt = query
            deep_think = False
        else:
            query_prompt = query.prompt
            deep_think = query.deep_think
        
        assert_condition(query_prompt, "query is required for locate")
        
        # 获取上下文
        context = opts.context if opts and opts.context else await self._get_context()
        
        start_time = time.time()
        
        elements = []
        rect = None
        raw_response = "{}"
        usage = None
        error_msg = None
        
        try:
            # 调用AI模型进行定位
            from mspy.core.ai_model.service_caller import (
                call_ai_with_object_response,
                build_vision_message,
            )
            from mspy.core.ai_model.prompt import (
                system_prompt_to_locate_element,
                find_element_prompt,
            )
            from mspy.core.ai_model.types import AIActionType
            
            if model_config and model_config.openai_api_key:
                # 构建消息
                system_prompt = system_prompt_to_locate_element(model_config.vl_mode)
                user_prompt = find_element_prompt(query_prompt)
                
                messages = build_vision_message(
                    system_prompt,
                    user_prompt,
                    context.screenshot_base64
                )
                
                # 调用AI
                result = await call_ai_with_object_response(
                    messages,
                    AIActionType.LOCATE_ELEMENT,
                    model_config,
                    {"type": "json_object"}
                )
                
                raw_response = result.get('raw_response', '{}')
                usage = result.get('usage')
                content = result.get('content', {})
                
                # 解析定位结果
                bbox = content.get('bbox', [])
                errors = content.get('errors', [])
                
                if bbox and len(bbox) == 4:
                    # 计算矩形和中心点
                    xmin, ymin, xmax, ymax = bbox
                    rect = Rect(
                        left=xmin,
                        top=ymin,
                        width=xmax - xmin,
                        height=ymax - ymin
                    )
                    center = (
                        int(xmin + (xmax - xmin) / 2),
                        int(ymin + (ymax - ymin) / 2)
                    )
                    
                    element = LocateResultElement(
                        description=query_prompt,
                        center=center,
                        rect=rect
                    )
                    elements.append(element)
                
                if errors:
                    error_msg = '; '.join(errors)
            else:
                debug("未配置AI模型API密钥，无法进行定位")
                error_msg = "MIDSCENE_MODEL_API_KEY not configured"
                
        except Exception as e:
            debug(f"AI定位失败: {e}")
            error_msg = str(e)
        
        time_cost = int((time.time() - start_time) * 1000)
        
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response=raw_response,
            usage=usage,
        )
        
        # 创建Dump
        dump = create_service_dump(
            dump_type="locate",
            user_query={"element": query_prompt},
            matched_element=elements,
            matched_rect=rect,
            task_info=task_info,
            deep_think=deep_think,
            error=error_msg,
        )
        
        if len(elements) > 1:
            raise ServiceError(
                f"locate: 找到多个元素, 数量 = {len(elements)}",
                dump
            )
        
        if len(elements) == 1:
            return LocateResultWithDump(
                element=elements[0],
                rect=rect,
                dump=dump,
            )
        
        return LocateResultWithDump(
            element=None,
            rect=rect,
            dump=dump,
        )
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: Optional[IModelConfig] = None,
        opts: Optional[ServiceExtractOption] = None,
        page_description: Optional[str] = None,
    ) -> ServiceExtractResult:
        """提取数据
        
        使用AI模型从页面提取结构化数据
        
        Args:
            data_demand: 数据需求描述
            model_config: 模型配置
            opts: 提取选项
            page_description: 页面描述
            
        Returns:
            提取结果
        """
        assert_condition(
            isinstance(data_demand, (str, dict)),
            f"data_demand should be object or string, but got {type(data_demand)}"
        )
        
        context = await self._get_context()
        start_time = time.time()
        
        data = {}
        thought = None
        usage = None
        raw_response = "{}"
        error_msg = None
        
        try:
            from mspy.core.ai_model.service_caller import (
                call_ai_with_object_response,
                build_vision_message,
            )
            from mspy.core.ai_model.prompt import (
                system_prompt_to_extract,
                extract_data_query_prompt,
            )
            from mspy.core.ai_model.types import AIActionType
            
            if model_config and model_config.openai_api_key:
                # 构建页面描述
                if not page_description:
                    page_description = f"Page size: {context.size.width}x{context.size.height}"
                
                # 构建消息
                system_prompt = system_prompt_to_extract()
                user_prompt = extract_data_query_prompt(page_description, data_demand)
                
                messages = build_vision_message(
                    system_prompt,
                    user_prompt,
                    context.screenshot_base64
                )
                
                # 调用AI
                result = await call_ai_with_object_response(
                    messages,
                    AIActionType.EXTRACT_DATA,
                    model_config,
                    {"type": "json_object"}
                )
                
                raw_response = result.get('raw_response', '{}')
                usage = result.get('usage')
                content = result.get('content', {})
                
                data = content.get('data', {})
                thought = content.get('thought')
                errors = content.get('errors', [])
                
                if errors:
                    error_msg = '; '.join(errors)
            else:
                debug("未配置AI模型API密钥，无法进行数据提取")
                error_msg = "MIDSCENE_MODEL_API_KEY not configured"
                
        except Exception as e:
            debug(f"AI数据提取失败: {e}")
            error_msg = str(e)
        
        time_cost = int((time.time() - start_time) * 1000)
        
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response=raw_response,
            usage=usage,
        )
        
        dump = create_service_dump(
            dump_type="extract",
            user_query={"dataDemand": data_demand},
            matched_element=[],
            data=data,
            task_info=task_info,
            error=error_msg,
        )
        
        return ServiceExtractResult(
            data=data,
            thought=thought,
            usage=usage,
            dump=dump,
        )
    
    async def do_assert(
        self,
        assertion: str,
        model_config: Optional[IModelConfig] = None,
    ) -> Dict[str, Any]:
        """执行断言
        
        使用AI模型验证页面是否满足断言条件
        
        Args:
            assertion: 断言描述
            model_config: 模型配置
            
        Returns:
            断言结果 {passed: bool, thought: str}
        """
        assert_condition(assertion, "assertion is required")
        
        context = await self._get_context()
        start_time = time.time()
        
        passed = False
        thought = None
        
        try:
            from mspy.core.ai_model.service_caller import (
                call_ai_with_object_response,
                build_vision_message,
            )
            from mspy.core.ai_model.prompt.assertion import system_prompt_to_assert
            from mspy.core.ai_model.types import AIActionType
            
            if model_config and model_config.openai_api_key:
                system_prompt = system_prompt_to_assert()
                user_prompt = f"Assertion to verify: {assertion}"
                
                messages = build_vision_message(
                    system_prompt,
                    user_prompt,
                    context.screenshot_base64
                )
                
                result = await call_ai_with_object_response(
                    messages,
                    AIActionType.ASSERT,
                    model_config,
                    {"type": "json_object"}
                )
                
                content = result.get('content', {})
                passed = content.get('pass', False)
                thought = content.get('thought', '')
            else:
                debug("未配置AI模型API密钥，无法进行断言")
                thought = "MIDSCENE_MODEL_API_KEY not configured"
                
        except Exception as e:
            debug(f"AI断言失败: {e}")
            thought = str(e)
        
        return {
            'passed': passed,
            'thought': thought,
        }
    
    async def describe(
        self,
        target: Union[Rect, tuple],
        model_config: Optional[IModelConfig] = None,
        opts: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """描述元素
        
        使用AI模型描述指定位置的元素
        
        Args:
            target: 目标位置（矩形区域或中心点坐标）
            model_config: 模型配置
            opts: 选项（如deep_think）
            
        Returns:
            包含description字段的字典
        """
        assert_condition(target, "target is required for service.describe")
        
        context = await self._get_context()
        screenshot_base64 = context.screenshot_base64
        
        assert_condition(screenshot_base64, "screenshot is required for service.describe")
        
        try:
            from mspy.core.ai_model.service_caller import (
                call_ai_with_object_response,
                build_vision_message,
            )
            from mspy.core.ai_model.prompt import element_describer_instruction
            from mspy.core.ai_model.types import AIActionType
            
            if model_config and model_config.openai_api_key:
                system_prompt = element_describer_instruction()
                
                # 格式化目标位置
                if isinstance(target, tuple):
                    user_prompt = f"Describe the element at position ({target[0]}, {target[1]})"
                else:
                    user_prompt = f"Describe the element in the rectangle: left={target.left}, top={target.top}, width={target.width}, height={target.height}"
                
                messages = build_vision_message(
                    system_prompt,
                    user_prompt,
                    screenshot_base64
                )
                
                result = await call_ai_with_object_response(
                    messages,
                    AIActionType.DESCRIBE_ELEMENT,
                    model_config,
                    {"type": "json_object"}
                )
                
                content = result.get('content', {})
                return {
                    "description": content.get('description', ''),
                    "error": content.get('error')
                }
            else:
                return {"description": "", "error": "MIDSCENE_MODEL_API_KEY not configured"}
                
        except Exception as e:
            debug(f"AI描述失败: {e}")
            return {"description": "", "error": str(e)}
