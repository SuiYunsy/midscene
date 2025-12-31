"""Static page implementation for testing without browser."""

import base64
from pathlib import Path
from typing import Any, List, Optional

from PIL import Image
import io

from midscene.shared.types import Size
from midscene.core.device import AbstractInterface
from midscene.core.agent import Agent
from midscene.core.types import AgentOpt


class StaticPage(AbstractInterface):
    """
    A static page implementation for testing.
    
    This allows testing Midscene with a static image instead of a live browser.
    Useful for unit tests and demonstrations.
    """
    
    def __init__(
        self,
        screenshot_path: Optional[str] = None,
        screenshot_base64_data: Optional[str] = None,
        size: Optional[Size] = None,
    ):
        """
        Initialize static page.
        
        Args:
            screenshot_path: Path to screenshot image file
            screenshot_base64_data: Base64 encoded screenshot
            size: Page size (if not provided, will be inferred from image)
        """
        if screenshot_path:
            with open(screenshot_path, "rb") as f:
                self._screenshot_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Infer size from image
            image = Image.open(screenshot_path)
            self._size = size or Size(width=image.width, height=image.height)
        elif screenshot_base64_data:
            self._screenshot_base64 = screenshot_base64_data
            
            # Infer size from image
            image_data = base64.b64decode(screenshot_base64_data)
            image = Image.open(io.BytesIO(image_data))
            self._size = size or Size(width=image.width, height=image.height)
        else:
            raise ValueError("Either screenshot_path or screenshot_base64_data is required")
    
    @property
    def interface_type(self) -> str:
        """Get the interface type."""
        return "static"
    
    async def screenshot_base64(self) -> str:
        """Get the screenshot as base64."""
        return self._screenshot_base64
    
    async def size(self) -> Size:
        """Get the page size."""
        return self._size
    
    async def mouse_click(
        self,
        x: float,
        y: float,
        button: str = "left",
        click_count: int = 1,
    ) -> None:
        """Click (no-op for static page)."""
        pass
    
    async def mouse_move(self, x: float, y: float) -> None:
        """Move mouse (no-op for static page)."""
        pass
    
    async def mouse_wheel(
        self,
        x: float,
        y: float,
        delta_x: float = 0,
        delta_y: float = 0,
    ) -> None:
        """Scroll (no-op for static page)."""
        pass
    
    async def keyboard_type(self, text: str) -> None:
        """Type text (no-op for static page)."""
        pass
    
    async def keyboard_press(self, key: str) -> None:
        """Press key (no-op for static page)."""
        pass
    
    def action_space(self) -> List[dict]:
        """Static pages have limited action space."""
        return [
            {"name": "Locate", "description": "Find an element"},
            {"name": "Query", "description": "Extract data from the page"},
        ]


class StaticPageAgent(Agent[StaticPage]):
    """
    Agent for static pages.
    
    Useful for testing AI capabilities without a browser.
    """
    
    def __init__(
        self,
        screenshot_path: Optional[str] = None,
        screenshot_base64: Optional[str] = None,
        size: Optional[Size] = None,
        opts: Optional[AgentOpt] = None,
    ):
        """
        Initialize static page agent.
        
        Args:
            screenshot_path: Path to screenshot image
            screenshot_base64: Base64 encoded screenshot
            size: Page size
            opts: Agent options
        """
        page = StaticPage(
            screenshot_path=screenshot_path,
            screenshot_base64_data=screenshot_base64,
            size=size,
        )
        super().__init__(page, opts)
