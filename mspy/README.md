# Midscene Python SDK (mspy)

AI驱动的UI自动化测试框架的Python实现。

从TypeScript版本迁移，支持通过AI执行浏览器操作自动化、断言和数据提取。

## 安装

```bash
pip install -r requirements.txt
```

如需使用Playwright集成：

```bash
pip install playwright
playwright install
```

## 快速开始

### 使用Playwright Agent

```python
import asyncio
from playwright.async_api import async_playwright
from mspy.web import PlaywrightAgent

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com")
        
        # 创建AI Agent
        agent = PlaywrightAgent(page)
        
        # 执行AI驱动的操作
        await agent.ai_act("点击登录按钮")
        
        # 查询页面信息
        result = await agent.ai_query("获取页面标题")
        print(result)
        
        await browser.close()

asyncio.run(main())
```

### 使用CLI运行YAML脚本

```bash
# 运行单个脚本
python -m mspy.cli.main script.yaml

# 运行目录下的所有脚本
python -m mspy.cli.main ./scripts/

# 带参数运行
python -m mspy.cli.main script.yaml --headed --keep-window
```

### YAML脚本示例

```yaml
# example.yaml
web:
  url: https://example.com

tasks:
  - name: Login Test
    flow:
      - aiAct: 点击登录按钮
      - aiInput:
          locate: 用户名输入框
          value: testuser
      - aiAssert: 登录成功
```

## 项目结构

```
mspy/
├── shared/           # 基础共享模块
│   ├── constants.py  # 常量定义
│   ├── types.py      # 类型定义
│   ├── utils.py      # 工具函数
│   ├── logger.py     # 日志系统
│   ├── keyboard.py   # 键盘布局
│   ├── env/          # 环境配置管理
│   └── img/          # 图像处理
├── core/             # 核心业务模块
│   ├── agent/        # Agent实现
│   ├── ai_model/     # AI模型调用
│   ├── device/       # 设备动作定义
│   ├── service/      # 服务层
│   ├── yaml/         # YAML脚本系统
│   └── report.py     # HTML报告生成
├── web/              # Web集成
│   ├── web_page.py   # 抽象Web页面
│   ├── actions.py    # Web动作定义
│   └── playwright/   # Playwright集成
│       ├── page.py   # 页面封装
│       └── agent.py  # Agent封装
└── cli/              # 命令行工具
    ├── main.py       # CLI入口
    ├── config.py     # 配置工厂
    └── batch_runner.py # 批量执行器
```

## 环境变量

| 变量 | 描述 |
|------|------|
| `MIDSCENE_MODEL_NAME` | AI模型名称 (如 gpt-4o) |
| `MIDSCENE_MODEL_API_KEY` | AI模型API密钥 |
| `MIDSCENE_MODEL_BASE_URL` | AI模型API基础URL |
| `MIDSCENE_DEBUG` | 启用调试日志 (true/false) |

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
