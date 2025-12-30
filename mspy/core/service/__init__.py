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
        
        # TODO: 实际调用AI模型进行定位
        # 这里先返回模拟结果，实际实现需要调用AI模型
        elements = []
        rect = None
        raw_response = "{}"
        usage = None
        
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
        
        # TODO: 实际调用AI模型进行数据提取
        # 这里先返回模拟结果
        data = {}
        thought = None
        usage = None
        
        time_cost = int((time.time() - start_time) * 1000)
        
        task_info = ServiceTaskInfo(
            duration_ms=time_cost,
            raw_response="{}",
        )
        
        dump = create_service_dump(
            dump_type="extract",
            user_query={"dataDemand": data_demand},
            matched_element=[],
            data=data,
            task_info=task_info,
        )
        
        return ServiceExtractResult(
            data=data,
            thought=thought,
            usage=usage,
            dump=dump,
        )
    
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
        
        # TODO: 实际调用AI模型进行描述
        # 这里先返回模拟结果
        return {"description": "元素描述"}
