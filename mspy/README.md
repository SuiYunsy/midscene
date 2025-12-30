# Midscene Python Port (mspy)

该目录提供 Midscene `core`、`shared`、`web-integration` 的 Python 3.11 版本实现，方便在纯 Python 环境运行。

## 目录结构

- `mspy/shared`：环境变量、日志、通用类型。
- `mspy/core`：AI 调度、计划、定位与任务编排。
- `mspy/web`：基于 Playwright 的浏览器执行层。
- `quickstart.py`：快速体验脚本。

## 快速开始

1. 在仓库根目录创建 `.env`（可参考 `.env.example`），至少提供：
   ```env
   OPENAI_API_KEY=your_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   MIDSCENE_MODEL=gpt-4o-mini
   ```
2. 安装 uv（https://docs.astral.sh/uv/）。
3. 在本目录下安装依赖并运行：
   ```bash
   cd mspy
   uv sync
   uv run python quickstart.py --url https://example.org --instruction "describe the page"
   ```

日志为英文，核心注释为中文，方便调试与二次开发。
