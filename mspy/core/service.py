"""
Service - 服务模块
提供 AI 服务接口
"""

import time
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable

from mspy.shared.types import (
    AIAssertionResponse,
    AIUsageInfo,
    IModelConfig,
    LocateResultElement,
    Rect,
    Size,
    UIContext,
)
from mspy.shared.logger import get_debug
from mspy.shared.utils import assert_condition, uuid
from mspy.core.types import ServiceDump, ServiceTaskInfo
from mspy.core.ai_model import call_ai_with_object_response
from mspy.core.prompts import ASSERT_SCHEMA


debug = get_debug("service")


class Service:
    """
    AI 服务类
    提供断言、定位等 AI 服务
    """
    
    def __init__(
        self,
        context_getter: Callable[[], Awaitable["UIContext"]],
    ):
        """
        初始化服务
        
        Args:
            context_getter: UI 上下文获取函数
        """
        self._context_getter = context_getter
    
    async def _get_context(self) -> "UIContext":
        """获取 UI 上下文"""
        return await self._context_getter()
    
    async def assert_condition(
        self,
        assertion: str,
        model_config: IModelConfig,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行断言
        
        Args:
            assertion: 断言文本
            model_config: 模型配置
            options: 可选配置
            
        Returns:
            包含 passed, thought, usage, dump 的字典
        """
        debug("assert_condition:", assertion)
        start_time = time.time()
        log_id = uuid()
        
        context = await self._get_context()
        
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant that helps verify assertions about UI screenshots.
                
Given a screenshot and an assertion statement, analyze the screenshot and determine if the assertion is true or false.

You must respond in JSON format with the following structure:
{
    "pass": boolean,  // true if the assertion passes, false otherwise
    "thought": string  // your reasoning for the decision
}

Be precise and base your decision only on what you can observe in the screenshot.""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Please verify the following assertion based on the screenshot:\n\n{assertion}",
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
            response = call_ai_with_object_response(messages, model_config)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            result = response["content"]
            usage = response.get("usage")
            
            passed = result.get("pass", False)
            thought = result.get("thought", "")
            
            # 构建 dump
            dump = ServiceDump(
                type="assert",
                log_id=log_id,
                log_time=int(time.time() * 1000),
                user_query={"assertion": assertion},
                matched_element=[],
                assertion_pass=passed,
                assertion_thought=thought,
                task_info=ServiceTaskInfo(
                    duration_ms=duration_ms,
                    raw_response=response.get("content_string"),
                ),
            )
            
            return {
                "passed": passed,
                "thought": thought,
                "usage": usage,
                "dump": dump,
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            dump = ServiceDump(
                type="assert",
                log_id=log_id,
                log_time=int(time.time() * 1000),
                user_query={"assertion": assertion},
                matched_element=[],
                error=str(e),
                task_info=ServiceTaskInfo(duration_ms=duration_ms),
            )
            
            raise RuntimeError(f"Assertion failed: {e}") from e
    
    async def describe(
        self,
        center: tuple[float, float],
        model_config: IModelConfig,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        描述指定位置的元素
        
        Args:
            center: 中心坐标 (x, y)
            model_config: 模型配置
            options: 可选配置
            
        Returns:
            包含 description 的字典
        """
        debug("describe at:", center)
        
        context = await self._get_context()
        deep_think = options.get("deepThink", False) if options else False
        
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant that describes UI elements at specific coordinates.

Given a screenshot and coordinates (x, y), describe the UI element at that location.
Be specific about what the element is (button, text, input field, etc.) and what it contains or represents.

Respond in JSON format:
{
    "description": string  // A clear, concise description of the element
}""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Describe the UI element at coordinates ({center[0]}, {center[1]}).",
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
        
        response = call_ai_with_object_response(messages, model_config)
        result = response["content"]
        
        return {
            "description": result.get("description", ""),
        }
