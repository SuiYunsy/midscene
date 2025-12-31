# -*- coding: utf-8 -*-
"""
Midscene Playwright Page Module
Playwright页面模块，实现AbstractInterface接口
"""

import asyncio
import base64
import platform
from typing import Dict, Any, List, Optional

from playwright.async_api import Page as PlaywrightPageType

from ..shared import (
    get_logger,
    Size,
    Rect,
    UIContext,
    LocateResultElement,
    assert_condition,
    sleep_ms,
)
from ..core.device import (
    AbstractInterface,
    define_action_tap,
    define_action_right_click,
    define_action_double_click,
    define_action_hover,
    define_action_input,
    define_action_keyboard_press,
    define_action_scroll,
    define_action_assert,
)

logger = get_logger("web:page")

# 默认超时配置
DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT = 30000  # 30秒
DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT = 30000  # 30秒
DEFAULT_WAIT_FOR_NETWORK_IDLE_CONCURRENCY = 2


class PlaywrightPage(AbstractInterface):
    """Playwright页面接口实现"""
    
    def __init__(
        self,
        page: PlaywrightPageType,
        opts: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化Playwright页面
        
        Args:
            page: Playwright Page对象
            opts: 选项配置
        """
        self._page = page
        self._opts = opts or {}
        self._viewport_size: Optional[Size] = None
        self._ever_moved = False
        
        # 配置
        self._wait_for_navigation_timeout = self._opts.get(
            "waitForNavigationTimeout",
            DEFAULT_WAIT_FOR_NAVIGATION_TIMEOUT,
        )
        self._wait_for_network_idle_timeout = self._opts.get(
            "waitForNetworkIdleTimeout",
            DEFAULT_WAIT_FOR_NETWORK_IDLE_TIMEOUT,
        )
        
        # 自定义动作
        self._custom_actions = self._opts.get("customActions", [])
    
    @property
    def interface_type(self) -> str:
        """设备接口类型"""
        return "playwright"
    
    @property
    def underlying_page(self) -> PlaywrightPageType:
        """获取底层Playwright Page"""
        return self._page
    
    async def screenshot_base64(self) -> str:
        """获取截图的base64编码"""
        await self._wait_for_navigation()
        logger.debug("screenshotBase64 begin")
        
        buffer = await self._page.screenshot(
            type="jpeg",
            quality=90,
            timeout=10000,
        )
        
        base64_str = base64.b64encode(buffer).decode("utf-8")
        result = f"data:image/jpeg;base64,{base64_str}"
        
        logger.debug("screenshotBase64 end")
        return result
    
    async def size(self) -> Size:
        """获取页面尺寸"""
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
    
    def action_space(self) -> List[Dict[str, Any]]:
        """获取可用动作空间"""
        actions = [
            define_action_tap(self._action_tap),
            define_action_right_click(self._action_right_click),
            define_action_double_click(self._action_double_click),
            define_action_hover(self._action_hover),
            define_action_input(self._action_input),
            define_action_keyboard_press(self._action_keyboard_press),
            define_action_scroll(self._action_scroll),
        ]
        
        # 添加自定义动作
        actions.extend(self._custom_actions)
        
        return actions
    
    async def _wait_for_navigation(self) -> None:
        """等待页面导航完成"""
        if self._wait_for_navigation_timeout == 0:
            logger.debug("waitForNavigation timeout is 0, skip waiting")
            return
        
        try:
            logger.debug(f"waitForNavigation begin, timeout: {self._wait_for_navigation_timeout}")
            await self._page.wait_for_selector(
                "html",
                timeout=self._wait_for_navigation_timeout,
            )
            logger.debug("waitForNavigation end")
        except Exception as e:
            logger.warning(
                f'Waiting for the "navigation" has timed out, but will continue execution. Error: {e}'
            )
    
    async def wait_for_network_idle(self, timeout: Optional[int] = None) -> None:
        """
        等待网络空闲
        
        Args:
            timeout: 超时时间（毫秒），默认使用配置的超时时间
        """
        actual_timeout = timeout if timeout is not None else self._wait_for_network_idle_timeout
        
        if actual_timeout == 0:
            logger.debug("waitForNetworkIdle timeout is 0, skip waiting")
            return
        
        try:
            logger.debug(f"waitForNetworkIdle begin, timeout: {actual_timeout}")
            await self._page.wait_for_load_state(
                "networkidle",
                timeout=actual_timeout,
            )
            logger.debug("waitForNetworkIdle end")
        except Exception as e:
            logger.warning(
                f'Waiting for "network idle" has timed out, but will continue execution. Error: {e}'
            )
    
    async def navigate(self, url: str) -> None:
        """导航到URL"""
        logger.debug(f"navigate to {url}")
        await self._page.goto(url)
    
    async def reload(self) -> None:
        """刷新页面"""
        logger.debug("reload page")
        await self._page.reload()
    
    async def go_back(self) -> None:
        """返回上一页"""
        logger.debug("go back")
        await self._page.go_back()
    
    async def url(self) -> str:
        """获取当前URL"""
        return self._page.url
    
    async def describe(self) -> str:
        """描述当前状态"""
        return self._page.url
    
    async def before_invoke_action(self, action_name: str, param: Any) -> None:
        """调用动作前的钩子"""
        pass
    
    async def after_invoke_action(self, action_name: str, param: Any) -> None:
        """调用动作后的钩子"""
        await self._wait_for_navigation()
        await self.wait_for_network_idle()
    
    async def destroy(self) -> None:
        """销毁/清理资源"""
        pass
    
    async def get_context(self) -> UIContext:
        """获取UI上下文"""
        screenshot = await self.screenshot_base64()
        page_size = await self.size()
        return UIContext(
            screenshot_base64=screenshot,
            size=page_size,
        )
    
    # ==================== 鼠标操作 ====================
    
    async def _mouse_move(self, x: int, y: int) -> None:
        """移动鼠标"""
        self._ever_moved = True
        logger.debug(f"mouse move to {x}, {y}")
        await self._page.mouse.move(x, y)
    
    async def _mouse_click(
        self,
        x: int,
        y: int,
        button: str = "left",
        count: int = 1,
    ) -> None:
        """点击鼠标"""
        await self._mouse_move(x, y)
        logger.debug(f"mouse click {x}, {y}, {button}, {count}")
        
        if count == 2:
            await self._page.mouse.dblclick(x, y, button=button)
        else:
            await self._page.mouse.click(x, y, button=button, click_count=count)
    
    async def _mouse_wheel(self, delta_x: int, delta_y: int) -> None:
        """滚动鼠标滚轮"""
        logger.debug(f"mouse wheel {delta_x}, {delta_y}")
        await self._page.mouse.wheel(delta_x, delta_y)
    
    async def _mouse_drag(
        self,
        from_pos: Dict[str, int],
        to_pos: Dict[str, int],
    ) -> None:
        """拖拽"""
        logger.debug(f"mouse drag from {from_pos} to {to_pos}")
        await self._page.mouse.move(from_pos["x"], from_pos["y"])
        await asyncio.sleep(0.2)
        await self._page.mouse.down()
        await asyncio.sleep(0.3)
        await self._page.mouse.move(to_pos["x"], to_pos["y"], steps=20)
        await asyncio.sleep(0.5)
        await self._page.mouse.up()
        await asyncio.sleep(0.2)
    
    # ==================== 键盘操作 ====================
    
    async def _keyboard_type(self, text: str) -> None:
        """输入文本"""
        logger.debug(f"keyboard type {text}")
        await self._page.keyboard.type(text, delay=80)
    
    async def _keyboard_press(self, key: str) -> None:
        """按键"""
        logger.debug(f"keyboard press {key}")
        
        # 处理组合键
        if "+" in key:
            keys = key.split("+")
            for k in keys:
                await self._page.keyboard.down(k.strip())
            for k in reversed(keys):
                await self._page.keyboard.up(k.strip())
        else:
            await self._page.keyboard.press(key)
    
    async def _clear_input(self, element: LocateResultElement) -> None:
        """清空输入框"""
        if not element:
            logger.warning("No element to clear input")
            return
        
        logger.debug("clearInput begin")
        
        # 点击输入框
        await self._mouse_click(element.center[0], element.center[1])
        
        # 全选并删除
        if platform.system() == "Darwin":
            await self._page.keyboard.down("Meta")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Meta")
        else:
            await self._page.keyboard.down("Control")
            await self._page.keyboard.press("a")
            await self._page.keyboard.up("Control")
        
        await asyncio.sleep(0.1)
        await self._page.keyboard.press("Backspace")
        
        logger.debug("clearInput end")
    
    # ==================== 滚动操作 ====================
    
    async def _move_to_point_before_scroll(self, point: Optional[Dict[str, int]] = None) -> None:
        """在滚动前移动到指定点"""
        if point:
            await self._mouse_move(point["left"], point["top"])
        elif not self._ever_moved:
            page_size = await self.size()
            target_x = page_size.width // 2
            target_y = page_size.height // 2
            await self._mouse_move(target_x, target_y)
    
    async def scroll_up(self, distance: Optional[int] = None, starting_point: Optional[Dict[str, int]] = None) -> None:
        """向上滚动"""
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(0, -scroll_distance)
    
    async def scroll_down(self, distance: Optional[int] = None, starting_point: Optional[Dict[str, int]] = None) -> None:
        """向下滚动"""
        inner_height = await self._page.evaluate("() => window.innerHeight")
        scroll_distance = distance or int(inner_height * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(0, scroll_distance)
    
    async def scroll_left(self, distance: Optional[int] = None, starting_point: Optional[Dict[str, int]] = None) -> None:
        """向左滚动"""
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(-scroll_distance, 0)
    
    async def scroll_right(self, distance: Optional[int] = None, starting_point: Optional[Dict[str, int]] = None) -> None:
        """向右滚动"""
        inner_width = await self._page.evaluate("() => window.innerWidth")
        scroll_distance = distance or int(inner_width * 0.7)
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(scroll_distance, 0)
    
    async def scroll_until_top(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到顶部"""
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(0, -9999999)
    
    async def scroll_until_bottom(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到底部"""
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(0, 9999999)
    
    async def scroll_until_left(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到最左"""
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(-9999999, 0)
    
    async def scroll_until_right(self, starting_point: Optional[Dict[str, int]] = None) -> None:
        """滚动到最右"""
        await self._move_to_point_before_scroll(starting_point)
        await self._mouse_wheel(9999999, 0)
    
    # ==================== 动作实现 ====================
    
    async def _action_tap(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行Tap动作"""
        locate = param.get("locate")
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                await self._mouse_click(center[0], center[1])
    
    async def _action_right_click(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行RightClick动作"""
        locate = param.get("locate")
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                await self._mouse_click(center[0], center[1], button="right")
    
    async def _action_double_click(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行DoubleClick动作"""
        locate = param.get("locate")
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                await self._mouse_click(center[0], center[1], count=2)
    
    async def _action_hover(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行Hover动作"""
        locate = param.get("locate")
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                await self._mouse_move(center[0], center[1])
    
    async def _action_input(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行Input动作"""
        value = param.get("value", "")
        locate = param.get("locate")
        mode = param.get("mode", "replace")
        
        # 如果有定位元素，先点击
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                await self._mouse_click(center[0], center[1])
        
        if mode == "clear":
            # 清除模式
            if locate:
                await self._clear_input(locate)
        elif mode == "append":
            # 追加模式
            await self._keyboard_type(str(value))
        else:
            # 替换模式（默认）
            if locate:
                await self._clear_input(locate)
            await self._keyboard_type(str(value))
    
    async def _action_keyboard_press(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行KeyboardPress动作"""
        locate = param.get("locate")
        key_name = param.get("keyName", "")
        
        # 如果有定位元素，先点击
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                await self._mouse_click(center[0], center[1])
        
        if key_name:
            await self._keyboard_press(key_name)
    
    async def _action_scroll(self, param: Dict[str, Any], context: Any = None) -> None:
        """执行Scroll动作"""
        scroll_type = param.get("scrollType", "singleAction")
        direction = param.get("direction", "down")
        distance = param.get("distance")
        locate = param.get("locate")
        
        # 获取起始点
        starting_point = None
        if locate:
            center = locate.center if hasattr(locate, 'center') else locate.get("center")
            if center:
                starting_point = {"left": center[0], "top": center[1]}
        
        if scroll_type == "scrollToBottom":
            await self.scroll_until_bottom(starting_point)
        elif scroll_type == "scrollToTop":
            await self.scroll_until_top(starting_point)
        elif scroll_type == "scrollToRight":
            await self.scroll_until_right(starting_point)
        elif scroll_type == "scrollToLeft":
            await self.scroll_until_left(starting_point)
        else:
            # singleAction
            if direction == "up":
                await self.scroll_up(distance, starting_point)
            elif direction == "down":
                await self.scroll_down(distance, starting_point)
            elif direction == "left":
                await self.scroll_left(distance, starting_point)
            elif direction == "right":
                await self.scroll_right(distance, starting_point)
