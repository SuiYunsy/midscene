# Midscene Python SDK (mspy)

AI驱动的UI自动化测试框架的Python实现。

## 安装

```bash
pip install mspy
```

如需使用Playwright集成：

```bash
pip install mspy[web]
```

## 快速开始

```python
from mspy.core.agent import Agent
from mspy.shared.env import set_model_config

# 配置模型
set_model_config({
    "MIDSCENE_MODEL_NAME": "gpt-4o",
    "MIDSCENE_MODEL_API_KEY": "your-api-key",
})

# 创建Agent并执行操作
async def main():
    agent = Agent(interface)
    await agent.ai_act("点击登录按钮")
    result = await agent.ai_query("获取用户名")
    print(result)
```

## 项目结构

```
mspy/
├── shared/           # 基础共享模块
│   ├── constants.py  # 常量定义
│   ├── types.py      # 类型定义
│   ├── utils.py      # 工具函数
│   ├── logger.py     # 日志系统
│   ├── env/          # 环境配置管理
│   └── img/          # 图像处理
├── core/             # 核心业务模块
│   ├── agent/        # Agent实现
│   ├── ai_model/     # AI模型调用
│   ├── device/       # 设备动作定义
│   ├── service/      # 服务层
│   └── yaml/         # YAML脚本系统
└── web/              # Web集成 (Playwright)
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black .
ruff check .
```

## 许可证

MIT License
