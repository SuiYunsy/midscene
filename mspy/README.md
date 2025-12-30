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

```bash
pip install -e ./mspy
```

或者安装依赖后直接使用：

```bash
pip install -r mspy/requirements.txt
```

安装Playwright浏览器：

```bash
playwright install
```

## 快速开始

### 使用Python代码

```python
import asyncio
from playwright.async_api import async_playwright
from mspy.web import PlaywrightAgent

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

配置AI模型：

```bash
# 模型名称
export MIDSCENE_MODEL_NAME=gpt-4o

# API密钥
export MIDSCENE_MODEL_API_KEY=your-api-key

# API基础URL（可选）
export MIDSCENE_MODEL_BASE_URL=https://api.openai.com/v1

# 模型家族（VL模型必须设置）
export MIDSCENE_MODEL_FAMILY=qwen2.5-vl
```

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
