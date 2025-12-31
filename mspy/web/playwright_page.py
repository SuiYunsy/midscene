"""
Playwright 网页集成模块
Playwright web page integration module
"""
import asyncio
import base64
import time
from typing import Any, Dict, List, Optional

from playwright.async_api import Page as PlaywrightPage

from ..shared import (
    get_debug,
    assert_condition,
    Size,
    Rect,
    UIContext,
    Point,
    LocateResultElement,
    create_img_base64_by_format,
)

from ..core import (
    AbstractInterface,
    DeviceAction,
    define_action_tap,
    define_action_input,
    define_action_scroll,
    define_action_keyboard_press,
    define_action_hover,
    define_action_right_click,
    define_action_double_click,
    define_action_assert,
)

debug = get_debug("web:page")

# 默认超时配置
DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT = 3000
DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT = 3000


class PlaywrightWebPage(AbstractInterface):
    """
    Playwright web page interface.
    Playwright 网页接口
    """
    
    def __init__(
        self,
        page: PlaywrightPage,
        wait_for_navigation_timeout: int = DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
        wait_for_network_idle_timeout: int = DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
    ):
        self._page = page
        self._wait_for_navigation_timeout = wait_for_navigation_timeout
        self._wait_for_network_idle_timeout = wait_for_network_idle_timeout
        self._viewport_size: Optional[Size] = None
        self._ever_moved = False
    
    @property
    def interface_type(self) -> str:
        return "playwright"
    
    @property
    def underlying_page(self) -> PlaywrightPage:
        """Get the underlying Playwright page."""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """Take a screenshot and return as base64."""
        await self.wait_for_navigation()
        
        debug.debug("Taking screenshot")
        start_time = time.time()
        
        buffer = await self._page.screenshot(
            type="jpeg",
            quality=90,
            timeout=10000,
        )
        
        base64_str = base64.b64encode(buffer).decode("utf-8")
        
        result = create_img_base64_by_format("jpeg", base64_str)
        
        debug.debug(f"Screenshot taken in {int((time.time() - start_time) * 1000)}ms")
        return result
    
    async def size(self) -> Size:
        """Get the viewport size."""
        if self._viewport_size:
            return self._viewport_size
        
        size_info = await self._page.evaluate("""() => {
            return {
                width: document.documentElement.clientWidth,
                height: document.documentElement.clientHeight,
                dpr: window.devicePixelRatio
            }
        }""")
        
        self._viewport_size = Size(
            width=size_info["width"],
            height=size_info["height"],
            dpr=size_info.get("dpr"),
        )
        return self._viewport_size
    
    def action_space(self) -> List[DeviceAction]:
        """Get available actions."""
        return self._build_common_web_actions()
    
    async def wait_for_navigation(self) -> None:
        """
        Wait for navigation to complete.
        等待导航完成
        """
        if self._wait_for_navigation_timeout == 0:
            debug.debug("Wait for navigation timeout is 0, skipping")
            return
        
        debug.debug(f"Waiting for navigation (timeout: {self._wait_for_navigation_timeout}ms)")
        
        try:
            await self._page.wait_for_selector("html", timeout=self._wait_for_navigation_timeout)
        except Exception:
            debug.warning(
                "Waiting for navigation timed out, but Midscene will continue. "
                "See https://midscenejs.com/faq.html#customize-the-network-timeout"
            )
    
    async def wait_for_network_idle(self) -> None:
        """
        Wait for network to become idle.
        等待网络空闲 - 这是非常重要的功能
        """
        if self._wait_for_network_idle_timeout == 0:
            debug.debug("Wait for network idle timeout is 0, skipping")
            return
        
        debug.debug(f"Waiting for network idle (timeout: {self._wait_for_network_idle_timeout}ms)")
        
        try:
            # Playwright 的 wait_for_load_state 方法
            await self._page.wait_for_load_state(
                "networkidle",
                timeout=self._wait_for_network_idle_timeout
            )
            debug.debug("Network is idle")
        except Exception:
            debug.warning(
                "Waiting for network idle timed out, but Midscene will continue. "
                "See https://midscenejs.com/faq.html#customize-the-network-timeout"
            )
    
    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        debug.info(f"Navigating to: {url}")
        await self._page.goto(url)
        await self.wait_for_network_idle()
    
    async def reload(self) -> None:
        """Reload the current page."""
        debug.info("Reloading page")
        await self._page.reload()
        await self.wait_for_network_idle()
    
    async def go_back(self) -> None:
        """Go back in browser history."""
        debug.info("Going back")
        await self._page.go_back()
    
    async def url(self) -> str:
        """Get the current URL."""
        return self._page.url
    
    def describe(self) -> str:
        """Get a description of the current state."""
        return self._page.url
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """Hook called before invoking an action."""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """Hook called after invoking an action."""
        await self.wait_for_navigation()
        await self.wait_for_network_idle()
    
    async def destroy(self) -> None:
        """Destroy and cleanup."""
        pass
    
    async def get_context(self) -> UIContext:
        """Get UI context."""
        screenshot = await self.screenshot_base64()
        size = await self.size()
        return UIContext(
            screenshot_base64=screenshot,
            size=size,
            is_frozen=False,
        )
    
    # Mouse operations
    async def mouse_click(
        self,
        x: int,
        y: int,
        button: str = "left",
        click_count: int = 1,
    ) -> None:
        """Click at position."""
        await self.mouse_move(x, y)
        debug.debug(f"Mouse click at ({x}, {y}), button={button}, count={click_count}")
        
        if click_count == 2:
            await self._page.mouse.dblclick(x, y, button=button)
        else:
            await self._page.mouse.click(x, y, button=button, click_count=click_count)
    
    async def mouse_move(self, x: int, y: int) -> None:
        """Move mouse to position."""
        self._ever_moved = True
        debug.debug(f"Mouse move to ({x}, {y})")
        await self._page.mouse.move(x, y)
    
    async def mouse_wheel(self, delta_x: int, delta_y: int) -> None:
        """Scroll with mouse wheel."""
        debug.debug(f"Mouse wheel ({delta_x}, {delta_y})")
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def mouse_drag(
        self,
        from_pos: Dict[str, int],
        to_pos: Dict[str, int],
    ) -> None:
        """Drag from one position to another."""
        debug.debug(f"Mouse drag from {from_pos} to {to_pos}")
        await self._page.mouse.move(from_pos["x"], from_pos["y"])
        await asyncio.sleep(0.2)
        await self._page.mouse.down()
        await asyncio.sleep(0.3)
        await self._page.mouse.move(to_pos["x"], to_pos["y"], steps=20)
        await asyncio.sleep(0.5)
        await self._page.mouse.up()
        await asyncio.sleep(0.2)
    
    # Keyboard operations
    async def keyboard_type(self, text: str) -> None:
        """Type text."""
        debug.debug(f"Keyboard type: {text}")
        await self._page.keyboard.type(text, delay=80)
    
    async def keyboard_press(self, key: str) -> None:
        """Press a key."""
        debug.debug(f"Keyboard press: {key}")
        await self._page.keyboard.press(key)
    
    async def keyboard_down(self, key: str) -> None:
        """Press key down."""
        await self._page.keyboard.down(key)
    
    async def keyboard_up(self, key: str) -> None:
        """Release key."""
        await self._page.keyboard.up(key)
    
    # Input clearing
    async def clear_input(self, element: LocateResultElement) -> None:
        """Clear an input field."""
        if not element:
            debug.warning("No element to clear input")
            return
        
        debug.debug("Clearing input")
        
        import platform
        is_mac = platform.system() == "Darwin"
        
        await self.mouse_click(element.center[0], element.center[1])
        
        if is_mac:
            await self._page.keyboard.down("Meta")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Meta")
        else:
            await self._page.keyboard.down("Control")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Control")
        
        await asyncio.sleep(0.1)
        await self._page.keyboard.press("Backspace")
    
    # Scroll operations
    async def _move_to_point_before_scroll(self, point: Optional[Point] = None) -> None:
        """Move to point before scrolling."""
        if point:
            await self.mouse_move(point.left, point.top)
        elif not self._ever_moved:
            size = await self.size()
            await self.mouse_move(size.width // 2, size.height // 2)
    
    async def scroll_up(self, distance: Optional[int] = None, starting_point: Optional[Point] = None) -> None:
        """Scroll up."""
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(0, -scroll_distance)
    
    async def scroll_down(self, distance: Optional[int] = None, starting_point: Optional[Point] = None) -> None:
        """Scroll down."""
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(0, scroll_distance)
    
    async def scroll_left(self, distance: Optional[int] = None, starting_point: Optional[Point] = None) -> None:
        """Scroll left."""
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(-scroll_distance, 0)
    
    async def scroll_right(self, distance: Optional[int] = None, starting_point: Optional[Point] = None) -> None:
        """Scroll right."""
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(scroll_distance, 0)
    
    async def scroll_until_top(self, starting_point: Optional[Point] = None) -> None:
        """Scroll to top."""
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(0, -9999999)
    
    async def scroll_until_bottom(self, starting_point: Optional[Point] = None) -> None:
        """Scroll to bottom."""
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(0, 9999999)
    
    async def scroll_until_left(self, starting_point: Optional[Point] = None) -> None:
        """Scroll to left."""
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(-9999999, 0)
    
    async def scroll_until_right(self, starting_point: Optional[Point] = None) -> None:
        """Scroll to right."""
        await self._move_to_point_before_scroll(starting_point)
        await self.mouse_wheel(9999999, 0)
    
    def _build_common_web_actions(self) -> List[DeviceAction]:
        """Build common web actions."""
        page = self
        
        async def tap_action(param: Any, context: Any = None) -> None:
            element = param.get("locate") if isinstance(param, dict) else param.locate
            assert_condition(element, "Element not found, cannot tap")
            await page.mouse_click(element.center[0], element.center[1])
        
        async def right_click_action(param: Any, context: Any = None) -> None:
            element = param.get("locate") if isinstance(param, dict) else param.locate
            assert_condition(element, "Element not found, cannot right click")
            await page.mouse_click(element.center[0], element.center[1], button="right")
        
        async def double_click_action(param: Any, context: Any = None) -> None:
            element = param.get("locate") if isinstance(param, dict) else param.locate
            assert_condition(element, "Element not found, cannot double click")
            await page.mouse_click(element.center[0], element.center[1], click_count=2)
        
        async def hover_action(param: Any, context: Any = None) -> None:
            element = param.get("locate") if isinstance(param, dict) else param.locate
            assert_condition(element, "Element not found, cannot hover")
            await page.mouse_move(element.center[0], element.center[1])
        
        async def input_action(param: Any, context: Any = None) -> None:
            if isinstance(param, dict):
                element = param.get("locate")
                value = param.get("value", "")
                mode = param.get("mode", "replace")
            else:
                element = param.locate
                value = param.value
                mode = getattr(param, "mode", "replace")
            
            if element and mode != "append":
                await page.clear_input(element)
            
            if mode == "clear":
                return
            
            if value:
                await page.keyboard_type(value)
        
        async def keyboard_press_action(param: Any, context: Any = None) -> None:
            if isinstance(param, dict):
                element = param.get("locate")
                key_name = param.get("keyName", "")
            else:
                element = getattr(param, "locate", None)
                key_name = param.key_name
            
            if element:
                await page.mouse_click(element.center[0], element.center[1])
            
            # Handle key combinations like "Control+A"
            if "+" in key_name:
                keys = key_name.split("+")
                for key in keys:
                    await page.keyboard_down(key.strip())
                for key in reversed(keys):
                    await page.keyboard_up(key.strip())
            else:
                await page.keyboard_press(key_name)
        
        async def scroll_action(param: Any, context: Any = None) -> None:
            if isinstance(param, dict):
                element = param.get("locate")
                scroll_type = param.get("scrollType", "singleAction")
                direction = param.get("direction", "down")
                distance = param.get("distance")
            else:
                element = getattr(param, "locate", None)
                scroll_type = getattr(param, "scroll_type", "singleAction")
                direction = getattr(param, "direction", "down")
                distance = getattr(param, "distance", None)
            
            starting_point = None
            if element:
                starting_point = Point(left=element.center[0], top=element.center[1])
            
            if scroll_type == "scrollToTop":
                await page.scroll_until_top(starting_point)
            elif scroll_type == "scrollToBottom":
                await page.scroll_until_bottom(starting_point)
            elif scroll_type == "scrollToRight":
                await page.scroll_until_right(starting_point)
            elif scroll_type == "scrollToLeft":
                await page.scroll_until_left(starting_point)
            else:
                if direction == "up":
                    await page.scroll_up(distance, starting_point)
                elif direction == "down":
                    await page.scroll_down(distance, starting_point)
                elif direction == "left":
                    await page.scroll_left(distance, starting_point)
                elif direction == "right":
                    await page.scroll_right(distance, starting_point)
                
                await asyncio.sleep(0.5)
        
        return [
            define_action_tap(tap_action),
            define_action_right_click(right_click_action),
            define_action_double_click(double_click_action),
            define_action_hover(hover_action),
            define_action_input(input_action),
            define_action_keyboard_press(keyboard_press_action),
            define_action_scroll(scroll_action),
            define_action_assert(),
        ]
