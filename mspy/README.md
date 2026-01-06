# Midscene Python (mspy)

Midscene 的 Python 实现，提供 AI 驱动的 UI 自动化功能。

## 功能特性

- 🤖 **AI 驱动的 UI 自动化** - 使用自然语言描述来执行 UI 操作
- 🌐 **Playwright 集成** - 支持 Chrome、Firefox、Safari 等主流浏览器
- 📸 **视觉定位** - 基于截图的智能元素定位
- ⚡ **网络空闲等待** - 自动等待网络请求完成后再执行操作

## 支持的模型

- Qwen3-VL (推荐)
- Qwen2.5-VL
- Gemini
- Doubao Vision
- UI-TARS

## 快速开始

### 1. 安装依赖

使用 [uv](https://docs.astral.sh/uv/) 安装依赖：

```bash
cd mspy
uv pip install -r requirements.txt
```

安装 Playwright 浏览器：

```bash
playwright install chromium
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必要配置：

```env
# 模型名称
MIDSCENE_MODEL_NAME=Local-Qwen3-VL-235B-A22B

# API 基础 URL
MIDSCENE_MODEL_BASE_URL=https://your-api-endpoint.com/v1

# API 密钥
MIDSCENE_MODEL_API_KEY=your-api-key-here

# 模型家族 (qwen3-vl, qwen2.5-vl, gemini, doubao-vision, vlm-ui-tars)
MIDSCENE_MODEL_FAMILY=qwen3-vl

# HTTP 代理 (可选)
MIDSCENE_MODEL_HTTP_PROXY=http://127.0.0.1:8888
```

### 3. 运行快速体验脚本

```bash
uv run python quick.py
```

这个脚本会：
1. 启动一个有头浏览器
2. 导航到 example.com
3. 执行 AI 动作：点击了解更多
4. 执行 AI 断言：检查是否出现 Example Domains

## 代码示例

```python
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from mspy.shared import ModelConfigManager
from mspy.web import PlaywrightWebPage
from mspy.core import Agent

# 加载环境变量
load_dotenv()

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 创建 Midscene 页面包装器
        web_page = PlaywrightWebPage(page)
        
        # 创建 Agent
        agent = Agent(
            interface=web_page,
            model_config_manager=ModelConfigManager(),
        )
        
        # 导航到页面
        await web_page.navigate("https://example.com")
        
        # 执行 AI 动作
        await agent.ai_act("点击链接")
        
        # 执行 AI 断言
        await agent.ai_assert("页面包含某些内容")
        
        await browser.close()

asyncio.run(main())
```

## 项目结构

```
mspy/
├── __init__.py          # 主模块导出
├── shared/              # 共享模块
│   ├── __init__.py
│   ├── env.py           # 环境变量配置
│   ├── logger.py        # 日志模块
│   ├── types.py         # 类型定义
│   ├── utils.py         # 工具函数
│   └── img.py           # 图像处理
├── core/                # 核心模块
│   ├── __init__.py
│   ├── agent.py         # AI Agent
│   ├── device.py        # 设备抽象接口
│   ├── service.py       # AI 服务
│   ├── service_caller.py # AI 模型调用
│   ├── prompt.py        # 提示词
│   ├── llm_planning.py  # LLM 规划
│   ├── conversation_history.py  # 对话历史
│   └── task_runner.py   # 任务运行器
├── web/                 # Web 模块
│   ├── __init__.py
│   └── playwright_page.py  # Playwright 集成
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
├── quick.py             # 快速体验脚本
└── README.md            # 说明文档
```

## API 参考

### Agent

主要的 AI 代理类，提供以下方法：

- `ai_act(instruction: str)` - 执行 AI 驱动的动作
- `ai_assert(assertion: str)` - 执行 AI 驱动的断言

### PlaywrightWebPage

Playwright 页面包装器，提供以下方法：

- `navigate(url: str)` - 导航到 URL
- `wait_for_network_idle()` - 等待网络空闲
- `screenshot_base64()` - 获取页面截图

## 注意事项

1. **模型配置** - 必须配置一个支持视觉的模型（VL 模型）
2. **网络代理** - 如果需要通过代理访问 API，请配置 `MIDSCENE_MODEL_HTTP_PROXY`
3. **浏览器** - 默认使用 Chromium，需要先安装 Playwright 浏览器

## 许可证

MIT License
