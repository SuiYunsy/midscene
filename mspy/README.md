# Midscene Python

Midscene 的 Python 实现，提供 AI 驱动的 UI 自动化能力。

## 功能特性

- 🤖 **AI 规划** - 使用 LLM 智能规划 UI 操作
- ✅ **AI 断言** - 基于视觉的智能断言
- 🎭 **Playwright 集成** - 完整的 Playwright 浏览器自动化支持
- 🔧 **简单配置** - 通过环境变量快速配置

## 系统要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

## 快速开始

### 1. 安装依赖

使用 uv（推荐）:

```bash
cd mspy
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

uv pip install -r requirements.txt
playwright install chromium
```

使用 pip:

```bash
cd mspy
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

pip install -r requirements.txt
playwright install chromium
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写你的 API Key
```

### 3. 运行示例

```bash
python example.py
```

## 快速体验脚本

创建 `example.py`:

```python
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# 加载环境变量
load_dotenv()

# 导入 Midscene
from mspy import PlaywrightAgent

async def main():
    """快速体验示例：导航到 example 网站并点击了解更多"""
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 导航到示例网站
        await page.goto("https://www.example.com")
        
        # 创建 Midscene Agent
        agent = PlaywrightAgent(page)
        
        # 执行 AI 动作
        await agent.ai_act("点击了解更多")
        
        # 等待查看结果
        await asyncio.sleep(3)
        
        # 关闭浏览器
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 核心 API

### PlaywrightAgent

Playwright 浏览器的 AI 智能体。

```python
from mspy import PlaywrightAgent

# 创建 Agent
agent = PlaywrightAgent(page)

# AI 动作 - 智能规划并执行操作
await agent.ai_act("点击登录按钮")
await agent.ai_act("在用户名输入框输入 test@example.com")

# AI 断言 - 验证页面状态
await agent.ai_assert("页面显示登录成功")
```

### 配置选项

```python
from mspy import PlaywrightAgent, AgentOpt

opts = AgentOpt(
    model_config={
        "MIDSCENE_MODEL_NAME": "qwen-vl-max-latest",
        "MIDSCENE_MODEL_FAMILY": "qwen3-vl",
        "MIDSCENE_MODEL_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "MIDSCENE_MODEL_API_KEY": "your-api-key",
    },
    ai_act_context="这是一个电商网站",  # 提供上下文帮助 AI 理解
)

agent = PlaywrightAgent(page, opts)
```

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `MIDSCENE_MODEL_NAME` | 模型名称 | ✅ |
| `MIDSCENE_MODEL_FAMILY` | 模型家族 (qwen2.5-vl 或 qwen3-vl) | ✅ |
| `MIDSCENE_MODEL_BASE_URL` | API 基础 URL | ✅ |
| `MIDSCENE_MODEL_API_KEY` | API Key | ✅ |
| `MIDSCENE_MODEL_HTTP_PROXY` | HTTP 代理 | ❌ |
| `MIDSCENE_MODEL_TEMPERATURE` | 模型温度 | ❌ |
| `MIDSCENE_MODEL_TIMEOUT` | 请求超时（毫秒） | ❌ |
| `MIDSCENE_DEBUG_MODE` | 调试模式 | ❌ |

## 模块结构

```
mspy/
├── __init__.py          # 主入口
├── shared/              # 共享模块
│   ├── types.py         # 类型定义
│   ├── config.py        # 配置管理
│   ├── logger.py        # 日志工具
│   └── utils.py         # 工具函数
├── core/                # 核心模块
│   ├── agent.py         # Agent 实现
│   ├── service.py       # AI 服务
│   ├── ai_model.py      # AI 模型调用
│   ├── prompts.py       # 提示词
│   └── types.py         # 核心类型
├── web/                 # Web 模块
│   ├── playwright_page.py   # Playwright 页面封装
│   └── playwright_agent.py  # Playwright Agent
├── requirements.txt     # 依赖
├── .env.example         # 环境变量示例
└── README.md           # 说明文档
```

## 注意事项

- 仅支持 qwen2.5-vl 和 qwen3-vl 模型家族
- 仅保留 aiAct 和 aiAssert 功能，其他功能（aiTap、aiScroll 等）暂未实现
- 需要 Playwright 浏览器驱动

## License

MIT
