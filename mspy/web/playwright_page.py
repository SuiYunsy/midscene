"""
Playwright Web页面模块
Playwright web page integration for Midscene Python SDK
"""
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from ..shared import (
    get_debug,
    assert_value,
    sleep,
    create_img_base64_by_format,
    Size,
    Rect,
    UIContext,
    LocateResultElement,
)
from ..core import (
    AbstractInterface,
    DeviceAction,
    define_action,
    define_action_tap,
    define_action_right_click,
    define_action_double_click,
    define_action_hover,
    define_action_input,
    define_action_keyboard_press,
    define_action_scroll,
)

debug = get_debug("web:page")

# 默认超时设置
DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT = 30000  # 30秒
DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT = 30000  # 30秒
DEFAULT_WAIT_FOR_NETWORK_IDLE_CONCURRENCY = 2


@dataclass
class WebPageOpt:
    """Web页面选项"""
    wait_for_navigation_timeout: int = DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT
    wait_for_network_idle_timeout: int = DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT
    before_invoke_action: Optional[callable] = None
    after_invoke_action: Optional[callable] = None
    custom_actions: Optional[List[DeviceAction]] = None
    enable_touch_events: bool = False


class PlaywrightWebPage(AbstractInterface):
    """
    Playwright Web页面实现
    """
    
    def __init__(
        self,
        page,
        opts: Optional[WebPageOpt] = None,
    ):
        """
        初始化Playwright Web页面
        
        Args:
            page: Playwright Page对象
            opts: 页面选项
        """
        self._page = page
        self._opts = opts or WebPageOpt()
        self._viewport_size: Optional[Size] = None
        self._interface_type = "playwright"
    
    @property
    def interface_type(self) -> str:
        return self._interface_type
    
    @property
    def page(self):
        """获取底层Playwright Page对象"""
        return self._page
    
    async def wait_for_navigation(self) -> None:
        """等待导航完成"""
        if self._opts.wait_for_navigation_timeout == 0:
            debug("waitForNavigation timeout is 0, skip waiting")
            return
        
        debug("waitForNavigation begin")
        try:
            await self._page.wait_for_selector("html", timeout=self._opts.wait_for_navigation_timeout)
        except Exception as e:
            debug(f"waitForNavigation timeout: {e}")
        debug("waitForNavigation end")
    
    async def wait_for_network_idle(self) -> None:
        """
        等待网络空闲
        这是一个非常重要的功能，确保页面完全加载
        """
        if self._opts.wait_for_network_idle_timeout == 0:
            debug("waitForNetworkIdle timeout is 0, skip waiting")
            return
        
        debug("waitForNetworkIdle begin")
        try:
            # Playwright的waitForLoadState('networkidle')
            await self._page.wait_for_load_state(
                "networkidle",
                timeout=self._opts.wait_for_network_idle_timeout
            )
        except Exception as e:
            debug(f"waitForNetworkIdle timeout: {e}")
            # 超时不抛出错误，继续执行
        debug("waitForNetworkIdle end")
    
    async def screenshot_base64(self) -> str:
        """获取截图的base64编码"""
        await self.wait_for_navigation()
        
        debug("screenshotBase64 begin")
        
        buffer = await self._page.screenshot(
            type="jpeg",
            quality=90,
            timeout=10000,
        )
        
        import base64
        base64_str = base64.b64encode(buffer).decode("utf-8")
        result = create_img_base64_by_format("jpeg", base64_str)
        
        debug("screenshotBase64 end")
        return result
    
    async def size(self) -> Size:
        """获取页面尺寸"""
        if self._viewport_size:
            return self._viewport_size
        
        size_info = await self._page.evaluate("""
            () => ({
                width: document.documentElement.clientWidth,
                height: document.documentElement.clientHeight,
                dpr: window.devicePixelRatio
            })
        """)
        
        self._viewport_size = Size(
            width=size_info["width"],
            height=size_info["height"],
            dpr=size_info.get("dpr"),
        )
        
        return self._viewport_size
    
    async def url(self) -> str:
        """获取当前URL"""
        return self._page.url
    
    def describe(self) -> str:
        """获取页面描述"""
        return self._page.url or ""
    
    async def navigate(self, url: str) -> None:
        """导航到指定URL"""
        debug(f"navigate to {url}")
        await self._page.goto(url)
    
    async def reload(self) -> None:
        """重新加载页面"""
        debug("reload page")
        await self._page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        debug("go back")
        await self._page.go_back()
    
    async def mouse_click(
        self,
        x: int,
        y: int,
        button: str = "left",
        count: int = 1,
    ) -> None:
        """鼠标点击"""
        await self.mouse_move(x, y)
        debug(f"mouse click {x}, {y}, {button}, {count}")
        
        if count == 2:
            await self._page.mouse.dblclick(x, y, button=button)
        else:
            await self._page.mouse.click(x, y, button=button, click_count=count)
    
    async def mouse_move(self, x: int, y: int) -> None:
        """鼠标移动"""
        debug(f"mouse move to {x}, {y}")
        await self._page.mouse.move(x, y)
    
    async def mouse_wheel(self, delta_x: int, delta_y: int) -> None:
        """鼠标滚轮"""
        debug(f"mouse wheel {delta_x}, {delta_y}")
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def keyboard_type(self, text: str) -> None:
        """键盘输入"""
        debug(f"keyboard type {text}")
        await self._page.keyboard.type(text, delay=80)
    
    async def keyboard_press(self, key: str) -> None:
        """键盘按键"""
        debug(f"keyboard press {key}")
        await self._page.keyboard.press(key)
    
    async def clear_input(self, element: LocateResultElement) -> None:
        """清除输入框内容"""
        if not element:
            debug("No element to clear input")
            return
        
        import platform
        is_mac = platform.system() == "Darwin"
        
        debug("clearInput begin")
        
        # 点击元素
        await self.mouse_click(element.center[0], element.center[1])
        
        # 全选并删除
        if is_mac:
            await self._page.keyboard.down("Meta")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Meta")
        else:
            await self._page.keyboard.down("Control")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Control")
        
        await sleep(100)
        await self._page.keyboard.press("Backspace")
        
        debug("clearInput end")
    
    async def scroll_until_top(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到顶部"""
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        await self.mouse_wheel(0, -9999999)
    
    async def scroll_until_bottom(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到底部"""
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        await self.mouse_wheel(0, 9999999)
    
    async def scroll_until_left(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到左边"""
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        await self.mouse_wheel(-9999999, 0)
    
    async def scroll_until_right(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到右边"""
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        await self.mouse_wheel(9999999, 0)
    
    async def scroll_up(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None,
    ) -> None:
        """向上滚动"""
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        
        await self.mouse_wheel(0, -scroll_distance)
    
    async def scroll_down(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None,
    ) -> None:
        """向下滚动"""
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        
        await self.mouse_wheel(0, scroll_distance)
    
    async def scroll_left(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None,
    ) -> None:
        """向左滚动"""
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        
        await self.mouse_wheel(-scroll_distance, 0)
    
    async def scroll_right(
        self,
        distance: Optional[int] = None,
        starting_point: Optional[Dict[str, int]] = None,
    ) -> None:
        """向右滚动"""
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        
        if starting_point:
            await self.mouse_move(starting_point.get("left", 0), starting_point.get("top", 0))
        
        await self.mouse_wheel(scroll_distance, 0)
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """动作执行前的钩子"""
        if self._opts.before_invoke_action:
            await self._opts.before_invoke_action(action_name, param)
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """动作执行后的钩子"""
        await self.wait_for_navigation()
        await self.wait_for_network_idle()
        if self._opts.after_invoke_action:
            await self._opts.after_invoke_action(action_name, param)
    
    async def destroy(self) -> None:
        """销毁页面"""
        pass
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        screenshot_base64 = await self.screenshot_base64()
        size = await self.size()
        
        return UIContext(
            screenshot_base64=screenshot_base64,
            size=size,
        )
    
    def action_space(self) -> List[DeviceAction]:
        """获取支持的动作空间"""
        page = self
        
        actions = [
            define_action_tap(lambda param: page._action_tap(param)),
            define_action_right_click(lambda param: page._action_right_click(param)),
            define_action_double_click(lambda param: page._action_double_click(param)),
            define_action_hover(lambda param: page._action_hover(param)),
            define_action_input(lambda param: page._action_input(param)),
            define_action_keyboard_press(lambda param: page._action_keyboard_press(param)),
            define_action_scroll(lambda param: page._action_scroll(param)),
        ]
        
        # 添加导航动作
        actions.append(define_action(
            name="Navigate",
            description="Navigate the browser to a specified URL",
            param_schema={
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to",
                    "optional": False,
                },
            },
            call=lambda param: page.navigate(param.get("url", "")),
        ))
        
        actions.append(define_action(
            name="Reload",
            description="Reload the current page",
            call=lambda _: page.reload(),
        ))
        
        actions.append(define_action(
            name="GoBack",
            description="Navigate back in browser history",
            call=lambda _: page.go_back(),
        ))
        
        # 添加自定义动作
        if self._opts.custom_actions:
            actions.extend(self._opts.custom_actions)
        
        return actions
    
    async def _action_tap(self, param: Dict[str, Any]) -> None:
        """点击动作"""
        element = param.get("locate")
        assert_value(element, "Element not found, cannot tap")
        await self.mouse_click(element.center[0], element.center[1], button="left")
    
    async def _action_right_click(self, param: Dict[str, Any]) -> None:
        """右键点击动作"""
        element = param.get("locate")
        assert_value(element, "Element not found, cannot right click")
        await self.mouse_click(element.center[0], element.center[1], button="right")
    
    async def _action_double_click(self, param: Dict[str, Any]) -> None:
        """双击动作"""
        element = param.get("locate")
        assert_value(element, "Element not found, cannot double click")
        await self.mouse_click(element.center[0], element.center[1], button="left", count=2)
    
    async def _action_hover(self, param: Dict[str, Any]) -> None:
        """悬停动作"""
        element = param.get("locate")
        assert_value(element, "Element not found, cannot hover")
        await self.mouse_move(element.center[0], element.center[1])
    
    async def _action_input(self, param: Dict[str, Any]) -> None:
        """输入动作"""
        element = param.get("locate")
        value = param.get("value", "")
        mode = param.get("mode", "replace")
        
        if element and mode != "append":
            await self.clear_input(element)
        
        if mode == "clear":
            return
        
        if value:
            await self.keyboard_type(str(value))
    
    async def _action_keyboard_press(self, param: Dict[str, Any]) -> None:
        """键盘按键动作"""
        element = param.get("locate")
        key_name = param.get("keyName", "")
        
        if element:
            await self.mouse_click(element.center[0], element.center[1])
        
        if key_name:
            await self.keyboard_press(key_name)
    
    async def _action_scroll(self, param: Dict[str, Any]) -> None:
        """滚动动作"""
        element = param.get("locate")
        starting_point = None
        if element:
            starting_point = {
                "left": element.center[0],
                "top": element.center[1],
            }
        
        scroll_type = param.get("scrollType", "singleAction")
        direction = param.get("direction", "down")
        distance = param.get("distance")
        
        if scroll_type == "scrollToTop":
            await self.scroll_until_top(starting_point)
        elif scroll_type == "scrollToBottom":
            await self.scroll_until_bottom(starting_point)
        elif scroll_type == "scrollToRight":
            await self.scroll_until_right(starting_point)
        elif scroll_type == "scrollToLeft":
            await self.scroll_until_left(starting_point)
        elif scroll_type == "singleAction" or not scroll_type:
            if direction == "down" or not direction:
                await self.scroll_down(distance, starting_point)
            elif direction == "up":
                await self.scroll_up(distance, starting_point)
            elif direction == "left":
                await self.scroll_left(distance, starting_point)
            elif direction == "right":
                await self.scroll_right(distance, starting_point)
            else:
                raise ValueError(f"Unknown scroll direction: {direction}")
            
            await sleep(500)
        else:
            raise ValueError(f"Unknown scroll type: {scroll_type}")


async def create_playwright_page(
    url: Optional[str] = None,
    headless: bool = True,
    viewport_width: int = 1280,
    viewport_height: int = 720,
    user_data_dir: Optional[str] = None,
    cookies: Optional[List[Dict[str, Any]]] = None,
    local_storage: Optional[Dict[str, str]] = None,
    opts: Optional[WebPageOpt] = None,
) -> Tuple[PlaywrightWebPage, Any, Any]:
    """
    创建Playwright页面
    
    Args:
        url: 初始URL
        headless: 是否无头模式
        viewport_width: 视口宽度
        viewport_height: 视口高度
        user_data_dir: 用户数据目录
        cookies: Cookies列表
        local_storage: LocalStorage键值对
        opts: 页面选项
        
    Returns:
        (PlaywrightWebPage, browser, context) 元组
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError("playwright is required. Install with: pip install playwright")
    
    playwright = await async_playwright().start()
    
    # 创建浏览器
    browser_args = {
        "headless": headless,
    }
    
    if user_data_dir:
        # 使用持久化上下文
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=headless,
            viewport={"width": viewport_width, "height": viewport_height},
        )
        browser = None
    else:
        browser = await playwright.chromium.launch(**browser_args)
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
        )
    
    # 设置Cookies
    if cookies:
        await context.add_cookies(cookies)
    
    # 创建页面
    page = await context.new_page()
    
    # 设置LocalStorage
    if local_storage and url:
        await page.goto(url)
        for key, value in local_storage.items():
            await page.evaluate(f"localStorage.setItem('{key}', '{value}')")
    elif url:
        await page.goto(url)
    
    # 创建WebPage包装
    web_page = PlaywrightWebPage(page, opts)
    
    # 等待页面加载
    await web_page.wait_for_navigation()
    await web_page.wait_for_network_idle()
    
    return web_page, browser, context


async def close_playwright(browser, context, playwright=None) -> None:
    """
    关闭Playwright资源
    
    Args:
        browser: 浏览器实例
        context: 上下文实例
        playwright: Playwright实例
    """
    try:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
    except Exception as e:
        debug(f"Error closing playwright: {e}")
