"""Playwright page wrapper implementing AbstractInterface."""

import base64
from typing import Any, Optional

from playwright.async_api import Page

from midscene.shared.types import Size
from midscene.core.device import AbstractInterface


class PlaywrightPage(AbstractInterface):
    """
    Playwright page wrapper implementing AbstractInterface.
    
    This class wraps a Playwright Page object and provides the
    interface methods required by the Midscene Agent.
    """
    
    def __init__(self, page: Page):
        """
        Initialize with a Playwright page.
        
        Args:
            page: Playwright Page instance
        """
        self._page = page
    
    @property
    def interface_type(self) -> str:
        """Get the interface type."""
        return "playwright"
    
    @property
    def page(self) -> Page:
        """Get the underlying Playwright page."""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """
        Take a screenshot and return as base64 string.
        
        Returns:
            Base64 encoded screenshot
        """
        buffer = await self._page.screenshot(type="png")
        return base64.b64encode(buffer).decode("utf-8")
    
    async def size(self) -> Size:
        """
        Get the viewport size.
        
        Returns:
            Size object with width and height
        """
        viewport = self._page.viewport_size
        if viewport:
            return Size(width=viewport["width"], height=viewport["height"])
        
        # Fallback: evaluate in browser
        size = await self._page.evaluate("""() => ({
            width: window.innerWidth,
            height: window.innerHeight
        })""")
        return Size(width=size["width"], height=size["height"])
    
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
            click_count: Number of clicks
        """
        await self._page.mouse.click(
            x, y, 
            button=button,
            click_count=click_count,
        )
    
    async def mouse_move(self, x: float, y: float) -> None:
        """
        Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        await self._page.mouse.move(x, y)
    
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
        await self._page.mouse.move(x, y)
        await self._page.mouse.wheel(delta_x=delta_x, delta_y=delta_y)
    
    async def keyboard_type(self, text: str) -> None:
        """
        Type text.
        
        Args:
            text: Text to type
        """
        await self._page.keyboard.type(text)
    
    async def keyboard_press(self, key: str) -> None:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Tab', 'Escape')
        """
        await self._page.keyboard.press(key)
    
    async def goto(self, url: str, **kwargs) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            **kwargs: Additional arguments passed to page.goto
        """
        await self._page.goto(url, **kwargs)
    
    async def evaluate_javascript(self, script: str) -> Any:
        """
        Evaluate JavaScript in the page context.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result of the script execution
        """
        return await self._page.evaluate(script)
    
    async def wait_for_load_state(
        self, 
        state: str = "load",
        timeout: Optional[float] = None,
    ) -> None:
        """
        Wait for page to reach a load state.
        
        Args:
            state: Load state to wait for ('load', 'domcontentloaded', 'networkidle')
            timeout: Timeout in milliseconds
        """
        await self._page.wait_for_load_state(state, timeout=timeout)
    
    async def destroy(self) -> None:
        """Clean up resources."""
        # Don't close the page - let the user manage it
        pass
