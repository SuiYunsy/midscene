#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Midscene Python SDK 快速体验脚本

这个脚本演示如何使用 Midscene Python SDK 进行AI驱动的Web自动化。
使用有头模式（headless=False）以便观察执行过程。

使用方法:
1. 复制 .env.example 为 .env 并配置好模型参数
2. 安装依赖: uv pip install -r requirements.txt
3. 安装Playwright浏览器: playwright install chromium
4. 运行脚本: uv run quick.py
"""

import asyncio
import os
import sys

# 添加父目录到路径，以便导入 mspy 包
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, '.env'))

from playwright.async_api import async_playwright
from mspy.web import PlaywrightAgent


async def main():
    """主函数：演示Midscene AI驱动的Web自动化"""
    
    print("=" * 60)
    print("Midscene Python SDK 快速体验")
    print("=" * 60)
    
    # 启动浏览器（有头模式）
    async with async_playwright() as p:
        print("\n[1] 启动Chromium浏览器（有头模式）...")
        browser = await p.chromium.launch(
            headless=False,  # 有头模式，可以看到浏览器界面
            slow_mo=500,     # 放慢操作速度，便于观察
        )
        
        # 创建新页面
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        
        # 创建PlaywrightAgent
        print("[2] 创建PlaywrightAgent...")
        agent = PlaywrightAgent(page)
        
        try:
            # 导航到example.com
            print("\n[3] 导航到 example.com ...")
            await page.goto("https://example.com")
            await agent.wait_for_network_idle(timeout=5000)
            print("    页面加载完成！")
            
            # 使用AI执行动作
            print("\n[4] 执行 AI 动作: '点击了解更多，然后点击About'")
            print("    注意：example.com 是一个简单的示例页面，可能没有这些元素。")
            print("    这只是演示AI如何理解和执行自然语言指令。")
            
            try:
                await agent.ai_act("点击 More information 链接")
                print("    AI 动作执行完成！")
            except Exception as e:
                print(f"    AI 动作执行失败（这是预期的，因为example.com很简单）: {e}")
            
            # 等待一下让用户观察
            await asyncio.sleep(2)
            
            # 执行AI断言
            print("\n[5] 执行 AI 断言: '页面包含 Example Domain'")
            try:
                await agent.ai_assert("页面包含 Example Domain 字样")
                print("    断言通过！")
            except AssertionError as e:
                print(f"    断言失败: {e}")
            
            print("\n[6] 演示完成！")
            
            # 等待用户观察
            print("\n按 Ctrl+C 退出...")
            await asyncio.sleep(10)
            
        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"\n发生错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理
            print("\n[7] 关闭浏览器...")
            await agent.destroy()
            await context.close()
            await browser.close()
    
    print("\n" + "=" * 60)
    print("演示结束")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
