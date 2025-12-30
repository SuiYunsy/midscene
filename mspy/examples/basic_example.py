"""
基础示例 - 演示mspy的基本用法

这个示例展示如何使用PlaywrightAgent进行Web自动化测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


async def main():
    """主函数"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("请先安装playwright: pip install playwright")
        print("然后运行: playwright install")
        return
    
    from mspy.web import PlaywrightAgent
    
    print("🚀 启动Playwright...")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 导航到示例页面
        print("📄 打开示例页面...")
        await page.goto('https://example.com')
        
        # 创建Agent
        print("🤖 创建AI Agent...")
        agent = PlaywrightAgent(page)
        
        # 获取页面尺寸
        size = await agent.interface.size()
        print(f"📐 页面尺寸: {size.width}x{size.height}")
        
        # 截图
        screenshot = await agent.interface.screenshot_base64()
        print(f"📷 截图大小: {len(screenshot)} 字符")
        
        # 这里可以添加AI操作，例如:
        # await agent.ai_tap('某个按钮')
        # await agent.ai_input('搜索框', '搜索内容')
        # await agent.ai_assert('页面包含某些内容')
        
        print("✅ 示例运行完成!")
        
        # 关闭浏览器
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
