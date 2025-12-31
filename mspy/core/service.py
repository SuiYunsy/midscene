"""Service：封装定位与数据抽取逻辑。"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

from .ai_model.prompt.assertion import ASSERT_SCHEMA
from .ai_model.service_caller import call_ai_with_object_response
from .types import LocateResult, UIContext
from ..shared.logger import get_logger
from ..shared.utils import assert_true
from ..shared.env import ModelConfig

logger = get_logger("service")


class Service:
    def __init__(
        self,
        context_provider: Callable[[], UIContext],
    ) -> None:
        self.context_provider = context_provider

    def _context(self) -> UIContext:
        ctx = self.context_provider()
        assert_true(ctx and ctx.screenshot_base64, "UI context is required")
        return ctx

    def locate(
        self, query: str, model_config: ModelConfig
    ) -> LocateResult:
        """调用模型返回单个元素的 bbox。"""
        ctx = self._context()
        system = {
            "role": "system",
            "content": "Locate the target element in the screenshot and return bbox [xmin,ymin,xmax,ymax] and center.",
        }
        user = {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": ctx.screenshot_base64, "detail": "high"},
                },
            ],
        }

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "locate",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4,
                            "maxItems": 4,
                            "description": "2d bounding box as [xmin, ymin, xmax, ymax]",
                        },
                        "center": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                        "description": {"type": ["string", "null"]},
                    },
                    "required": ["bbox"],
                    "additionalProperties": True,
                },
            },
        }
        result = call_ai_with_object_response(
            [system, user], model_config, response_format=response_format
        )
        content: Dict[str, Any] = result["content"]
        bbox_value = content.get("bbox")
        assert_true(bbox_value, "Model did not return bbox")
        bbox = tuple(bbox_value)  # type: ignore[arg-type]
        center = content.get("center")
        if not center and len(bbox) == 4:
            x1, y1, x2, y2 = bbox  # type: ignore[misc]
            center = ((x1 + x2) / 2, (y1 + y2) / 2)
        assert_true(center is not None, "Failed to locate center point")
        logger.info("Locate result: bbox=%s center=%s", bbox, center)
        return LocateResult(center=center, bbox=bbox, description=content.get("description"))

    def assert_text(
        self, assertion: str, model_config: ModelConfig
    ) -> Tuple[bool, Optional[str]]:
        """基于截图与文本的断言。"""
        ctx = self._context()
        system = {
            "role": "system",
            "content": "You are a vision assertion helper. Judge whether the assertion is correct.",
        }
        user = {
            "role": "user",
            "content": [
                {"type": "text", "text": assertion},
                {
                    "type": "image_url",
                    "image_url": {"url": ctx.screenshot_base64, "detail": "high"},
                },
            ],
        }
        result = call_ai_with_object_response(
            [system, user], model_config, response_format=ASSERT_SCHEMA
        )
        payload: Dict[str, Any] = result["content"]
        passed = bool(payload.get("pass"))
        thought = payload.get("thought")
        logger.info("Assertion evaluated: pass=%s thought=%s", passed, thought)
        return passed, thought if isinstance(thought, str) else None
