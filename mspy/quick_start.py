#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mspy 快速体验脚本
演示如何使用 mspy 进行 AI 驱动的 UI 自动化。
"""

import asyncio
import os
import sys

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, using system environment variables only")

from playwright.async_api import async_playwright

# 添加 mspy 到路径（开发时使用）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mspy.web import PlaywrightAgent


async def demo_baidu_search():
    """
    演示：使用 AI 在百度进行搜索
    """
    print("=" * 50)
    print("mspy Quick Start Demo")
    print("=" * 50)
    
    # 检查必要的环境变量
    if not os.environ.get("MIDSCENE_MODEL_API_KEY"):
        print("\n[Error] Missing MIDSCENE_MODEL_API_KEY environment variable.")
        print("Please copy .env.example to .env and fill in your API key.")
        return
    
    print(f"\n[Info] Using model: {os.environ.get('MIDSCENE_MODEL_NAME', 'default')}")
    print(f"[Info] Base URL: {os.environ.get('MIDSCENE_MODEL_BASE_URL', 'default')}")
    
    async with async_playwright() as p:
        # 启动浏览器（非无头模式以便观察）
        print("\n[Step 1] Launching browser...")
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 导航到百度
        print("[Step 2] Navigating to Baidu...")
        await page.goto("https://www.baidu.com")
        await asyncio.sleep(1)  # 等待页面加载
        
        # 创建 AI Agent
        print("[Step 3] Creating AI Agent...")
        agent = PlaywrightAgent(page, headless=False)
        
        try:
            # 使用 AI 操作页面
            print("[Step 4] Using AI to interact with the page...")
            
            # 点击搜索框
            print("  - Tapping search box...")
            await agent.ai_tap("搜索框")
            await asyncio.sleep(0.5)
            
            # 输入搜索词
            print("  - Inputting search text...")
            await agent.ai_input("搜索框", {"value": "Midscene AI automation"})
            await asyncio.sleep(0.5)
            
            # 点击搜索按钮
            print("  - Clicking search button...")
            await agent.ai_tap("百度一下")
            await asyncio.sleep(2)  # 等待搜索结果
            
            # 提取数据
            print("[Step 5] Extracting search results...")
            try:
                results = await agent.ai_query("列出前3个搜索结果的标题")
                print(f"\n[Result] Search results:\n{results}")
            except Exception as e:
                print(f"[Warning] Failed to extract results: {e}")
            
            # 断言验证
            print("\n[Step 6] Verifying page state...")
            try:
                await agent.ai_assert("页面显示了搜索结果")
                print("[Success] Assertion passed!")
            except AssertionError as e:
                print(f"[Failed] Assertion failed: {e}")
            
        except Exception as e:
            print(f"\n[Error] An error occurred: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 等待用户观察结果
            print("\n[Info] Demo completed. Closing browser in 5 seconds...")
            await asyncio.sleep(5)
            await browser.close()
    
    print("\n[Done] Thank you for trying mspy!")


async def demo_simple():
    """
    简单演示：仅截图和定位
    """
    print("=" * 50)
    print("mspy Simple Demo")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://www.example.com")
        
        agent = PlaywrightAgent(page)
        
        # 获取页面信息
        context = await agent._get_ui_context()
        print(f"[Info] Page size: {context.size.width}x{context.size.height}")
        print(f"[Info] Screenshot captured (base64 length: {len(context.screenshot_base64)})")
        
        await browser.close()
    
    print("[Done] Simple demo completed.")


def main():
    """主函数"""
    print("\nmspy - Python implementation of Midscene")
    print("An AI-powered UI automation framework\n")
    
    # 根据是否配置了 API key 选择演示
    if os.environ.get("MIDSCENE_MODEL_API_KEY"):
        asyncio.run(demo_baidu_search())
    else:
        print("[Info] No API key configured. Running simple demo...")
        print("[Hint] Set MIDSCENE_MODEL_API_KEY to run the full demo.\n")
        asyncio.run(demo_simple())


if __name__ == "__main__":
    main()
