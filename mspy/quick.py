#!/usr/bin/env python3
"""
Midscene 快速体验脚本
Quick start script for Midscene Python SDK

用法 / Usage:
    # 从mspy目录的父目录运行
    cd /path/to/midscene
    python -m mspy.quick
    
    # 或者设置PYTHONPATH后运行
    PYTHONPATH=/path/to/midscene python mspy/quick.py
    
    # 使用uv运行
    cd /path/to/midscene
    uv run python -m mspy.quick

确保在运行前设置好.env文件或环境变量
Make sure to set up .env file or environment variables before running
"""

import asyncio
import sys
import os

# 添加父目录到路径，以便可以正确导入mspy包
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 加载.env文件
try:
    from dotenv import load_dotenv
    # 首先尝试加载mspy目录下的.env文件
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

from mspy.core import Agent
from mspy.web import create_playwright_page, close_playwright
from mspy.shared import get_logger

logger = get_logger("quick")


async def main():
    """主函数"""
    
    print("=" * 60)
    print("Midscene Python SDK 快速体验")
    print("Quick Start Demo")
    print("=" * 60)
    
    browser = None
    context = None
    
    try:
        # 创建Playwright页面（有头模式）
        print("\n[1/5] Creating browser and navigating to example.com...")
        logger.debug("Creating Playwright page in headed mode")
        
        web_page, browser, context = await create_playwright_page(
            url="https://example.com",
            headless=False,  # 有头模式
            viewport_width=1280,
            viewport_height=720,
        )
        
        print("    ✓ Browser created and page loaded")
        
        # 创建Agent
        print("\n[2/5] Creating Midscene Agent...")
        agent = Agent(web_page)
        print("    ✓ Agent created")
        
        # 等待页面完全加载
        print("\n[3/5] Waiting for page to be ready...")
        await asyncio.sleep(2)
        print("    ✓ Page is ready")
        
        # 执行AI动作：点击了解更多，然后点击About
        print("\n[4/5] Executing AI action: '点击了解更多，然后点击About'...")
        print("    Note: This may take a moment as it involves AI processing...")
        
        try:
            await agent.ai_act("点击了解更多，然后点击About")
            print("    ✓ AI action completed")
        except Exception as e:
            print(f"    ⚠ AI action failed: {e}")
            print("    This is expected on example.com which has limited interactive elements")
        
        # 等待页面变化
        await asyncio.sleep(2)
        
        # 执行AI断言
        print("\n[5/5] Executing AI assertion: '页面上有一些文字内容'...")
        
        try:
            await agent.ai_assert("页面上有一些文字内容")
            print("    ✓ AI assertion passed")
        except AssertionError as e:
            print(f"    ✗ AI assertion failed: {e}")
        except Exception as e:
            print(f"    ⚠ AI assertion error: {e}")
        
        print("\n" + "=" * 60)
        print("Demo completed!")
        print("The browser will stay open for 5 seconds so you can see the result.")
        print("=" * 60)
        
        # 保持浏览器打开一会儿让用户看到结果
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\nCleaning up...")
        if context:
            await context.close()
        if browser:
            await browser.close()
        print("Done!")


if __name__ == "__main__":
    # 检查环境变量
    required_vars = [
        "MIDSCENE_MODEL_NAME",
        "MIDSCENE_MODEL_BASE_URL", 
        "MIDSCENE_MODEL_API_KEY",
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("⚠ Warning: The following environment variables are not set:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease copy .env.example to .env and configure your settings.")
        print("Or set the environment variables directly.\n")
    
    # 运行主函数
    asyncio.run(main())
