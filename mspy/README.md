# Midscene Python SDK

Midscene Python SDK 是 Midscene 的 Python 实现，提供 AI 驱动的 Web 自动化能力。

## 特性

- 🤖 AI 驱动的 Web 自动化
- 🎯 自然语言指令执行（aiAct）
- ✅ AI 断言验证（aiAssert）
- 🌐 Playwright 集成
- 🔧 支持 qwen3-vl 视觉语言模型

## 快速开始

### 1. 创建虚拟环境

使用 `uv` 创建虚拟环境：

```bash
cd mspy
uv venv
```

### 2. 激活虚拟环境

```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
uv pip install -r requirements.txt
```

### 4. 安装 Playwright 浏览器

```bash
playwright install chromium
```

### 5. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写模型配置：

```env
MIDSCENE_MODEL_NAME=Local-Qwen3-VL-235B-A22B
MIDSCENE_MODEL_BASE_URL=http://localhost:8000/v1
MIDSCENE_MODEL_API_KEY=your-api-key-here
MIDSCENE_MODEL_FAMILY=qwen3-vl
MIDSCENE_MODEL_HTTP_PROXY=http://localhost:8888
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION=true
```

### 6. 运行快速体验脚本

```bash
cd mspy
uv run quick.py
```

或者从仓库根目录运行:

```bash
uv run mspy/quick.py
```

## 使用示例

```python
import asyncio
from playwright.async_api import async_playwright
from web import PlaywrightAgent

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 创建 Agent
        agent = PlaywrightAgent(page)
        
        # 导航
        await page.goto("https://example.com")
        await agent.wait_for_network_idle()
        
        # AI 动作
        await agent.ai_act("点击登录按钮")
        
        # AI 断言
        await agent.ai_assert("页面显示登录成功")
        
        # 清理
        await agent.destroy()
        await browser.close()

asyncio.run(main())
```

## 模块结构

```
mspy/
├── shared/          # 共享模块
│   ├── logger.py    # 日志
│   ├── env.py       # 环境配置
│   ├── types.py     # 类型定义
│   ├── utils.py     # 工具函数
│   └── img.py       # 图像处理
├── core/            # 核心模块
│   ├── agent.py     # Agent 主类
│   ├── service.py   # AI 服务
│   ├── device.py    # 设备抽象接口
│   ├── task_runner.py       # 任务运行器
│   ├── task_executor.py     # 任务执行器
│   ├── llm_planning.py      # LLM 规划
│   ├── service_caller.py    # AI 服务调用
│   ├── conversation_history.py  # 对话历史
│   └── common.py    # 通用函数
├── web/             # Web 集成模块
│   ├── playwright_page.py   # Playwright 页面
│   └── playwright_agent.py  # Playwright Agent
├── .env.example     # 环境变量示例
├── requirements.txt # 依赖
├── quick.py         # 快速体验脚本
└── README.md        # 说明文档
```

## 配置说明

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `MIDSCENE_MODEL_NAME` | 模型名称 | `Local-Qwen3-VL-235B-A22B` |
| `MIDSCENE_MODEL_BASE_URL` | 模型 API 地址 | `http://localhost:8000/v1` |
| `MIDSCENE_MODEL_API_KEY` | API 密钥 | `your-api-key` |
| `MIDSCENE_MODEL_FAMILY` | 模型家族 | `qwen3-vl` |
| `MIDSCENE_MODEL_HTTP_PROXY` | HTTP 代理 | `http://localhost:8888` |
| `MIDSCENE_MODEL_SKIP_CERT_VERIFICATION` | 跳过证书验证 | `true` |
| `MIDSCENE_MODEL_TIMEOUT` | 超时时间(毫秒) | `600000` |
| `MIDSCENE_REPLANNING_CYCLE_LIMIT` | 重新规划次数限制 | `20` |

## API 参考

### PlaywrightAgent

主要方法：

- `ai_act(prompt)` - 执行 AI 驱动的动作
- `ai_assert(assertion)` - 执行 AI 断言
- `wait_for_network_idle(timeout)` - 等待网络空闲
- `navigate(url)` - 导航到 URL
- `destroy()` - 销毁 Agent

## 注意事项

- 本 SDK 目前仅支持 `qwen3-vl` 模型家族
- 需要 Python 3.11 或更高版本
- Playwright 需要单独安装浏览器驱动

## 许可证

MIT License
