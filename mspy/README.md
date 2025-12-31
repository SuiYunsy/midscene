# mspy - Midscene Python SDK

AI驱动的UI自动化测试框架的Python实现。

## 安装

```bash
# 使用uv
uv pip install -e .

# 或使用pip
pip install -e .
```

## 快速开始

```python
import asyncio
from mspy.web.playwright import PlaywrightAgent

async def main():
    agent = await PlaywrightAgent.create("https://example.com")
    
    # AI驱动的操作
    await agent.ai_act("点击登录按钮")
    await agent.ai_input("用户名输入框", value="admin")
    await agent.ai_assert("登录成功")
    
    await agent.destroy()

asyncio.run(main())
```

## 环境变量

```bash
# 模型配置
MIDSCENE_MODEL_NAME=gpt-4o
MIDSCENE_MODEL_API_KEY=your-api-key
MIDSCENE_MODEL_BASE_URL=https://api.openai.com/v1

# 可选：模型族配置
MIDSCENE_MODEL_FAMILY=qwen2.5-vl
```

## 功能特性

- 🤖 AI驱动的元素定位和操作
- 📝 YAML脚本支持
- 🎭 Playwright集成
- 📊 JSON报告输出
- 🔧 异步API支持

## 许可证

MIT License
