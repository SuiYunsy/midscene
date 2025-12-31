# Midscene Python (mspy)

Midscene Python 是 [Midscene.js](https://midscenejs.com) 的 Python 实现版本，提供 AI 驱动的 UI 自动化能力。

## 功能特性

- **ai_act**: 使用自然语言描述执行 UI 操作
- **ai_assert**: 使用自然语言进行 UI 断言验证
- **Playwright 集成**: 支持 Playwright 浏览器自动化
- **qwen3-vl 模型支持**: 使用视觉语言模型进行 UI 理解

## 快速开始

### 1. 创建虚拟环境

使用 [uv](https://github.com/astral-sh/uv) 创建虚拟环境（推荐）：

```bash
cd mspy
uv venv .venv
```

激活虚拟环境：

```bash
# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. 安装依赖

```bash
uv pip install -r requirements.txt
```

### 3. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 4. 配置环境变量

复制示例配置文件并填写您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要的配置：

```env
# 必填：模型配置
MIDSCENE_MODEL_NAME=Local-Qwen3-VL-235B-A22B
MIDSCENE_MODEL_BASE_URL=http://localhost:8000/v1
MIDSCENE_MODEL_API_KEY=your-api-key-here

# 必填：模型家族
MIDSCENE_MODEL_FAMILY=qwen3-vl

# 可选：HTTP代理
MIDSCENE_MODEL_HTTP_PROXY=http://localhost:8888

# 可选：跳过SSL证书验证
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION=true
```

### 5. 运行快速体验脚本

```bash
uv run quick.py
```

## 使用示例

### 基本用法

```python
import asyncio
from mspy import Agent
from mspy.web import create_playwright_page

async def main():
    # 创建浏览器和页面
    browser, page = await create_playwright_page(
        headless=False,
        view_width=1280,
        view_height=720,
    )
    
    # 创建 Agent
    agent = Agent(page)
    
    # 导航到目标页面
    await page.navigate("https://example.com")
    
    # 使用 AI 执行操作
    await agent.ai_act("点击登录按钮")
    await agent.ai_act("输入用户名 test@example.com")
    await agent.ai_act("输入密码 password123")
    await agent.ai_act("点击提交")
    
    # 使用 AI 进行断言
    await agent.ai_assert("页面显示登录成功")
    
    # 关闭浏览器
    await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 高级配置

```python
from mspy import Agent, AgentOpt
from mspy.web import create_playwright_page

async def main():
    # 创建带有 cookies 的浏览器
    browser, page = await create_playwright_page(
        headless=False,
        view_width=1920,
        view_height=1080,
        user_data_dir="/path/to/user/data",  # 持久化用户数据
        cookies=[
            {
                "name": "session",
                "value": "xxx",
                "domain": "example.com",
                "path": "/",
            }
        ],
    )
    
    # 创建带有自定义配置的 Agent
    agent = Agent(
        page,
        opts=AgentOpt(
            replanning_cycle_limit=30,  # 最大重规划次数
            ai_act_context="当前是一个电商网站的购物车页面",  # 上下文提示
        )
    )
    
    # ... 执行操作
```

## 项目结构

```
mspy/
├── __init__.py          # 主入口
├── core/                # 核心模块
│   ├── __init__.py
│   ├── agent.py         # Agent 实现
│   ├── device.py        # 设备抽象接口
│   ├── service.py       # AI 服务
│   ├── task_runner.py   # 任务运行器
│   └── ai_model/        # AI 模型相关
│       ├── __init__.py
│       ├── service_caller.py    # 服务调用
│       ├── conversation_history.py  # 对话历史
│       ├── llm_planning.py      # LLM 规划
│       └── prompt.py            # 提示词
├── shared/              # 共享模块
│   ├── __init__.py
│   ├── logger.py        # 日志
│   ├── env.py           # 环境配置
│   ├── utils.py         # 工具函数
│   ├── types.py         # 类型定义
│   └── img.py           # 图像处理
├── web/                 # Web 集成
│   ├── __init__.py
│   └── playwright.py    # Playwright 集成
├── .env.example         # 环境变量示例
├── requirements.txt     # 依赖
├── quick.py             # 快速体验脚本
└── README.md            # 说明文档
```

## 环境变量说明

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `MIDSCENE_MODEL_NAME` | ✓ | 模型名称 |
| `MIDSCENE_MODEL_BASE_URL` | ✓ | API 基础 URL |
| `MIDSCENE_MODEL_API_KEY` | ✓ | API 密钥 |
| `MIDSCENE_MODEL_FAMILY` | ✓ | 模型家族（qwen3-vl） |
| `MIDSCENE_MODEL_HTTP_PROXY` | - | HTTP 代理 |
| `MIDSCENE_MODEL_SKIP_CERT_VERIFICATION` | - | 跳过 SSL 验证 |
| `MIDSCENE_MODEL_TIMEOUT` | - | 请求超时（毫秒） |
| `MIDSCENE_REPLANNING_CYCLE_LIMIT` | - | 重规划次数限制 |

## 许可证

本项目遵循与 Midscene.js 相同的许可证。
