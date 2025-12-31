"""快速体验脚本：打开 example.com 并执行 AI 操作。"""

from __future__ import annotations

from mspy.core import Agent
from mspy.shared.logger import get_logger
from mspy.web.playwright_interface import launch_playwright, wait_for_network_idle

logger = get_logger("quick")


def main():
    # 1. 启动浏览器（有头模式）
    iface, page, playwright = launch_playwright("https://example.com", headless=False)
    try:
        # 2. 创建 Agent
        agent = Agent(iface)
        # 3. 执行 AI 行为
        agent.aiAct("点击了解更多")
        agent.ai_assert("出现Example Domains")
        wait_for_network_idle(page)
    finally:
        # 4. 清理
        page.context.browser.close()
        playwright.stop()
        logger.info("Browser closed.")


if __name__ == "__main__":
    main()
