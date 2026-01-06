# mspy

Midscene 的 Python 版本实现，提供以下模块：

- `mspy.shared`：通用工具与配置（日志、缓存、YAML 解析、报告）。
- `mspy.core`：核心工作流，负责加载 YAML、调度任务、调用统一动作接口。
- `mspy.web_integration`：基于 Python Playwright 的浏览器适配层，只保留 Web 能力。
- `mspy.cli`：命令行入口，支持直接运行 YAML 脚本，也可通过 `pytest` 管理 YAML（将 YAML 视作测试用例）。

## 安装与运行

```bash
cd mspy
pip install -e .
playwright install  # 首次使用需要安装浏览器

# 运行单个 YAML
mspy run examples/basic.yaml --headless

# 通过 pytest 运行 YAML（需要安装 pytest）
pytest examples/test_basic.py
```

> 说明：本目录为独立的 Python 包，未与原有 TS 构建链路耦合；需要 Python 3.10+。
