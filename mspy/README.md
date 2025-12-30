# mspy - Python 版 Midscene

mspy 是 [Midscene.js](https://midscenejs.com/) 的 Python 实现，一个基于 AI 的 UI 自动化测试框架。

## 特性

- 🤖 **AI 驱动的元素定位** - 使用自然语言描述目标元素，AI 自动识别并定位
- 📸 **视觉理解** - 支持多种视觉语言模型（VL Model），如 GPT-4o、Qwen-VL、Gemini 等
- 🎭 **Playwright 集成** - 无缝集成 Playwright，支持 Chromium、Firefox、WebKit
- 🐍 **Python 原生** - 完全使用 Python 3.11+ 实现，无需 Node.js

## 快速开始

### 环境要求

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（推荐的包管理工具）

### 安装

```bash
# 使用 uv 安装依赖
cd mspy
uv sync

# 安装 Playwright 浏览器
uv run playwright install chromium
```

### 配置

1. 复制环境变量示例文件：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的模型配置：

```bash
# 必填配置
MIDSCENE_MODEL_NAME=gpt-4o
MIDSCENE_MODEL_API_KEY=your-api-key-here
MIDSCENE_MODEL_BASE_URL=https://api.openai.com/v1

# 如果使用视觉语言模型，设置模型家族
MIDSCENE_MODEL_FAMILY=qwen2.5-vl
```

### 快速体验

运行快速体验脚本：

```bash
uv run python quick_start.py
```

或者手动编写代码：

```python
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from mspy import PlaywrightAgent

# 加载环境变量
load_dotenv()

async def main():
    # 启动浏览器
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 导航到目标页面
        await page.goto("https://www.baidu.com")
        
        # 创建 AI Agent
        agent = PlaywrightAgent(page)
        
        # 使用自然语言进行操作
        await agent.ai_tap("搜索框")
        await agent.ai_input("搜索框", {"value": "Midscene AI"})
        await agent.ai_tap("百度一下按钮")
        
        # 提取数据
        results = await agent.ai_query("搜索结果的标题列表")
        print("搜索结果:", results)
        
        # 断言验证
        await agent.ai_assert("页面显示了搜索结果")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## API 参考

### PlaywrightAgent

主要的 AI Agent 类，封装了 Playwright 页面操作。

#### 初始化

```python
from mspy import PlaywrightAgent, AgentOpt

agent = PlaywrightAgent(
    page,                    # Playwright Page 对象
    opts=AgentOpt(
        group_name="My Test", # 报告分组名称
        model_config={        # 模型配置覆盖
            "MIDSCENE_MODEL_NAME": "gpt-4o",
        }
    ),
    headless=True            # 是否无头模式
)
```

#### 核心方法

```python
# 点击元素
await agent.ai_tap("登录按钮")
await agent.ai_tap({"prompt": "登录按钮", "deep_think": True})

# 悬停
await agent.ai_hover("用户头像")

# 输入文本
await agent.ai_input("用户名输入框", {"value": "admin"})

# 按键
await agent.ai_keyboard_press(None, {"key_name": "Enter"})
await agent.ai_keyboard_press("搜索框", {"key_name": "Control+a"})

# 滚动
await agent.ai_scroll(None, {"direction": "down", "distance": 300})
await agent.ai_scroll("列表区域", {"scroll_type": "scrollToBottom"})

# 执行复杂任务
await agent.ai_act("登录账户，用户名为 admin，密码为 123456")

# 数据提取
data = await agent.ai_query("页面上的商品列表，包含名称和价格")

# 断言
await agent.ai_assert("页面显示欢迎消息")

# 等待条件
await agent.ai_wait_for("加载完成", timeout_ms=10000)

# 定位元素（返回坐标信息）
result = await agent.ai_locate("提交按钮")
print(result["center"])  # (x, y)
```

### Service

低级 AI 服务类，用于元素定位和数据提取。

```python
from mspy.core import Service

service = Service(context_fn)
result = await service.locate("登录按钮", model_config)
data = await service.extract("用户信息", model_config)
```

## 支持的模型

mspy 支持任何 OpenAI 兼容的 API，包括：

| 模型 | 模型家族 | 说明 |
|------|----------|------|
| GPT-4o | - | OpenAI 多模态模型 |
| Qwen-VL | qwen2.5-vl | 阿里通义千问视觉模型 |
| Qwen3-VL | qwen3-vl | 通义千问 3.0 视觉模型 |
| Doubao Vision | doubao-vision | 字节豆包视觉模型 |
| Gemini | gemini | Google Gemini 模型 |
| UI-TARS | vlm-ui-tars | UI 理解专用模型 |

## 项目结构

```
mspy/
├── __init__.py          # 主入口
├── pyproject.toml       # 项目配置
├── .env.example         # 环境变量示例
├── quick_start.py       # 快速体验脚本
├── shared/              # 共享模块
│   ├── types.py         # 类型定义
│   ├── utils.py         # 工具函数
│   ├── logger.py        # 日志模块
│   ├── common.py        # 通用功能
│   └── env/             # 环境配置
├── core/                # 核心模块
│   ├── types.py         # 类型定义
│   ├── common.py        # 通用功能
│   ├── service/         # AI 服务
│   ├── agent/           # Agent 实现
│   └── ai_model/        # AI 模型调用
│       └── prompt/      # 提示词模板
└── web/                 # Web 集成
    ├── page.py          # Playwright 页面封装
    └── agent.py         # Playwright Agent
```

## 与 TypeScript 版本的差异

1. **类名和方法名** - 使用 Python 风格的 snake_case
2. **异步编程** - 使用 `async/await` 语法
3. **类型注解** - 使用 Python 类型提示
4. **配置管理** - 使用 python-dotenv 加载环境变量

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
