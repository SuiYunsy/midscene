"""Abstract interface for device control."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from midscene.shared.types import Size
from midscene.core.types import UIContext


class AbstractInterface(ABC):
    """
    Abstract interface for controlling a device or page.
    
    This is the base class that Playwright, Puppeteer (not supported),
    and other integrations should implement.
    """
    
    @property
    @abstractmethod
    def interface_type(self) -> str:
        """Get the interface type (e.g., 'playwright', 'static')."""
        pass
    
    @abstractmethod
    async def screenshot_base64(self) -> str:
        """
        Take a screenshot and return as base64 string.
        
        Returns:
            Base64 encoded screenshot
        """
        pass
    
    @abstractmethod
    async def size(self) -> Size:
        """
        Get the viewport/screen size.
        
        Returns:
            Size object with width and height
        """
        pass
    
    async def get_context(self) -> UIContext:
        """
        Get the UI context (screenshot + size).
        
        Returns:
            UIContext with current state
        """
        from midscene.core.types import SimpleUIContext
        
        screenshot = await self.screenshot_base64()
        size = await self.size()
        return SimpleUIContext(screenshot_base64=screenshot, size=size)
    
    @abstractmethod
    async def mouse_click(
        self,
        x: float,
        y: float,
        button: str = "left",
        click_count: int = 1,
    ) -> None:
        """
        Click at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button ('left', 'right', 'middle')
            click_count: Number of clicks (1 for single, 2 for double)
        """
        pass
    
    @abstractmethod
    async def mouse_move(self, x: float, y: float) -> None:
        """
        Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        pass
    
    @abstractmethod
    async def mouse_wheel(
        self,
        x: float,
        y: float,
        delta_x: float = 0,
        delta_y: float = 0,
    ) -> None:
        """
        Scroll at coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            delta_x: Horizontal scroll amount
            delta_y: Vertical scroll amount
        """
        pass
    
    @abstractmethod
    async def keyboard_type(self, text: str) -> None:
        """
        Type text.
        
        Args:
            text: Text to type
        """
        pass
    
    @abstractmethod
    async def keyboard_press(self, key: str) -> None:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Tab', 'Escape')
        """
        pass
    
    def action_space(self) -> List[Dict[str, Any]]:
        """
        Get the action space for this interface.
        
        Returns:
            List of available actions
        """
        return [
            {"name": "Tap", "description": "Click on an element"},
            {"name": "DoubleClick", "description": "Double click on an element"},
            {"name": "RightClick", "description": "Right click on an element"},
            {"name": "Hover", "description": "Hover over an element"},
            {"name": "Input", "description": "Type text into an element"},
            {"name": "KeyboardPress", "description": "Press a keyboard key"},
            {"name": "Scroll", "description": "Scroll the page"},
        ]
    
    async def destroy(self) -> None:
        """Clean up resources."""
        pass
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        Evaluate JavaScript in the page context.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of the script execution
            
        Raises:
            NotImplementedError: If not supported by this interface
        """
        raise NotImplementedError(
            "evaluate_javascript is not supported by this interface"
        )
