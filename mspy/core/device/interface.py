"""
抽象设备接口

从 packages/core/src/device/index.ts 迁移
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from mspy.core.types import DeviceAction, UIContext
from mspy.shared.types import Rect, Size


class AbstractInterface(ABC):
    """抽象设备接口基类"""
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """接口类型标识"""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """获取屏幕截图的Base64编码"""
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """获取屏幕/页面尺寸"""
        pass
    
    @abstractmethod
    def action_space(self) -> list[DeviceAction]:
        """获取支持的动作空间"""
        pass
    
    async def get_context(self) -> UIContext:
        """
        获取UI上下文
        
        默认实现：截图 + 尺寸
        子类可以重写以提供更多信息
        """
        screenshot = await self.screenshot_base64()
        size = await self.size()
        
        return UIContext(
            screenshot_base64=screenshot,
            size=size,
        )
    
    async def cache_feature_for_rect(
        self,
        rect: Rect,
        options: Optional[dict[str, Any]] = None
    ) -> Any:
        """
        为矩形区域获取缓存特征
        
        子类可选实现
        """
        raise NotImplementedError("cache_feature_for_rect not implemented")
    
    async def rect_matches_cache_feature(
        self,
        feature: Any
    ) -> Optional[Rect]:
        """
        检查特征是否匹配某个矩形
        
        子类可选实现
        """
        raise NotImplementedError("rect_matches_cache_feature not implemented")
    
    async def destroy(self) -> None:
        """
        销毁接口资源
        
        子类可选实现
        """
        pass
    
    def describe(self) -> str:
        """
        获取接口描述
        
        子类可选实现
        """
        return f"AbstractInterface({self.interface_type})"
    
    async def before_invoke_action(
        self,
        action_name: str,
        param: Any
    ) -> None:
        """
        动作执行前的钩子
        
        子类可选实现
        """
        pass
    
    async def after_invoke_action(
        self,
        action_name: str,
        param: Any
    ) -> None:
        """
        动作执行后的钩子
        
        子类可选实现
        """
        pass
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        执行JavaScript脚本
        
        仅Web接口实现
        """
        raise NotImplementedError("evaluate_javascript not supported")
    
    async def url(self) -> str:
        """
        获取当前URL
        
        仅Web接口实现
        """
        raise NotImplementedError("url not supported")
