# Midscene Python SDK (mspy)

AI驱动的UI自动化测试SDK - Python版本

## 简介

mspy是Midscene SDK的Python实现，提供基于AI的UI自动化测试能力。它可以通过自然语言描述来定位页面元素、执行操作、提取数据和进行断言验证。

## 功能特性

- 🤖 **AI驱动**: 使用自然语言描述进行元素定位和操作
- 🌐 **Web自动化**: 集成Playwright实现Web自动化测试
- 📝 **YAML脚本**: 支持YAML格式的测试脚本
- 🛠 **CLI工具**: 提供命令行工具批量执行测试
- 📊 **报告生成**: 自动生成测试报告

## 安装

### 使用 uv（推荐）

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包管理器，推荐使用：

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
cd mspy
uv venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

uv pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install
```

### 使用 pip

```bash
pip install -r mspy/requirements.txt
playwright install
```

### 开发模式安装

```bash
pip install -e ./mspy
```

## 环境变量配置

### 创建 .env 文件

在项目根目录创建 `.env` 文件来配置 AI 模型：

```bash
# .env 文件示例

# AI 模型配置（必需）
MIDSCENE_MODEL_NAME=gpt-4o
MIDSCENE_MODEL_API_KEY=your-api-key-here

# API 基础 URL（可选，默认为 OpenAI）
MIDSCENE_MODEL_BASE_URL=https://api.openai.com/v1

# 模型家族（使用视觉语言模型时需要设置）
# 可选值: qwen2.5-vl, qwen3-vl, doubao-vision, gemini, vlm-ui-tars
MIDSCENE_MODEL_FAMILY=qwen2.5-vl

# 调试模式（可选）
MIDSCENE_DEBUG_MODE=false

# 缓存配置（可选）
MIDSCENE_CACHE=false
```

### 在代码中加载 .env

```python
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 现在可以使用 mspy
from mspy.web import PlaywrightAgent
```

### 使用 CLI 时自动加载

CLI 工具会自动查找并加载当前目录下的 `.env` 文件。

## 快速开始

### 使用Python代码

```python
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from mspy.web import PlaywrightAgent

# 加载环境变量
load_dotenv()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://example.com')
        
        # 创建Agent
        agent = PlaywrightAgent(page)
        
        # 使用AI执行操作
        await agent.ai_tap('登录按钮')
        await agent.ai_input('用户名输入框', 'test@example.com')
        await agent.ai_input('密码输入框', 'password123')
        await agent.ai_tap('提交按钮')
        
        # 断言验证
        await agent.ai_assert('页面显示欢迎信息')
        
        await browser.close()

asyncio.run(main())
```

### 使用YAML脚本

创建测试脚本 `test.yaml`:

```yaml
web:
  url: https://example.com
  headed: true

tasks:
  - name: 登录测试
    flow:
      - aiTap: 登录按钮
      - aiInput:
          locate: 用户名输入框
          value: test@example.com
      - aiInput:
          locate: 密码输入框
          value: password123
      - aiTap: 提交按钮
      - aiAssert: 页面显示欢迎信息
```

运行脚本：

```bash
mspy test.yaml
```

## 模块结构

```
mspy/
├── __init__.py          # 包入口
├── shared/              # 共享模块
│   ├── types.py         # 类型定义
│   ├── logger.py        # 日志工具
│   ├── utils.py         # 工具函数
│   └── env/             # 环境配置
├── core/                # 核心模块
│   ├── agent/           # Agent实现
│   ├── ai_model/        # AI模型调用
│   │   ├── prompt/      # 英文提示词模板
│   │   └── service_caller/ # AI服务调用
│   ├── service/         # 服务层
│   ├── device/          # 设备抽象
│   └── yaml/            # YAML解析
├── web/                 # Web集成
│   └── playwright/      # Playwright集成
└── cli/                 # 命令行工具
    ├── main.py          # CLI入口
    └── batch_runner.py  # 批量执行器
```

## 环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `MIDSCENE_MODEL_NAME` | AI模型名称 | 是 | - |
| `MIDSCENE_MODEL_API_KEY` | API密钥 | 是 | - |
| `MIDSCENE_MODEL_BASE_URL` | API基础URL | 否 | OpenAI默认 |
| `MIDSCENE_MODEL_FAMILY` | 模型家族 | 视觉模型需要 | - |
| `MIDSCENE_DEBUG_MODE` | 调试模式 | 否 | false |
| `MIDSCENE_CACHE` | 启用缓存 | 否 | false |

## API参考

### Agent方法

- `ai_tap(prompt)` - 点击元素
- `ai_input(prompt, value)` - 输入文本
- `ai_hover(prompt)` - 悬停在元素上
- `ai_scroll(direction)` - 滚动页面
- `ai_act(instruction)` - 执行自然语言指令
- `ai_query(demand)` - 提取数据
- `ai_assert(assertion)` - 断言验证
- `ai_wait_for(condition)` - 等待条件满足
- `ai_locate(prompt)` - 定位元素

## 更多信息

- 📚 [官方文档](https://midscenejs.com)
- 🐛 [问题反馈](https://github.com/web-infra-dev/midscene/issues)
- 💬 [讨论区](https://github.com/web-infra-dev/midscene/discussions)

## 许可证

MIT License
