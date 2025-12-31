"""
CLI主入口

从 packages/cli/src/index.ts 迁移
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from mspy import __version__
from mspy.cli.batch_runner import BatchRunner
from mspy.cli.config import (
    BatchRunnerConfig,
    create_config,
    create_files_config,
    match_yaml_files,
)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="""Midscene.py - AI驱动的浏览器自动化工具

帮助您通过AI实现浏览器操作自动化、断言和数据提取。
主页: https://midscenejs.com
Github: https://github.com/web-infra-dev/midscene
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        help="YAML脚本文件或目录的路径",
    )
    
    parser.add_argument(
        "--files",
        nargs="+",
        help="要运行的YAML文件列表，用空格分隔",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径",
    )
    
    parser.add_argument(
        "--summary",
        type=str,
        default="summary.json",
        help="摘要输出文件路径 (默认: summary.json)",
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="并发执行数量 (默认: 1)",
    )
    
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="即使某些任务失败也继续执行",
    )
    
    parser.add_argument(
        "--headed",
        action="store_true",
        help="在有头模式下运行浏览器，显示浏览器界面",
    )
    
    parser.add_argument(
        "--keep-window",
        action="store_true",
        help="脚本执行完成后保持浏览器窗口打开（调试用）",
    )
    
    parser.add_argument(
        "--dotenv-override",
        action="store_true",
        help=".env文件中的变量是否覆盖全局变量",
    )
    
    parser.add_argument(
        "--dotenv-debug",
        action="store_true",
        help="启用dotenv调试日志",
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"mspy {__version__}",
    )
    
    return parser.parse_args()


async def run_cli() -> int:
    """运行CLI"""
    args = parse_args()
    
    welcome = f"\n欢迎使用 mspy v{__version__}\n"
    print(welcome)
    
    config_file = args.config
    cmd_files = args.files
    path = args.path
    
    if not config_file and not path and not cmd_files:
        print("错误: 未提供脚本路径、文件或配置", file=sys.stderr)
        return 1
    
    # 配置选项
    config_options = {
        "concurrent": args.concurrent,
        "continue_on_error": args.continue_on_error,
        "summary": args.summary,
        "headed": args.headed,
        "keep_window": args.keep_window,
        "dotenv_override": args.dotenv_override,
        "dotenv_debug": args.dotenv_debug,
    }
    
    config: Optional[BatchRunnerConfig] = None
    
    if config_file:
        config = create_config(config_file, config_options)
        print(f"   配置文件: {config_file}")
    elif cmd_files:
        print("   执行来自 --files 参数的YAML文件...")
        config = create_files_config(cmd_files, config_options)
    elif path:
        files = match_yaml_files(path)
        if not files:
            print(f"错误: 在 {path} 中未找到YAML文件", file=sys.stderr)
            return 1
        print("   执行YAML文件...")
        config = create_files_config(files, config_options)
    
    if not config:
        print("错误: 无法创建有效的配置", file=sys.stderr)
        return 1
    
    # 加载.env文件
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        print(f"   环境文件: {dotenv_path}")
        load_dotenv(
            dotenv_path,
            override=config.dotenv_override,
        )
    
    # 执行批量运行
    executor = BatchRunner(config)
    await executor.run()
    
    success = executor.print_execution_summary()
    
    if config.keep_window:
        import time
        while True:
            print("浏览器仍在运行，使用 Ctrl+C 停止")
            time.sleep(5)
    
    return 0 if success else 1


def main() -> None:
    """CLI入口点"""
    try:
        exit_code = asyncio.run(run_cli())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
