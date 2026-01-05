"""Web动作空间定义"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ..core.types import DeviceAction, LocateResult
from ..shared.logger import get_logger
from ..shared.utils import sleep_ms

if TYPE_CHECKING:
    from .playwright_page import PlaywrightPage

logger = get_logger("web-actions")

def get_web_action_space(page: "PlaywrightPage") -> List[DeviceAction]:
    """获取Web端动作空间"""
    async def tap(param: Dict[str, Any]) -> None:
        """点击元素"""
        locate = param.get("locate")
        if not locate:
            raise ValueError("Tap需要locate参数")
        x, y = locate.center
        await page.mouse_click(x, y)
    async def right_click(param: Dict[str, Any]) -> None:
        """右键点击"""
        locate = param.get("locate")
        if not locate:
            raise ValueError("RightClick需要locate参数")
        x, y = locate.center
        await page.mouse_click(x, y, button="right")
    async def double_click(param: Dict[str, Any]) -> None:
        """双击"""
        locate = param.get("locate")
        if not locate:
            raise ValueError("DoubleClick需要locate参数")
        x, y = locate.center
        await page.mouse_dblclick(x, y)
    async def hover(param: Dict[str, Any]) -> None:
        """悬停"""
        locate = param.get("locate")
        if not locate:
            raise ValueError("Hover需要locate参数")
        x, y = locate.center
        await page.mouse_move(x, y)
    async def input_text(param: Dict[str, Any]) -> None:
        """输入文本"""
        value = param.get("value", "")
        locate = param.get("locate")
        mode = param.get("mode", "replace")
        # 如果有定位，先点击
        if locate:
            x, y = locate.center
            await page.mouse_click(x, y)
            await sleep_ms(100)
        # 根据模式处理
        if mode == "clear" or mode == "replace":
            await page.clear_input()
        if mode != "clear" and value:
            await page.keyboard_type(value)
    async def keyboard_press(param: Dict[str, Any]) -> None:
        """按键"""
        key_name = param.get("keyName", "")
        locate = param.get("locate")
        if locate:
            x, y = locate.center
            await page.mouse_click(x, y)
            await sleep_ms(100)
        await page.keyboard_press(key_name)
    async def scroll(param: Dict[str, Any]) -> None:
        """滚动"""
        scroll_type = param.get("scrollType", "singleAction")
        direction = param.get("direction", "down")
        distance = param.get("distance")
        locate = param.get("locate")
        # 确定起始点
        start_x, start_y = None, None
        if locate:
            start_x, start_y = locate.center
        if scroll_type == "scrollToTop":
            await page.scroll_to_top(start_x, start_y)
        elif scroll_type == "scrollToBottom":
            await page.scroll_to_bottom(start_x, start_y)
        elif scroll_type == "scrollToLeft":
            await page.scroll_to_left(start_x, start_y)
        elif scroll_type == "scrollToRight":
            await page.scroll_to_right(start_x, start_y)
        else:
            # 单次滚动
            dist = distance or 500
            if direction == "up":
                await page.scroll(0, -dist, start_x, start_y)
            elif direction == "down":
                await page.scroll(0, dist, start_x, start_y)
            elif direction == "left":
                await page.scroll(-dist, 0, start_x, start_y)
            elif direction == "right":
                await page.scroll(dist, 0, start_x, start_y)
    async def drag_and_drop(param: Dict[str, Any]) -> None:
        """拖放"""
        from_loc = param.get("from")
        to_loc = param.get("to")
        if not from_loc or not to_loc:
            raise ValueError("DragAndDrop需要from和to参数")
        await page.drag(from_loc.center, to_loc.center)
    async def navigate(param: Dict[str, Any]) -> None:
        """导航到URL"""
        url = param.get("url", "")
        if not url:
            raise ValueError("Navigate需要url参数")
        await page.goto(url)
    async def reload(param: Dict[str, Any]) -> None:
        """刷新页面"""
        await page.reload()
    async def go_back(param: Dict[str, Any]) -> None:
        """后退"""
        await page.go_back()
    async def print_assert_result(param: Dict[str, Any]) -> None:
        """打印断言结果"""
        condition = param.get("condition", "")
        thought = param.get("thought", "")
        result = param.get("result", False)
        logger.info(f"断言: {condition}")
        logger.info(f"思考: {thought}")
        logger.info(f"结果: {result}")
        if not result:
            raise AssertionError(f"断言失败: {thought}")
    return [
        DeviceAction(name="Tap", description="点击元素", call=tap),
        DeviceAction(name="RightClick", description="右键点击", call=right_click),
        DeviceAction(name="DoubleClick", description="双击", call=double_click),
        DeviceAction(name="Hover", description="悬停", call=hover),
        DeviceAction(name="Input", description="输入文本", call=input_text),
        DeviceAction(name="KeyboardPress", description="按键", call=keyboard_press),
        DeviceAction(name="Scroll", description="滚动", call=scroll),
        DeviceAction(name="DragAndDrop", description="拖放", call=drag_and_drop),
        DeviceAction(name="Navigate", description="导航到URL", call=navigate),
        DeviceAction(name="Reload", description="刷新页面", call=reload),
        DeviceAction(name="GoBack", description="后退", call=go_back),
        DeviceAction(name="Print_Assert_Result", description="打印断言结果", call=print_assert_result),
    ]
