"""
CLI主入口

提供命令行界面。
"""

import argparse
import asyncio
import sys
import logging
from pathlib import Path
from typing import List, Optional

from mspy.cli.yaml_player import create_yaml_player
from mspy.cli.batch_runner import BatchRunner, BatchRunnerConfig


def setup_logging(verbose: bool = False) -> None:
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog="mspy",
        description="Midscene Python CLI - AI驱动的UI自动化测试工具",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # run命令
    run_parser = subparsers.add_parser("run", help="运行YAML脚本")
    run_parser.add_argument(
        "files",
        nargs="+",
        help="YAML脚本文件路径",
    )
    run_parser.add_argument(
        "--headed",
        action="store_true",
        help="以有头模式运行浏览器",
    )
    run_parser.add_argument(
        "--keep-window",
        action="store_true",
        help="运行结束后保持浏览器窗口",
    )
    run_parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="并发执行数量",
    )
    run_parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="出错时继续执行",
    )
    run_parser.add_argument(
        "--summary",
        default="summary.json",
        help="结果摘要文件名",
    )
    run_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出",
    )
    
    # version命令
    version_parser = subparsers.add_parser("version", help="显示版本信息")
    
    return parser


async def run_command(args: argparse.Namespace) -> int:
    """执行run命令"""
    files = args.files
    
    # 验证文件存在
    valid_files: List[str] = []
    for file in files:
        path = Path(file)
        if path.exists():
            valid_files.append(str(path.absolute()))
        else:
            print(f"错误: 文件不存在: {file}", file=sys.stderr)
            return 1
    
    if not valid_files:
        print("错误: 没有有效的文件", file=sys.stderr)
        return 1
    
    # 创建批量运行器配置
    config = BatchRunnerConfig(
        files=valid_files,
        concurrent=args.concurrent,
        continue_on_error=args.continue_on_error,
        summary=args.summary,
        share_browser_context=False,
        headed=args.headed,
        keep_window=args.keep_window,
    )
    
    # 运行
    runner = BatchRunner(config)
    results = await runner.run()
    
    # 打印摘要
    success = runner.print_execution_summary()
    
    return 0 if success else 1


def main() -> None:
    """CLI入口"""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    if args.command == "version":
        from mspy import __version__
        print(f"mspy version {__version__}")
        sys.exit(0)
    
    if args.command == "run":
        setup_logging(getattr(args, "verbose", False))
        exit_code = asyncio.run(run_command(args))
        sys.exit(exit_code)
    
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
