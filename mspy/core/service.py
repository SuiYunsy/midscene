"""
服务模块 - 提供定位和提取等服务
"""

import time
from typing import Any, Callable, Dict, List, Optional, Union

from ..shared import (
    get_debug,
    IModelConfig,
    UIContext,
    ServiceDump,
    ServiceError,
    LocateResultElement,
    LocateResultWithDump,
    Rect,
    AIUsageInfo,
    uuid,
    assert_condition,
)
from .ai_model import call_ai_with_object_response, adapt_bbox

debug = get_debug('ai:service')


def create_service_dump(
    dump_type: str,
    user_query: Dict[str, Any],
    matched_element: List[LocateResultElement],
    matched_rect: Optional[Rect] = None,
    data: Any = None,
    error: Optional[str] = None,
) -> ServiceDump:
    """
    创建服务转储
    
    Args:
        dump_type: 转储类型
        user_query: 用户查询
        matched_element: 匹配的元素
        matched_rect: 匹配的矩形
        data: 数据
        error: 错误信息
    
    Returns:
        ServiceDump实例
    """
    return ServiceDump(
        type=dump_type,
        log_id=uuid(),
        log_time=int(time.time() * 1000),
        user_query=user_query,
        matched_element=matched_element,
        matched_rect=matched_rect,
        data=data,
        error=error,
    )


class Service:
    """AI服务类"""
    
    def __init__(
        self,
        context: Union[UIContext, Callable[[], UIContext]],
    ):
        """
        初始化服务
        
        Args:
            context: UI上下文或返回UI上下文的函数
        """
        assert_condition(context, "context is required for Service")
        
        if callable(context):
            self.context_retriever_fn = context
        else:
            self.context_retriever_fn = lambda: context
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        ctx = self.context_retriever_fn()
        if hasattr(ctx, '__await__'):
            return await ctx
        return ctx
    
    async def locate(
        self,
        query: Union[str, Dict[str, Any]],
        model_config: IModelConfig,
        context: Optional[UIContext] = None,
    ) -> LocateResultWithDump:
        """
        定位元素
        
        Args:
            query: 查询字符串或详细定位参数
            model_config: 模型配置
            context: UI上下文（可选）
        
        Returns:
            LocateResultWithDump实例
        """
        query_prompt = query if isinstance(query, str) else query.get('prompt', '')
        assert_condition(query_prompt, "query is required for locate")
        
        if context is None:
            context = await self.get_context()
        
        vl_mode = model_config.vl_mode
        
        # 构建提示词
        system_prompt = self._build_locate_system_prompt()
        
        # 构建消息
        msgs = [
            {'role': 'system', 'content': system_prompt},
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f'Find the element: {query_prompt}',
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': context.screenshot_base64,
                            'detail': 'high',
                        },
                    },
                ],
            },
        ]
        
        start_time = time.time()
        
        try:
            response = await call_ai_with_object_response(msgs, model_config)
            time_cost = int((time.time() - start_time) * 1000)
            
            parse_result = response['content']
            usage = response.get('usage')
            
            # 解析结果
            elements = []
            rect = None
            
            if parse_result.get('bbox'):
                bbox = parse_result['bbox']
                if vl_mode:
                    bbox = adapt_bbox(
                        bbox,
                        context.size.width,
                        context.size.height,
                        context.size.width,
                        context.size.height,
                        vl_mode
                    )
                
                x1, y1, x2, y2 = bbox
                rect = Rect(
                    left=x1,
                    top=y1,
                    width=x2 - x1,
                    height=y2 - y1,
                )
                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                
                element = LocateResultElement(
                    center=center,
                    rect=rect,
                    description=parse_result.get('text', query_prompt),
                )
                elements.append(element)
            
            # 创建转储
            dump = create_service_dump(
                dump_type='locate',
                user_query={'element': query_prompt},
                matched_element=elements,
                matched_rect=rect,
            )
            
            # 检查错误
            errors = parse_result.get('errors', [])
            if errors:
                error_log = f"Failed to locate element: \n{chr(10).join(errors)}"
                dump.error = error_log
                raise ServiceError(error_log, dump)
            
            if len(elements) > 1:
                raise ServiceError(f"locate: multiple elements found, length = {len(elements)}", dump)
            
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
        
        except ServiceError:
            raise
        except Exception as e:
            dump = create_service_dump(
                dump_type='locate',
                user_query={'element': query_prompt},
                matched_element=[],
                error=str(e),
            )
            raise ServiceError(str(e), dump) from e
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: IModelConfig,
        context: Optional[UIContext] = None,
    ) -> Dict[str, Any]:
        """
        提取数据
        
        Args:
            data_demand: 数据需求
            model_config: 模型配置
            context: UI上下文（可选）
        
        Returns:
            {'data': Any, 'thought': str, 'usage': AIUsageInfo, 'dump': ServiceDump}
        """
        if context is None:
            context = await self.get_context()
        
        # 构建提示词
        system_prompt = self._build_extract_system_prompt(data_demand)
        
        # 构建消息
        msgs = [
            {'role': 'system', 'content': system_prompt},
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': 'Please extract the required information from the screenshot.',
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': context.screenshot_base64,
                            'detail': 'high',
                        },
                    },
                ],
            },
        ]
        
        start_time = time.time()
        
        try:
            response = await call_ai_with_object_response(msgs, model_config)
            time_cost = int((time.time() - start_time) * 1000)
            
            parse_result = response['content']
            usage = response.get('usage')
            
            data = parse_result.get('data', parse_result)
            thought = parse_result.get('thought', '')
            
            dump = create_service_dump(
                dump_type='extract',
                user_query={'dataDemand': data_demand},
                matched_element=[],
                data=data,
            )
            
            errors = parse_result.get('errors', [])
            if errors and not data:
                error_log = f"AI response error: \n{chr(10).join(errors)}"
                raise ServiceError(error_log, dump)
            
            return {
                'data': data,
                'thought': thought,
                'usage': usage,
                'dump': dump,
            }
        
        except ServiceError:
            raise
        except Exception as e:
            dump = create_service_dump(
                dump_type='extract',
                user_query={'dataDemand': data_demand},
                matched_element=[],
                error=str(e),
            )
            raise ServiceError(str(e), dump) from e
    
    def _build_locate_system_prompt(self) -> str:
        """构建定位系统提示词"""
        return '''You are an AI assistant that helps locate elements on a screen.

Given a screenshot and a description of an element, find the element and return its bounding box.

Return format:
{
  "bbox": [xmin, ymin, xmax, ymax],  // coordinates normalized to 0-1000
  "text": "description of the found element",
  "errors": []  // any error messages
}

If the element cannot be found, return:
{
  "errors": ["Element not found: <reason>"]
}
'''
    
    def _build_extract_system_prompt(self, data_demand: Union[str, Dict[str, str]]) -> str:
        """构建提取系统提示词"""
        if isinstance(data_demand, str):
            demand_str = data_demand
        else:
            demand_str = '\n'.join(f"- {k}: {v}" for k, v in data_demand.items())
        
        return f'''You are an AI assistant that helps extract information from screenshots.

Extract the following information from the screenshot:
{demand_str}

Return format:
{{
  "data": <extracted data matching the requested format>,
  "thought": "explanation of how you extracted the data",
  "errors": []  // any error messages
}}

If information cannot be extracted, explain in the errors array.
'''
