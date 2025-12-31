#!/usr/bin/env python3
"""
Midscene Python 快速体验脚本
Midscene Python quick start script

使用方法 (Usage):
    1. 复制 .env.example 到 .env 并填写配置
       Copy .env.example to .env and fill in the configuration
    2. 运行脚本
       Run the script:
       uv run python quick.py
"""
import asyncio
import os
import sys

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from playwright.async_api import async_playwright

# 添加 mspy 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mspy import get_debug
from mspy.shared import ModelConfigManager
from mspy.web import PlaywrightWebPage
from mspy.core import Agent

# 初始化日志
logger = get_debug("quick")


async def main():
    """主函数"""
    print("=" * 60)
    print("Midscene Python Quick Start")
    print("=" * 60)
    
    # 检查必要的环境变量
    model_name = os.environ.get("MIDSCENE_MODEL_NAME")
    base_url = os.environ.get("MIDSCENE_MODEL_BASE_URL")
    
    if not model_name or not base_url:
        print("\n错误: 请先配置环境变量!")
        print("Error: Please configure environment variables first!")
        print("\n1. 复制 .env.example 到 .env")
        print("   Copy .env.example to .env")
        print("2. 填写 MIDSCENE_MODEL_NAME 和 MIDSCENE_MODEL_BASE_URL")
        print("   Fill in MIDSCENE_MODEL_NAME and MIDSCENE_MODEL_BASE_URL")
        return
    
    print(f"\n使用模型: {model_name}")
    print(f"Using model: {model_name}")
    print(f"API URL: {base_url}")
    
    # 启动 Playwright
    print("\n启动浏览器...")
    print("Starting browser...")
    
    async with async_playwright() as p:
        # 启动有头浏览器
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 创建 Midscene 页面包装器
        web_page = PlaywrightWebPage(page)
        
        # 创建模型配置管理器
        model_config_manager = ModelConfigManager()
        
        # 创建 Agent
        agent = Agent(
            interface=web_page,
            model_config_manager=model_config_manager,
        )
        
        # 导航到 example.com
        print("\n导航到 example.com...")
        print("Navigating to example.com...")
        await web_page.navigate("https://example.com")
        
        # 等待页面加载
        await asyncio.sleep(2)
        
        print("\n执行 AI 动作: 点击了解更多")
        print("Executing AI action: Click to learn more")
        
        try:
            # 执行 AI 动作
            result = await agent.ai_act("点击了解更多")
            print(f"AI 动作结果: {result}")
        except Exception as e:
            print(f"AI 动作执行失败: {e}")
            print(f"AI action failed: {e}")
        
        # 等待一下看结果
        await asyncio.sleep(2)
        
        print("\n执行 AI 断言: 检查是否出现 Example Domains")
        print("Executing AI assertion: Check if Example Domains appears")
        
        try:
            # 执行 AI 断言
            result = await agent.ai_assert("出现Example Domains")
            print(f"AI 断言结果: {result}")
        except Exception as e:
            print(f"AI 断言执行失败: {e}")
            print(f"AI assertion failed: {e}")
        
        # 保持浏览器打开一会
        print("\n完成! 浏览器将在5秒后关闭...")
        print("Done! Browser will close in 5 seconds...")
        await asyncio.sleep(5)
        
        await browser.close()
    
    print("\n" + "=" * 60)
    print("快速体验结束")
    print("Quick start finished")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
