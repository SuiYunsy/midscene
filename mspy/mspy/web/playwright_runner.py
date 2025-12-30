"""
基于 Playwright 的执行层，只保留必要集成。
"""

from __future__ import annotations

import base64
from typing import Any, Dict

from playwright.sync_api import Playwright, sync_playwright

from mspy.shared.logger import get_logger

logger = get_logger("mspy.web")


class PlaywrightRunner:
    """Playwright 管理器。"""

    def __init__(self, headless: bool = True):
        self._headless = headless
        self._context_manager: Playwright | None = None
        self._browser = None

    def __enter__(self):
        self._context_manager = sync_playwright().start()
        self._browser = self._context_manager.chromium.launch(headless=self._headless)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._browser:
            self._browser.close()
        if self._context_manager:
            self._context_manager.stop()

    # 中文注释：打开页面并返回 page
    def open(self, url: str):
        logger.info("Opening page: %s", url)
        page = self._browser.new_page()
        page.goto(url)
        return page

    # 中文注释：截图并返回 base64
    def screenshot_base64(self, page) -> str:
        data = page.screenshot(full_page=True)
        return "data:image/png;base64," + base64.b64encode(data).decode("utf-8")

    # 中文注释：根据 AI 规划执行动作
    def apply_action(self, page, action: Dict[str, Any]) -> None:
        action_type = action.get("type")
        param = action.get("param") or {}
        logger.info("Applying action %s", action_type)
        if action_type in {"Tap", "DoubleClick", "Hover"}:
            self._apply_pointer_action(page, action_type, param)
        elif action_type == "Input":
            self._apply_input(page, param)
        elif action_type == "Scroll":
            self._apply_scroll(page, param)
        elif action_type == "AssertText":
            self._apply_assert_text(page, param)
        else:
            logger.warning("Unknown action type: %s", action_type)

    def _apply_pointer_action(self, page, action_type: str, param: Dict[str, Any]) -> None:
        locate = param.get("locate") or {}
        bbox = locate.get("bbox")
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            if action_type == "Hover":
                page.mouse.move(x, y)
            elif action_type == "DoubleClick":
                page.mouse.dblclick(x, y)
            else:
                page.mouse.click(x, y)
        else:
            prompt = locate.get("prompt")
            if prompt:
                locator = page.get_by_text(prompt, exact=False)
                if action_type == "Hover":
                    locator.hover()
                elif action_type == "DoubleClick":
                    locator.dblclick()
                else:
                    locator.click()
            else:
                logger.warning("No locate hint provided for pointer action.")

    def _apply_input(self, page, param: Dict[str, Any]) -> None:
        value = param.get("value", "")
        locate = param.get("locate") or {}
        prompt = locate.get("prompt")
        target = page.get_by_placeholder(prompt) if prompt else page.locator("input,textarea").first
        mode = param.get("mode", "replace")
        if mode == "clear":
            target.fill("")
        elif mode == "append":
            target.type(str(value))
        else:
            target.fill(str(value))

    def _apply_scroll(self, page, param: Dict[str, Any]) -> None:
        direction = param.get("direction", "down")
        amount = param.get("amount", 400)
        dy = amount if direction == "down" else -amount
        page.mouse.wheel(0, dy)

    def _apply_assert_text(self, page, param: Dict[str, Any]) -> None:
        text = param.get("text", "")
        if not text:
            logger.warning("AssertText missing 'text' param")
            return
        locator = page.get_by_text(text, exact=False)
        assert locator.count() > 0, f"Text '{text}' not found"
        logger.info("Assertion passed: %s", text)
