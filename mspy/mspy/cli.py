from __future__ import annotations

from pathlib import Path
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
        typer.echo(f"File not found: {yaml_path}")
        raise typer.Exit(code=1)

    runner = YamlScriptRunner(config=RuntimeConfig(headless=headless))
    report = runner.run(path)
    if report.result.output_path:
        console.print(f"[green]Done[/green] Report: {report.result.output_path}")
    else:
        console.print("[green]Done[/green]")


@app.command("pytest")
def run_with_pytest(yaml_path: str, headless: bool = True) -> None:
    """
    通过 pytest 方式运行 YAML。
    中文注释：将 YAML 视为测试用例，便于 CI 集成。
    """

    try:
        # 延迟引入可选依赖，避免未安装 pytest 时阻塞 CLI 的其他功能
        import pytest
    except ImportError:
        typer.echo("pytest is required: pip install pytest")
        raise typer.Exit(code=1)

    import tempfile

    script = Path(yaml_path).resolve()

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_yaml.py"
        content = f"""
import pathlib
from mspy.core.yaml_runner import YamlScriptRunner
from mspy.shared.config import RuntimeConfig


def test_yaml_script():
    runner = YamlScriptRunner(config=RuntimeConfig(headless={headless}))
    report = runner.run(pathlib.Path({repr(str(script))}))
    assert report.result.status == "done"
"""
        test_file.write_text(content.strip() + "\n", encoding="utf-8")
        raise SystemExit(pytest.main([str(test_file)]))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
