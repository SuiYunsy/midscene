#!/usr/bin/env python3
"""
Midscene Python 快速体验示例
导航到 example 网站并使用 AI 执行操作
"""

import asyncio
import os
import sys

# 添加 mspy 到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 加载环境变量
load_dotenv()


async def main():
    """
    快速体验示例
    1. 导航到 example.com
    2. 使用 AI 分析页面并执行操作
    """
    print("=" * 50)
    print("Midscene Python Quick Start Example")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.environ.get("MIDSCENE_MODEL_API_KEY")
    if not api_key:
        print("\n⚠️  Warning: MIDSCENE_MODEL_API_KEY not set")
        print("Please copy .env.example to .env and fill in your API key")
        print("\n示例:")
        print("  cp .env.example .env")
        print("  # 编辑 .env 文件")
        return
    
    # 导入 Midscene（延迟导入以便先检查环境变量）
    from mspy import PlaywrightAgent
    
    print("\n🚀 Starting browser...")
    
    async with async_playwright() as p:
        # 启动浏览器（非无头模式以便观察）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        print("📍 Navigating to example.com...")
        await page.goto("https://www.example.com")
        
        # 等待页面加载
        await page.wait_for_load_state("networkidle")
        
        print("🤖 Creating Midscene Agent...")
        agent = PlaywrightAgent(page)
        
        print("\n📝 Page loaded. Let's analyze and interact with it.")
        print("   Current URL:", page.url)
        
        # 执行 AI 断言 - 验证页面内容
        print("\n✅ Running AI assertion: Check if we're on example.com")
        try:
            await agent.ai_assert("This is the Example Domain page")
            print("   ✓ Assertion passed!")
        except AssertionError as e:
            print(f"   ✗ Assertion failed: {e}")
        
        # 执行 AI 动作 - 尝试点击链接
        print("\n🎯 Running AI action: Click 'More information' link")
        try:
            result = await agent.ai_act("点击 'More information' 链接")
            print("   ✓ Action completed!")
            print(f"   Actions executed: {len(result.get('actions', []))}")
        except Exception as e:
            print(f"   ✗ Action failed: {e}")
        
        # 等待用户观察结果
        print("\n⏳ Waiting 5 seconds for observation...")
        await asyncio.sleep(5)
        
        print("\n📍 Final URL:", page.url)
        
        # 清理
        print("\n🧹 Cleaning up...")
        await agent.destroy()
        await browser.close()
    
    print("\n✅ Example completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
