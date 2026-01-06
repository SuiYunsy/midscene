"""
CLI主入口

对应TypeScript源码: packages/cli/src/index.ts
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

from mspy.shared.common import get_version


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Midscene CLI - AI驱动的UI自动化测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  mspy script.yaml                    # 执行单个YAML脚本
  mspy ./scripts/                     # 执行目录下所有YAML脚本
  mspy --config midscene.config.yaml  # 使用配置文件执行
  mspy script1.yaml script2.yaml      # 执行多个脚本

更多信息请访问: https://midscenejs.com
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        help='YAML脚本文件或目录路径'
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        help='要执行的YAML文件列表'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--concurrent',
        type=int,
        default=1,
        help='并发执行数量 (默认: 1)'
    )
    
    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='错误时继续执行'
    )
    
    parser.add_argument(
        '--summary',
        default='summary.json',
        help='摘要输出文件名 (默认: summary.json)'
    )
    
    parser.add_argument(
        '--share-browser-context',
        action='store_true',
        help='共享浏览器上下文'
    )
    
    parser.add_argument(
        '--headed',
        action='store_true',
        help='有头模式运行浏览器'
    )
    
    parser.add_argument(
        '--keep-window',
        action='store_true',
        help='执行完成后保持浏览器窗口'
    )
    
    parser.add_argument(
        '--dotenv-override',
        action='store_true',
        help='环境变量覆盖.env文件'
    )
    
    parser.add_argument(
        '--dotenv-debug',
        action='store_true',
        help='调试.env加载'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='Web模式'
    )
    
    parser.add_argument(
        '--android',
        action='store_true',
        help='Android模式'
    )
    
    parser.add_argument(
        '--ios',
        action='store_true',
        help='iOS模式'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'mspy {get_version()}'
    )
    
    return parser.parse_args()


def match_yaml_files(path: str) -> List[str]:
    """匹配目录下的YAML文件
    
    Args:
        path: 目录或文件路径
        
    Returns:
        匹配的YAML文件列表
    """
    path_obj = Path(path)
    
    if path_obj.is_file():
        if path_obj.suffix.lower() in ('.yaml', '.yml'):
            return [str(path_obj)]
        return []
    
    if path_obj.is_dir():
        files = []
        for ext in ('*.yaml', '*.yml'):
            files.extend(str(f) for f in path_obj.glob(ext))
            files.extend(str(f) for f in path_obj.glob(f'**/{ext}'))
        return sorted(set(files))
    
    return []


async def run_cli():
    """运行CLI"""
    args = parse_args()
    
    print(f"\n欢迎使用 mspy v{get_version()}\n")
    
    # 检查参数
    if not args.path and not args.files and not args.config:
        print("错误: 未提供脚本路径、文件或配置")
        sys.exit(1)
    
    from mspy.cli.batch_runner import BatchRunner, BatchRunnerConfig
    from mspy.cli.config import create_config, create_files_config
    
    # 创建配置
    config_options = {
        'concurrent': args.concurrent,
        'continue_on_error': args.continue_on_error,
        'summary': args.summary,
        'share_browser_context': args.share_browser_context,
        'headed': args.headed,
        'keep_window': args.keep_window,
        'dotenv_override': args.dotenv_override,
        'dotenv_debug': args.dotenv_debug,
        'web': args.web,
        'android': args.android,
        'ios': args.ios,
    }
    
    config = None
    
    if args.config:
        config = await create_config(args.config, config_options)
        print(f"   配置文件: {args.config}")
    elif args.files:
        print("   从 --files 参数执行YAML文件...")
        config = await create_files_config(args.files, config_options)
    elif args.path:
        files = match_yaml_files(args.path)
        if not files:
            print(f"错误: 在 {args.path} 中未找到YAML文件")
            sys.exit(1)
        print("   执行YAML文件...")
        config = await create_files_config(files, config_options)
    
    if not config:
        print("错误: 无法创建有效配置")
        sys.exit(1)
    
    # 加载.env文件
    env_file = Path.cwd() / '.env'
    if env_file.exists():
        print(f"   环境文件: {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv(
                env_file,
                override=config.dotenv_override
            )
        except ImportError:
            print("   警告: python-dotenv未安装，跳过.env加载")
    
    # 执行
    runner = BatchRunner(config)
    await runner.run()
    
    # 打印摘要
    success = runner.print_execution_summary()
    
    if config.keep_window:
        print("浏览器仍在运行，使用Ctrl+C停止")
        try:
            while True:
                await asyncio.sleep(5)
                print("浏览器仍在运行，使用Ctrl+C停止")
        except KeyboardInterrupt:
            pass
    else:
        sys.exit(0 if success else 1)


def main():
    """CLI入口点"""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
