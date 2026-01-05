"""
设备抽象接口

定义所有设备（Web、移动端等）需要实现的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List, Callable, Awaitable

from mspy.core.types import UIContext, ExecutionTask


class DeviceAction:
    """
    设备操作定义
    
    定义设备可执行的单个操作。
    """
    
    def __init__(
        self,
        name: str,
        call: Callable[..., Awaitable[Any]],
        description: Optional[str] = None,
        interface_alias: Optional[str] = None,
        param_schema: Optional[Any] = None,
        delay_after_runner: Optional[int] = None,
    ):
        """
        初始化设备操作
        
        Args:
            name: 操作名称
            call: 操作执行函数
            description: 操作描述
            interface_alias: 接口别名（用于YAML）
            param_schema: 参数schema（Pydantic模型）
            delay_after_runner: 操作后延迟时间（毫秒）
        """
        self.name = name
        self.call = call
        self.description = description
        self.interface_alias = interface_alias
        self.param_schema = param_schema
        self.delay_after_runner = delay_after_runner


class AbstractInterface(ABC):
    """
    抽象设备接口
    
    所有设备（如Playwright页面、Android设备等）需要实现此接口。
    """
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """设备类型标识"""
        ...
    
    @abstractmethod
    def action_space(self) -> List[DeviceAction]:
        """
        获取设备支持的操作列表
        
        Returns:
            设备操作列表
        """
        ...
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """
        获取屏幕截图
        
        Returns:
            Base64编码的屏幕截图
        """
        ...
    
    @abstractmethod
    async def size(self) -> dict[str, Any]:
        """
        获取屏幕尺寸
        
        Returns:
            包含width、height的字典
        """
        ...
    
    async def get_context(self) -> Optional[UIContext]:
        """
        获取UI上下文
        
        默认返回None，子类可覆盖此方法。
        
        Returns:
            UI上下文，或None
        """
        return None
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行JavaScript代码
        
        默认抛出异常，只有Web设备需要实现此方法。
        
        Args:
            script: JavaScript代码
            
        Returns:
            执行结果
            
        Raises:
            NotImplementedError: 如果设备不支持JavaScript执行
        """
        raise NotImplementedError(
            "evaluateJavaScript is not supported in current device"
        )
    
    async def destroy(self) -> None:
        """
        销毁设备实例
        
        释放资源、关闭连接等。
        """
        pass
    
    # 可选的生命周期钩子
    before_invoke_action: Optional[Callable[[ExecutionTask], Awaitable[None]]] = None
    after_invoke_action: Optional[Callable[[ExecutionTask], Awaitable[None]]] = None
