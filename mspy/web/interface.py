"""抽象接口定义"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, List, Optional
from ..core.types import DeviceAction, Size

class AbstractInterface(ABC):
    """抽象页面接口 - 所有页面类型必须实现"""
    interface_type: str = "abstract"
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """获取当前页面截图的base64字符串"""
        pass
    @abstractmethod
    async def size(self) -> Size:
        """获取页面尺寸"""
        pass
    @abstractmethod
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作列表"""
        pass
    @abstractmethod
    async def destroy(self) -> None:
        """销毁接口，释放资源"""
        pass
    async def url(self) -> str:
        """获取当前URL"""
        return ""
    async def before_action(self, action_name: str, param: Any) -> None:
        """动作执行前钩子"""
        pass
    async def after_action(self, action_name: str, param: Any) -> None:
        """动作执行后钩子"""
        pass
