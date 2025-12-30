from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from mspy.shared.config import RuntimeConfig
from mspy.shared.logger import get_logger


@dataclass
class BrowserConfig:
    headless: bool = True
    locale: str | None = None
    viewport: Optional[dict] = None


class PlaywrightInterface:
    """
    基于 Playwright 的浏览器适配层。
    中文注释：仅保留 Web 能力，不包含 Puppeteer / Selenium / MCP。
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.logger = get_logger("mspy.playwright")
        self._sync_playwright = None
        self._play = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self) -> "PlaywrightInterface":
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise ImportError(
                "需要安装 playwright 才能使用 web-integration：pip install playwright && playwright install"
            ) from exc

        self._sync_playwright = sync_playwright
        self._play = sync_playwright().start()
        chromium = self._play.chromium
        self._browser = chromium.launch(headless=self.config.headless)
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="zh-CN",
        )
        self._page = self._context.new_page()
        if self.config.base_url:
            self.navigate(self.config.base_url)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._play:
            self._play.stop()

    # === 动作实现 ===
    def navigate(self, url: str) -> None:
        assert self._page, "浏览器尚未初始化"
        self.logger.info(f"[导航] {url}")
        self._page.goto(url, wait_until="load", timeout=self.config.timeout)

    def click(self, selector: str) -> None:
        assert self._page, "浏览器尚未初始化"
        self.logger.info(f"[点击] {selector}")
        self._page.click(selector, timeout=self.config.timeout)

    def input(self, selector: str, text: str) -> None:
        assert self._page, "浏览器尚未初始化"
        self.logger.info(f"[输入] {selector} <- {text}")
        self._page.fill(selector, text, timeout=self.config.timeout)

    def expect_text(self, selector: str, contains: str, timeout: int | None = None) -> None:
        assert self._page, "浏览器尚未初始化"
        self.logger.info(f"[断言文本] {selector} 包含 {contains}")
        self._page.wait_for_selector(selector, timeout=timeout or self.config.timeout, state="visible")
        content = self._page.inner_text(selector, timeout=timeout or self.config.timeout)
        if contains not in content:
            raise AssertionError(f"元素文本不包含预期内容: {contains}")

    def evaluate(self, script: str):
        assert self._page, "浏览器尚未初始化"
        self.logger.info("[执行脚本]")
        return self._page.evaluate(script)

    def sleep(self, ms: int) -> None:
        assert self._page, "浏览器尚未初始化"
        self.logger.info(f"[等待] {ms}ms")
        self._page.wait_for_timeout(ms)

    def screenshot(self, title: str | None = None) -> str:
        assert self._page, "浏览器尚未初始化"
        path = f".mspy-output/{title or 'screenshot'}.png"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"[截图] {path}")
        self._page.screenshot(path=path, full_page=True)
        return path
