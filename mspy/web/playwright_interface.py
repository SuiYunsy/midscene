"""Playwright 实现的页面接口，包含 wait_for_network_idle。"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple, Union

from playwright.sync_api import Error as PlaywrightError, Page, TimeoutError, sync_playwright

from ..core.device import AbstractInterface
from ..core.types import ActionSpaceItem, Size, UIContext
from ..shared.img import image_info_of_base64
from ..shared.logger import get_logger
from ..shared.utils import bytes_to_data_url

logger = get_logger("playwright-interface")


def wait_for_network_idle(page: Page, idle_ms: int = 500, timeout_ms: int = 10000):
    """等待网络空闲。"""
    logger.info("Waiting for network idle...")
    page.wait_for_load_state("networkidle", timeout=timeout_ms)
    page.wait_for_timeout(idle_ms)
    logger.info("Network idle detected")


class PlaywrightInterface(AbstractInterface):
    interface_type = "playwright"

    def __init__(self, page: Page):
        self.page = page

    def action_space(self) -> List[ActionSpaceItem]:
        return [
            ActionSpaceItem(
                name="Tap",
                description="Tap or click the target element",
                param_hint='{"locate": {"prompt": string, "bbox": [xmin,ymin,xmax,ymax]}}',
            ),
            ActionSpaceItem(
                name="Print_Assert_Result",
                description="Print assertion result for the user",
                param_hint='{"success": boolean, "message"?: string}',
            ),
        ]

    def get_context(self) -> UIContext:
        screenshot = self.screenshot_base64()
        info = image_info_of_base64(screenshot)
        return UIContext(
            screenshot_base64=screenshot,
            size=Size(width=info.width, height=info.height),
            url=self.page.url,
            title=self.page.title(),
            meta={"user_agent": self.page.context.user_agent},
        )

    def screenshot_base64(self) -> str:
        raw = self.page.screenshot(full_page=True)
        return bytes_to_data_url(raw)

    def perform_action(
        self, action_type: str, param: Dict[str, Any], context: UIContext
    ) -> Any:
        action_type_lower = action_type.lower()
        if action_type_lower in ("tap", "click"):
            bbox = param.get("bbox") or param.get("locate", {}).get("bbox")
            prompt = param.get("prompt") or param.get("locate", {}).get("prompt")
            if bbox:
                return self._click_bbox(bbox)
            if prompt:
                try:
                    locator = self.page.get_by_text(str(prompt), exact=False)
                    locator.first.click(timeout=5000)
                    return True
                except (PlaywrightError, TimeoutError) as error:
                    logger.error("Fallback text click failed: %s", error)
            raise ValueError("No bbox or prompt for Tap action")
        if action_type == "Print_Assert_Result":
            logger.info("Assert result: %s", param)
            return True
        raise ValueError(f"Unsupported action: {action_type}")

    def _click_bbox(
        self, bbox: Union[List[float], Tuple[float, float, float, float]]
    ) -> bool:
        x1, y1, x2, y2 = bbox
        x = (float(x1) + float(x2)) / 2
        y = (float(y1) + float(y2)) / 2
        logger.info("Click at bbox center (%s,%s)", x, y)
        self.page.mouse.click(x, y)
        return True


def launch_playwright(
    url: str, headless: bool = False
) -> Tuple[PlaywrightInterface, Page, Any]:
    """便捷启动函数，返回接口与 page、playwright 对象。"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    page = browser.new_page()
    page.goto(url)
    wait_for_network_idle(page)
    iface = PlaywrightInterface(page)
    return iface, page, playwright
