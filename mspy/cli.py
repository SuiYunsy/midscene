#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mspy 命令行入口
提供命令行接口来运行 mspy。
"""

import argparse
import asyncio
import sys
from pathlib import Path


def main():
    """主命令行入口"""
    parser = argparse.ArgumentParser(
        description="mspy - Python implementation of Midscene",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mspy run script.yaml          Run a YAML script
  mspy --version                Show version

For more information, visit: https://midscenejs.com
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="mspy 1.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="Run a YAML script")
    run_parser.add_argument(
        "script",
        help="Path to the YAML script file"
    )
    run_parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run in headless mode"
    )
    run_parser.add_argument(
        "--url",
        type=str,
        help="Initial URL to navigate to"
    )
    
    args = parser.parse_args()
    
    if args.command == "run":
        asyncio.run(run_script(args.script, args.headless, args.url))
    else:
        parser.print_help()


async def run_script(script_path: str, headless: bool = False, url: str = None):
    """
    运行 YAML 脚本
    
    Args:
        script_path: 脚本文件路径
        headless: 是否无头模式
        url: 初始 URL
    """
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed, using system environment variables only")
    
    from playwright.async_api import async_playwright
    from mspy.core.yaml import parse_yaml_script, ScriptPlayer
    from mspy.web import PlaywrightAgent
    
    # 读取脚本
    path = Path(script_path)
    if not path.exists():
        print(f"Error: Script file not found: {script_path}")
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    script = parse_yaml_script(content, script_path)
    
    print(f"[Info] Running script: {script_path}")
    print(f"[Info] Tasks: {len(script.tasks)}")
    
    async def setup_agent(target):
        """设置 Agent"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page()
            
            # 导航到初始 URL
            initial_url = url or (target.get("url") if target else None)
            if initial_url:
                await page.goto(initial_url)
            
            agent = PlaywrightAgent(page, headless=headless)
            
            async def cleanup():
                await browser.close()
            
            return {
                "agent": agent,
                "free_fn": [{"name": "close-browser", "fn": cleanup}],
            }
    
    # 创建播放器
    def on_status_change(status):
        print(f"[Task {status.get('index', 0) + 1}] {status.get('name', 'Unknown')}: {status.get('status', 'unknown')}")
    
    player = ScriptPlayer(
        script=script,
        setup_agent=setup_agent,
        on_task_status_change=on_status_change,
        script_path=script_path,
    )
    
    # 运行脚本
    await player.run()
    
    if player.status == "done":
        print("\n[Success] Script completed successfully!")
        if player.output:
            print(f"[Output] Results saved to: {player.output}")
    else:
        print(f"\n[Error] Script failed with status: {player.status}")
        if player.error_in_setup:
            print(f"[Error] {player.error_in_setup}")
        sys.exit(1)


if __name__ == "__main__":
    main()
