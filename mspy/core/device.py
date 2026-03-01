"""设备接口定义。"""

from __future__ import annotations

from typing import Any, Dict, List

from .types import ActionSpaceItem, UIContext


class AbstractInterface:
    """抽象设备接口，供具体实现继承。"""

    interface_type: str = "abstract"

    def get_context(self) -> UIContext:  # pragma: no cover - 接口定义
        raise NotImplementedError

    def action_space(self) -> List[ActionSpaceItem]:  # pragma: no cover
        raise NotImplementedError

    def perform_action(
        self, action_type: str, param: Dict[str, Any], context: UIContext
    ) -> Any:  # pragma: no cover
        raise NotImplementedError

    def screenshot_base64(self) -> str:  # pragma: no cover
        raise NotImplementedError
