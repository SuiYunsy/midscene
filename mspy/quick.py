#!/usr/bin/env python3
"""
快速体验脚本 - mspy
有头模式，导航到example.com，执行aiAct操作
"""
import asyncio
from mspy.core.agent import Agent
from mspy.web.playwright_page import PlaywrightLauncher
from mspy.shared.config import get_config
from mspy.shared.logger import get_logger

logger = get_logger("quick")

async def main():
    """主函数"""
    config = get_config()
    logger.info("启动浏览器（有头模式）...")
    # 启动浏览器 - 有头模式
    launcher = PlaywrightLauncher(
        headless=False,
        viewport_width=1280,
        viewport_height=720,
    )
    try:
        page = await launcher.launch()
        logger.info("导航到 example.com ...")
        await page.goto("https://example.com")
        # 创建Agent
        agent = Agent(page, config=config)
        # 执行aiAct
        logger.info("执行 aiAct...")
        result = await agent.ai_act(
            "点击了解更多，然后点击About，断言：出现About us"
        )
        # 输出结果
        logger.info(f"执行完成!")
        logger.info(f"耗时: {result.get('duration_ms', 0)}ms")
        logger.info(f"Token使用: {result.get('usage', {})}")
        # 检查断言结果
        assert_results = result.get("assert_results", [])
        for ar in assert_results:
            logger.info(f"断言: {ar.get('condition')}")
            logger.info(f"结果: {ar.get('result')}")
            logger.info(f"思考: {ar.get('thought')}")
        # 保存报告
        report_path = await agent.save_report()
        logger.info(f"报告已保存: {report_path}")
    finally:
        await launcher.close()
        logger.info("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(main())
