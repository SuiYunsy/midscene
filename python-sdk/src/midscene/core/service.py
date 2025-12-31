"""Service class for AI operations."""

import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from midscene.shared.logger import get_logger
from midscene.shared.utils import assert_condition, uuid
from midscene.core.types import (
    AIUsageInfo,
    DetailedLocateParam,
    LocateResult,
    LocateResultElement,
    Rect,
    ServiceDump,
    ServiceError,
    ServiceExtractOption,
    ServiceTaskInfo,
    UIContext,
)

logger = get_logger("service")

T = TypeVar("T")


class Service:
    """Service class for AI-powered UI operations."""
    
    def __init__(
        self,
        context: Union[UIContext, Callable[[], UIContext]],
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the service.
        
        Args:
            context: UI context or function that returns it
            options: Service options
        """
        assert_condition(context, "context is required for Service")
        
        if callable(context):
            self._context_retriever = context
        else:
            self._context_retriever = lambda: context
        
        self._options = options or {}
        self._task_info = self._options.get("task_info")
    
    async def get_context(self) -> UIContext:
        """Get the UI context."""
        context = self._context_retriever()
        if hasattr(context, "__await__"):
            return await context
        return context
    
    async def locate(
        self,
        query: Union[str, DetailedLocateParam],
        model_config: Dict[str, Any],
        context: Optional[UIContext] = None,
    ) -> LocateResult:
        """
        Locate an element on the page.
        
        Args:
            query: Element description or detailed locate param
            model_config: Model configuration
            context: Optional UI context override
            
        Returns:
            LocateResult with found element
        """
        if isinstance(query, str):
            query_prompt = query
            deep_think = False
        else:
            query_prompt = query.prompt
            deep_think = query.deep_think
        
        assert_condition(query_prompt, "query is required for locate")
        
        ctx = context or await self.get_context()
        
        start_time = time.time()
        
        # Call AI to locate element
        # This is a placeholder - actual implementation would call the AI model
        from midscene.core.ai_model import locate_element
        
        result = await locate_element(
            context=ctx,
            target_description=query_prompt,
            model_config=model_config,
            deep_think=deep_think,
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        task_info = ServiceTaskInfo(
            duration_ms=duration_ms,
            raw_response=result.get("raw_response"),
            usage=result.get("usage"),
        )
        
        if result.get("error"):
            raise ServiceError(
                f"Failed to locate element: {result['error']}",
                dump=ServiceDump(
                    log_time=int(time.time() * 1000),
                    log_id=uuid(),
                    type="locate",
                    user_query={"element": query_prompt},
                    error=result["error"],
                    task_info=task_info,
                ),
            )
        
        element = result.get("element")
        if element:
            return LocateResult(
                element=LocateResultElement(
                    description=element.get("description", ""),
                    center=element.get("center", (0, 0)),
                    rect=element.get("rect"),
                ),
            )
        
        return LocateResult(element=None)
    
    async def extract(
        self,
        data_demand: Union[str, Dict[str, str]],
        model_config: Dict[str, Any],
        options: Optional[ServiceExtractOption] = None,
    ) -> Dict[str, Any]:
        """
        Extract data from the page.
        
        Args:
            data_demand: Data extraction query
            model_config: Model configuration
            options: Extraction options
            
        Returns:
            Extracted data
        """
        ctx = await self.get_context()
        
        from midscene.core.ai_model import extract_data
        
        result = await extract_data(
            context=ctx,
            data_query=data_demand,
            model_config=model_config,
            options=options,
        )
        
        if result.get("error"):
            raise ServiceError(f"Failed to extract data: {result['error']}")
        
        return {
            "data": result.get("data"),
            "thought": result.get("thought"),
            "usage": result.get("usage"),
        }
    
    async def describe(
        self,
        target: Union[tuple, Rect],
        model_config: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Describe an element at a position.
        
        Args:
            target: Target position or rect
            model_config: Model configuration
            options: Description options
            
        Returns:
            Description result
        """
        ctx = await self.get_context()
        
        from midscene.core.ai_model import describe_element
        
        result = await describe_element(
            context=ctx,
            target=target,
            model_config=model_config,
            deep_think=options.get("deep_think", False) if options else False,
        )
        
        assert_condition(
            result.get("description"),
            "Failed to describe the element"
        )
        
        return {"description": result["description"]}
