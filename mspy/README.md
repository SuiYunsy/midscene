# Midscene Python SDK (mspy)

基于AI的UI自动化框架的Python实现。

## 简介

Midscene Python SDK 是 [Midscene.js](https://midscenejs.com) 的Python版本实现，提供了基于AI视觉语言模型（VL Model）的UI自动化能力。通过自然语言描述，即可实现对Web页面的智能操作。

## 特性

- 🤖 **AI驱动**：使用视觉语言模型（如 qwen3-vl）进行元素定位和动作规划
- 🎭 **Playwright集成**：支持Playwright进行Web自动化
- 💬 **自然语言交互**：使用中文或英文描述你想要执行的操作
- 🔄 **自动重规划**：当动作失败时，自动进行重规划和恢复
- ⏳ **等待网络空闲**：自动等待页面加载完成

## 安装

### 使用 uv（推荐）

```bash
# 进入mspy目录
cd mspy

# 创建虚拟环境
uv venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 安装依赖
uv pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 使用 pip

```bash
# 进入mspy目录
cd mspy

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

## 配置

1. 复制环境配置示例文件：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置你的模型服务：

```bash
# 模型配置
MIDSCENE_MODEL_NAME=Local-Qwen3-VL-235B-A22B
MIDSCENE_MODEL_FAMILY=qwen3-vl
MIDSCENE_MODEL_BASE_URL=https://your-api-endpoint.com/v1
MIDSCENE_MODEL_API_KEY=your-api-key-here

# HTTP代理（可选）
MIDSCENE_MODEL_HTTP_PROXY=http://localhost:8888

# 跳过证书验证（如使用代理或自签名证书）
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION=true
```

## 快速开始

### 运行示例脚本

```bash
# 使用 uv 运行
uv run quick.py

# 或者激活虚拟环境后直接运行
python quick.py
```

### 基础用法

```python
import asyncio
from mspy import Agent
from mspy.web import create_playwright_page

async def main():
    # 创建Playwright页面
    web_page, browser, context = await create_playwright_page(
        url="https://example.com",
        headless=False,  # 有头模式，可以看到浏览器
    )
    
    # 创建Agent
    agent = Agent(web_page)
    
    # 执行AI动作
    await agent.ai_act("点击登录按钮")
    
    # 执行AI断言
    await agent.ai_assert("页面显示登录表单")
    
    # 等待条件成立
    await agent.ai_wait_for("加载完成", timeout_ms=10000)
    
    # 关闭浏览器
    await browser.close()

asyncio.run(main())
```

## API 参考

### Agent

```python
from mspy import Agent

agent = Agent(interface, opts)
```

**方法：**

- `ai_act(task_prompt)`: 执行AI动作，使用自然语言描述任务
- `ai_assert(assertion, msg)`: 执行AI断言，验证页面状态
- `ai_wait_for(assertion, timeout_ms, check_interval_ms)`: 等待断言成立
- `ai_locate(prompt)`: 定位元素，返回元素位置信息

### create_playwright_page

```python
from mspy.web import create_playwright_page

web_page, browser, context = await create_playwright_page(
    url="https://example.com",
    headless=False,
    viewport_width=1280,
    viewport_height=720,
    user_data_dir=None,  # 可选：用户数据目录
    cookies=None,  # 可选：Cookies列表
    local_storage=None,  # 可选：LocalStorage键值对
)
```

## 支持的模型

目前SDK主要支持 `qwen3-vl` 模型家族。请确保你的模型服务兼容 OpenAI API 格式。

配置模型：

```bash
MIDSCENE_MODEL_FAMILY=qwen3-vl
MIDSCENE_MODEL_NAME=你的模型名称
```

## 目录结构

```
mspy/
├── __init__.py          # 主入口
├── core/                # 核心模块
│   ├── agent.py         # Agent实现
│   ├── device.py        # 设备抽象接口
│   ├── service.py       # 服务模块
│   ├── service_caller.py # AI模型调用
│   ├── llm_planning.py  # LLM规划
│   └── task_executor.py # 任务执行器
├── shared/              # 共享模块
│   ├── types.py         # 类型定义
│   ├── env.py           # 环境配置
│   ├── logger.py        # 日志模块
│   ├── img.py           # 图像处理
│   └── utils.py         # 工具函数
├── web/                 # Web集成模块
│   └── playwright_page.py  # Playwright页面
├── quick.py             # 快速体验脚本
├── requirements.txt     # 依赖列表
├── .env.example         # 环境配置示例
└── README.md            # 本文件
```

## 常见问题

### Q: 如何配置代理？

在 `.env` 文件中设置：
```bash
MIDSCENE_MODEL_HTTP_PROXY=http://localhost:8888
```

### Q: 证书验证失败怎么办？

如果使用代理或自签名证书，设置：
```bash
MIDSCENE_MODEL_SKIP_CERT_VERIFICATION=true
```

### Q: 如何调试？

设置调试模式：
```bash
MIDSCENE_DEBUG_MODE=true
```

### Q: 超时时间如何调整？

```bash
MIDSCENE_MODEL_TIMEOUT=60000  # 毫秒
```

## 许可证

MIT License

## 相关链接

- [Midscene.js 官网](https://midscenejs.com)
- [Midscene.js GitHub](https://github.com/AIMidscene/midscene)
