from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from mspy.shared.config import RuntimeConfig
from mspy.core.yaml_runner import YamlScriptRunner

app = typer.Typer(add_completion=False, help="Midscene Python CLI")
console = Console()


@app.command()
def run(yaml_path: str, headless: bool = True) -> None:
    """
    运行单个 YAML 脚本。
    中文注释：默认使用无头浏览器，可通过 --headless false 打开可视化调试。
    """

    path = Path(yaml_path)
    if not path.exists():
        typer.echo(f"未找到文件: {yaml_path}")
        raise typer.Exit(code=1)

    runner = YamlScriptRunner(config=RuntimeConfig(headless=headless))
    report = runner.run(path)
    if report.result.output_path:
        console.print(f"[green]完成[/green] 报告: {report.result.output_path}")
    else:
        console.print("[green]完成[/green]")


@app.command("pytest")
def run_with_pytest(yaml_path: str, headless: bool = True) -> None:
    """
    通过 pytest 方式运行 YAML。
    中文注释：将 YAML 视为测试用例，便于 CI 集成。
    """

    try:
        import pytest  # noqa: WPS433
    except ImportError:
        typer.echo("需要安装 pytest：pip install pytest")
        raise typer.Exit(code=1)

    script = Path(yaml_path).resolve()

    def _pytest_adapter() -> None:
        runner = YamlScriptRunner(config=RuntimeConfig(headless=headless))
        report = runner.run(script)
        assert report.result.status == "done", report.result

    # 动态注册一个临时测试函数
    def test_yaml() -> None:  # type: ignore
        _pytest_adapter()

    # 将动态生成的用例注入到模块级别，便于 pytest 发现
    globals()["test_yaml"] = test_yaml

    raise SystemExit(pytest.main([__file__]))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
