"""
示例 pytest 用例：将 YAML 当作测试。
运行前请确保安装 playwright：pip install playwright && playwright install
"""

import os
import pytest

from mspy.core.yaml_runner import YamlScriptRunner
from mspy.shared.config import RuntimeConfig


@pytest.mark.skipif(
    bool(os.environ.get("MSPY_SKIP_E2E")),
    reason="设置 MSPY_SKIP_E2E=1 可跳过浏览器依赖",
)
def test_basic_yaml():
    runner = YamlScriptRunner(config=RuntimeConfig(headless=True))
    report = runner.run(os.path.join(os.path.dirname(__file__), "basic.yaml"))
    assert report.result.status == "done"
