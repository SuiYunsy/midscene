#!/usr/bin/env python3
"""
Midscene Python 快速体验脚本

这个脚本演示了如何使用Midscene Python进行UI自动化：
1. 启动有头浏览器
2. 导航到example.com
3. 使用AI执行点击操作
4. 使用AI进行断言验证

使用方法:
    # 1. 创建虚拟环境
    uv venv .venv
    
    # 2. 激活虚拟环境
    # Windows: .venv\\Scripts\\activate
    # Linux/Mac: source .venv/bin/activate
    
    # 3. 安装依赖
    uv pip install -r requirements.txt
    
    # 4. 安装 Playwright 浏览器
    playwright install chromium
    
    # 5. 配置环境变量
    # 复制 .env.example 为 .env 并填写您的配置
    
    # 6. 运行脚本
    uv run quick.py
"""

import asyncio
import os
import sys

# 添加mspy到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from mspy import Agent, get_debug
from mspy.web import create_playwright_page

# 设置日志
debug = get_debug('quick')


async def main():
    """主函数"""
    print("=" * 60)
    print("Midscene Python Quick Demo")
    print("=" * 60)
    
    browser = None
    
    try:
        # 创建有头浏览器和页面
        print("\n[Step 1] Launching browser (headed mode)...")
        browser, page = await create_playwright_page(
            headless=False,  # 有头模式
            view_width=1280,
            view_height=720,
        )
        debug("Browser launched successfully")
        
        # 创建Agent
        print("[Step 2] Creating AI Agent...")
        agent = Agent(page)
        debug("Agent created")
        
        # 导航到 example.com
        print("[Step 3] Navigating to example.com...")
        await page.navigate("https://example.com", wait_for_network_idle=True)
        debug("Navigation completed")
        
        # 等待页面加载
        await asyncio.sleep(1)
        
        # 使用AI执行操作
        print("[Step 4] Executing AI action: 点击了解更多，然后点击About...")
        try:
            # 注意：example.com 是一个非常简单的页面，可能没有"了解更多"按钮
            # 这里我们演示如何使用 ai_act
            await agent.ai_act("点击 More information 链接")
            debug("AI action completed")
        except Exception as e:
            print(f"  Note: Action may have failed (expected on example.com): {e}")
            debug(f"Action error: {e}")
        
        # 等待页面响应
        await asyncio.sleep(2)
        
        # 使用AI进行断言
        print("[Step 5] Executing AI assertion: 检查页面内容...")
        try:
            await agent.ai_assert("页面上显示了 Example Domain 或 IANA 相关内容")
            print("  ✓ Assertion passed!")
            debug("AI assertion passed")
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            debug(f"Assertion error: {e}")
        
        print("\n" + "=" * 60)
        print("Demo completed!")
        print("=" * 60)
        
        # 保持浏览器打开一段时间让用户观察
        print("\nBrowser will close in 5 seconds...")
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # 清理
        if browser:
            print("\nClosing browser...")
            await browser.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
