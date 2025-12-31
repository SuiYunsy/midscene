# Midscene Python 3.11 迁移计划

## 概述

本文档详细描述了将 Midscene.js 项目中的 `packages/shared`、`packages/core`、`packages/web-integration` 和 `packages/cli` 迁移到 Python 3.11 实现的计划。迁移后的 Python 项目将作为独立项目运行。

## 目录

1. [项目分析](#项目分析)
2. [Python 项目结构](#python-项目结构)
3. [依赖映射](#依赖映射)
4. [各包迁移策略](#各包迁移策略)
5. [实施步骤](#实施步骤)
6. [测试策略](#测试策略)
7. [时间估算](#时间估算)

---

## 项目分析

### 原始 TypeScript 包概览

| 包名 | 功能描述 | 主要依赖 |
|------|----------|----------|
| `@midscene/shared` | 共享工具函数、类型定义、图像处理、日志记录 | jimp, sharp, uuid, debug, express |
| `@midscene/core` | AI 模型集成、Agent 实现、任务执行器、YAML 脚本解析 | openai, zod, js-yaml, dayjs |
| `@midscene/web` | Web 集成（Playwright、Puppeteer）、页面上下文解析 | playwright, puppeteer, socket.io |
| `@midscene/cli` | 命令行工具、批量运行器、配置管理 | yargs, chalk, glob, puppeteer |

### 包依赖关系

```
@midscene/cli
    ├── @midscene/web
    │   ├── @midscene/core
    │   │   └── @midscene/shared
    │   └── @midscene/shared
    └── @midscene/core
        └── @midscene/shared
```

---

## Python 项目结构

### 推荐的目录结构

```
midscene-python/
├── pyproject.toml           # 项目配置 (PEP 517/518)
├── setup.py                 # 向后兼容
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt         # 依赖列表
├── requirements-dev.txt     # 开发依赖
│
├── src/
│   └── midscene/
│       ├── __init__.py
│       │
│       ├── shared/          # @midscene/shared
│       │   ├── __init__.py
│       │   ├── common.py
│       │   ├── logger.py
│       │   ├── utils.py
│       │   ├── constants/
│       │   │   ├── __init__.py
│       │   │   └── node_type.py
│       │   ├── env/
│       │   │   ├── __init__.py
│       │   │   ├── basic.py
│       │   │   └── model_config.py
│       │   ├── extractor/
│       │   │   ├── __init__.py
│       │   │   ├── web_extractor.py
│       │   │   ├── dom_util.py
│       │   │   └── locator.py
│       │   ├── img/
│       │   │   ├── __init__.py
│       │   │   ├── image_utils.py
│       │   │   └── transform.py
│       │   └── types/
│       │       ├── __init__.py
│       │       └── base.py
│       │
│       ├── core/            # @midscene/core
│       │   ├── __init__.py
│       │   ├── service.py
│       │   ├── task_runner.py
│       │   ├── utils.py
│       │   ├── types.py
│       │   ├── agent/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   ├── task_cache.py
│       │   │   ├── task_executor.py
│       │   │   └── execution_session.py
│       │   ├── ai_model/
│       │   │   ├── __init__.py
│       │   │   ├── llm_planning.py
│       │   │   ├── inspect.py
│       │   │   ├── ui_tars_planning.py
│       │   │   ├── conversation_history.py
│       │   │   ├── prompt/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── llm_locator.py
│       │   │   │   └── util.py
│       │   │   └── service_caller/
│       │   │       ├── __init__.py
│       │   │       └── caller.py
│       │   ├── device/
│       │   │   ├── __init__.py
│       │   │   └── abstract_interface.py
│       │   └── yaml/
│       │       ├── __init__.py
│       │       ├── parser.py
│       │       └── player.py
│       │
│       ├── web/             # @midscene/web
│       │   ├── __init__.py
│       │   ├── web_element.py
│       │   ├── web_page.py
│       │   ├── utils.py
│       │   ├── playwright/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   ├── page.py
│       │   │   └── fixture.py
│       │   ├── puppeteer/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   └── page.py
│       │   └── static/
│       │       ├── __init__.py
│       │       └── page.py
│       │
│       └── cli/             # @midscene/cli
│           ├── __init__.py
│           ├── __main__.py
│           ├── args.py
│           ├── batch_runner.py
│           ├── config_factory.py
│           ├── printer.py
│           └── yaml_player.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── shared/
│   ├── core/
│   ├── web/
│   └── cli/
│
└── scripts/
    └── run_tests.py
```

---

## 依赖映射

### 核心依赖对照表

| TypeScript 依赖 | Python 替代方案 | 用途 |
|-----------------|-----------------|------|
| `openai` | `openai` | OpenAI API 客户端 |
| `zod` | `pydantic` | 数据验证和模式定义 |
| `jimp` / `sharp` | `Pillow` | 图像处理 |
| `@silvia-odwyer/photon-node` | `Pillow` + `scikit-image` | 高级图像处理 (注: photon 是轻量级库，Pillow 可满足大部分需求，scikit-image 用于高级滤镜) |
| `uuid` | `uuid` (stdlib) | UUID 生成 |
| `debug` | `logging` (stdlib) | 日志记录 |
| `dayjs` | `datetime` (stdlib) / `pendulum` | 日期时间处理 |
| `js-yaml` | `pyyaml` | YAML 解析 |
| `dotenv` | `python-dotenv` | 环境变量管理 |
| `playwright` | `playwright` (Python版) | 浏览器自动化 |
| `puppeteer` | `playwright` (推荐使用 Playwright 替代，pyppeteer 已停止维护) | 浏览器自动化 |
| `yargs` | `argparse` (stdlib) / `click` | 命令行参数解析 |
| `chalk` | `rich` / `colorama` | 终端彩色输出 |
| `glob` | `glob` (stdlib) / `pathlib` | 文件模式匹配 |
| `express` | `fastapi` / `flask` | HTTP 服务器 |
| `socket.io` | `python-socketio` | WebSocket 通信 |
| `semver` | `packaging` / `semver` | 版本号处理 |
| `lodash.merge` | `deepmerge` | 深度对象合并 |
| `p-limit` | `asyncio.Semaphore` | 并发限制 |
| `jsonrepair` | `json-repair` | JSON 修复 |
| `fetch-socks` / `undici` | `httpx` / `aiohttp` | HTTP 客户端 |

### requirements.txt

```
# 核心依赖
openai>=1.0.0,<2.0.0
pydantic>=2.0.0,<3.0.0
pyyaml>=6.0,<7.0
python-dotenv>=1.0.0,<2.0.0
httpx>=0.24.0,<1.0.0

# 图像处理
Pillow>=10.0.0,<11.0.0

# 浏览器自动化
playwright>=1.40.0,<2.0.0

# CLI
click>=8.0.0,<9.0.0
rich>=13.0.0,<14.0.0

# 工具
deepmerge>=1.1.0,<2.0.0
packaging>=23.0,<24.0

# 异步
aiohttp>=3.9.0,<4.0.0
python-socketio>=5.10.0,<6.0.0

# 类型检查
typing-extensions>=4.8.0,<5.0.0
```

### requirements-dev.txt

```
# 测试
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# 类型检查
mypy>=1.7.0

# 代码格式化
black>=23.0.0
isort>=5.12.0
ruff>=0.1.0

# 文档
mkdocs>=1.5.0
mkdocs-material>=9.0.0
```

---

## 各包迁移策略

### 1. @midscene/shared → midscene.shared

#### 核心模块迁移

| TypeScript 文件 | Python 文件 | 说明 |
|-----------------|-------------|------|
| `common.ts` | `common.py` | 路径处理，运行目录管理 |
| `logger.ts` | `logger.py` | 使用 Python logging 模块 |
| `utils.ts` | `utils.py` | 工具函数 |
| `constants/index.ts` | `constants/node_type.py` | 节点类型常量 |
| `env/index.ts` | `env/model_config.py` | 模型配置管理 |
| `extractor/web-extractor.ts` | `extractor/web_extractor.py` | Web 元素提取 |
| `img/index.ts` | `img/image_utils.py` | 图像处理工具 |
| `types/index.ts` | `types/base.py` | 基础类型定义 |

#### 关键代码转换示例

**TypeScript (logger.ts)**
```typescript
import { getDebug } from '@midscene/shared/logger';
const debug = getDebug('agent');
debug('message', data);
```

**Python (logger.py)**
```python
import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"midscene.{name}")
    logger.setLevel(logging.DEBUG)
    return logger

# 使用
logger = get_logger('agent')
logger.debug('message %s', data)
```

**TypeScript (types/index.ts)**
```typescript
export interface Point {
  left: number;
  top: number;
}

export interface Size {
  width: number;
  height: number;
  dpr?: number;
}

export type Rect = Point & Size & { zoom?: number };
```

**Python (types/base.py)**
```python
from pydantic import BaseModel
from typing import Optional

class Point(BaseModel):
    left: float
    top: float

class Size(BaseModel):
    width: float
    height: float
    dpr: Optional[float] = None

class Rect(Point, Size):
    zoom: Optional[float] = None
```

### 2. @midscene/core → midscene.core

#### 核心模块迁移

| TypeScript 文件 | Python 文件 | 说明 |
|-----------------|-------------|------|
| `agent/agent.ts` | `agent/agent.py` | 主 Agent 类 |
| `agent/task-cache.ts` | `agent/task_cache.py` | 任务缓存 |
| `agent/tasks.ts` | `agent/task_executor.py` | 任务执行器 |
| `ai-model/index.ts` | `ai_model/__init__.py` | AI 模型调用 |
| `ai-model/llm-planning.ts` | `ai_model/llm_planning.py` | LLM 规划 |
| `ai-model/inspect.ts` | `ai_model/inspect.py` | 元素检测 |
| `service/index.ts` | `service.py` | 服务层 |
| `yaml/index.ts` | `yaml/parser.py` | YAML 脚本解析 |

#### 关键代码转换示例

**TypeScript (agent/agent.ts - 部分)**
```typescript
export class Agent<InterfaceType extends AbstractInterface = AbstractInterface> {
  interface: InterfaceType;
  service: Service;
  
  async aiTap(locatePrompt: TUserPrompt, opt?: LocateOption) {
    assert(locatePrompt, 'missing locate prompt for tap');
    const detailedLocateParam = buildDetailedLocateParam(locatePrompt, opt);
    return this.callActionInActionSpace('Tap', {
      locate: detailedLocateParam,
    });
  }
}
```

**Python (agent/agent.py)**
```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from midscene.core.device import AbstractInterface
from midscene.core.service import Service

T = TypeVar('T', bound=AbstractInterface)

class Agent(Generic[T]):
    def __init__(self, interface: T, opts: Optional[AgentOpt] = None):
        self.interface = interface
        self.service = Service(self.get_ui_context)
        self._opts = opts or AgentOpt()
    
    async def ai_tap(
        self, 
        locate_prompt: str, 
        opt: Optional[LocateOption] = None
    ) -> Any:
        if not locate_prompt:
            raise ValueError('missing locate prompt for tap')
        
        detailed_locate_param = build_detailed_locate_param(locate_prompt, opt)
        return await self.call_action_in_action_space('Tap', {
            'locate': detailed_locate_param,
        })
```

**TypeScript (使用 OpenAI)**
```typescript
import OpenAI from 'openai';

const client = new OpenAI();
const response = await client.chat.completions.create({
  model: 'gpt-4-vision-preview',
  messages: [{ role: 'user', content: prompt }],
});
```

**Python (使用 OpenAI)**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def call_ai(prompt: str) -> str:
    response = await client.chat.completions.create(
        model='gpt-4-vision-preview',
        messages=[{'role': 'user', 'content': prompt}],
    )
    return response.choices[0].message.content
```

### 3. @midscene/web → midscene.web

#### 核心模块迁移

| TypeScript 文件 | Python 文件 | 说明 |
|-----------------|-------------|------|
| `playwright/index.ts` | `playwright/agent.py` | Playwright Agent |
| `playwright/page.ts` | `playwright/page.py` | Playwright 页面封装 |
| `puppeteer/index.ts` | `puppeteer/agent.py` | 使用 playwright 替代 |
| `web-element.ts` | `web_element.py` | Web 元素定义 |
| `web-page.ts` | `web_page.py` | Web 页面抽象 |
| `static/index.ts` | `static/page.py` | 静态页面处理 |

#### 关键代码转换示例

**TypeScript (playwright/page.ts)**
```typescript
import type { Page } from '@playwright/test';

export class PlaywrightPage implements AbstractInterface {
  private page: Page;
  
  async screenshotBase64(): Promise<string> {
    const buffer = await this.page.screenshot();
    return buffer.toString('base64');
  }
}
```

**Python (playwright/page.py)**
```python
from playwright.async_api import Page
from midscene.core.device import AbstractInterface
import base64

class PlaywrightPage(AbstractInterface):
    def __init__(self, page: Page):
        self._page = page
    
    async def screenshot_base64(self) -> str:
        buffer = await self._page.screenshot()
        return base64.b64encode(buffer).decode('utf-8')
```

### 4. @midscene/cli → midscene.cli

#### 核心模块迁移

| TypeScript 文件 | Python 文件 | 说明 |
|-----------------|-------------|------|
| `index.ts` | `__main__.py` | CLI 入口点 |
| `args.ts` | `args.py` | 参数解析 |
| `batch-runner.ts` | `batch_runner.py` | 批量运行器 |
| `config-factory.ts` | `config_factory.py` | 配置工厂 |
| `printer.ts` | `printer.py` | 输出格式化 |

#### 关键代码转换示例

**TypeScript (index.ts - CLI 入口)**
```typescript
import yargs from 'yargs';

const { options, path } = await parseProcessArgs();
const executor = new BatchRunner(config);
await executor.run();
```

**Python (__main__.py)**
```python
import click
import asyncio
from midscene.cli.batch_runner import BatchRunner
from midscene.cli.config_factory import create_config

@click.command()
@click.option('--config', '-c', help='Config file path')
@click.option('--headed', is_flag=True, help='Run in headed mode')
@click.option('--keep-window', is_flag=True, help='Keep browser window open')
@click.argument('path', required=False)
def main(config: str, headed: bool, keep_window: bool, path: str):
    """Midscene CLI - AI-powered UI automation"""
    
    async def run():
        cfg = await create_config(config, {
            'headed': headed,
            'keep_window': keep_window,
        })
        runner = BatchRunner(cfg)
        await runner.run()
        runner.print_execution_summary()
    
    asyncio.run(run())

if __name__ == '__main__':
    main()
```

---

## 实施步骤

### 阶段 1: 项目初始化 (1 周)

1. **创建项目骨架**
   - 初始化 Python 项目结构
   - 配置 `pyproject.toml`
   - 设置开发环境 (virtualenv, pre-commit hooks)

2. **配置工具链**
   - 设置 pytest 测试框架
   - 配置 mypy 类型检查
   - 设置 black/ruff 代码格式化

### 阶段 2: 迁移 shared 包 (1-2 周)

1. **基础模块**
   - 迁移类型定义 (`types/`)
   - 迁移常量 (`constants/`)
   - 迁移工具函数 (`utils.py`, `common.py`)

2. **核心功能**
   - 迁移日志模块 (`logger.py`)
   - 迁移环境配置 (`env/`)
   - 迁移图像处理 (`img/`)
   - 迁移 DOM 提取器 (`extractor/`)

3. **测试**
   - 为每个模块编写单元测试

### 阶段 3: 迁移 core 包 (2-3 周)

1. **设备抽象层**
   - 迁移 `AbstractInterface`
   - 定义设备操作接口

2. **AI 模型集成**
   - 迁移 OpenAI 调用封装
   - 迁移 LLM 规划逻辑
   - 迁移 UI-TARS 集成
   - 迁移 Prompt 模板

3. **Agent 核心**
   - 迁移 `Agent` 类
   - 迁移任务执行器
   - 迁移缓存机制

4. **YAML 脚本**
   - 迁移 YAML 解析器
   - 迁移脚本播放器

5. **测试**
   - 单元测试
   - 集成测试（使用 mock AI 响应）

### 阶段 4: 迁移 web-integration 包 (2-3 周)

1. **Web 抽象层**
   - 迁移 `WebElement` 类
   - 迁移 `WebPage` 抽象

2. **Playwright 集成**
   - 迁移 `PlaywrightPage`
   - 迁移 `PlaywrightAgent`
   - 迁移测试 fixture

3. **Puppeteer 替代**
   - 使用 Playwright 完全替代 Puppeteer（pyppeteer 已停止维护）
   - 确保 API 兼容性

4. **静态页面**
   - 迁移静态页面处理器

5. **测试**
   - 浏览器自动化测试
   - E2E 测试

### 阶段 5: 迁移 CLI 包 (1-2 周)

1. **命令行接口**
   - 使用 Click 实现 CLI
   - 迁移参数解析逻辑

2. **批量运行器**
   - 迁移 `BatchRunner`
   - 实现并发控制

3. **配置管理**
   - 迁移配置工厂
   - 迁移 dotenv 集成

4. **输出格式化**
   - 使用 Rich 实现终端输出
   - 迁移进度显示

5. **测试**
   - CLI 集成测试

### 阶段 6: 集成和优化 (1-2 周)

1. **端到端测试**
   - 完整工作流测试
   - 性能基准测试

2. **文档**
   - API 文档
   - 使用指南
   - 迁移指南

3. **打包发布**
   - 配置 PyPI 发布
   - 创建安装脚本

---

## 测试策略

### 单元测试

```python
# tests/shared/test_utils.py
import pytest
from midscene.shared.utils import if_in_node

def test_if_in_node():
    # Python 版本应该总是返回 False（不在 Node 环境）
    assert if_in_node() == False
```

### 集成测试

```python
# tests/core/test_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from midscene.core.agent import Agent
from midscene.web.playwright import PlaywrightPage

@pytest.mark.asyncio
async def test_agent_ai_tap():
    mock_page = AsyncMock(spec=PlaywrightPage)
    agent = Agent(mock_page)
    
    with patch.object(agent, 'call_action_in_action_space') as mock_call:
        mock_call.return_value = {'success': True}
        result = await agent.ai_tap('click the submit button')
        
        mock_call.assert_called_once()
        assert result['success'] == True
```

### E2E 测试

```python
# tests/e2e/test_full_workflow.py
import pytest
from playwright.async_api import async_playwright
from midscene.web.playwright import PlaywrightAgent

@pytest.mark.asyncio
async def test_full_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        agent = PlaywrightAgent(page)
        await page.goto('https://example.com')
        
        # 使用 AI 进行操作
        result = await agent.ai_query('What is the page title?')
        assert 'Example' in result
        
        await browser.close()
```

---

## 时间估算

| 阶段 | 预计时间 | 里程碑 |
|------|----------|--------|
| 阶段 1: 项目初始化 | 1 周 | 项目骨架完成 |
| 阶段 2: shared 包迁移 | 1-2 周 | shared 包可用 |
| 阶段 3: core 包迁移 | 2-3 周 | core 包可用 |
| 阶段 4: web 包迁移 | 2-3 周 | web 包可用 |
| 阶段 5: CLI 包迁移 | 1-2 周 | CLI 可用 |
| 阶段 6: 集成优化 | 1-2 周 | 生产就绪 |

**总计: 8-13 周**

---

## 风险和挑战

### 技术风险

1. **AI 模型响应格式差异**
   - OpenAI Python SDK 和 TypeScript SDK 可能有细微差异
   - 需要仔细测试响应解析

2. **异步模型差异**
   - TypeScript 使用 Promise
   - Python 使用 asyncio
   - 需要注意事件循环管理

3. **类型系统差异**
   - TypeScript 有更严格的类型系统
   - 使用 Pydantic 和 mypy 来保持类型安全

### 功能缺失风险

1. **UI-TARS 模型集成**
   - 需要验证 Python 版本的模型调用兼容性

2. **浏览器自动化性能**
   - Python Playwright 和 Node.js Playwright 性能可能略有差异

### 缓解措施

1. 建立全面的测试套件
2. 使用 mock 进行 AI 响应测试
3. 进行性能基准比较
4. 保持与原始 TypeScript 版本的 API 兼容性

---

## 下一步行动

1. [ ] 创建 Python 项目仓库
2. [ ] 设置开发环境和 CI/CD
3. [ ] 开始 shared 包的迁移
4. [ ] 建立测试基础设施
5. [ ] 迭代迁移其他包

---

## 附录

### A. 命名约定对照

| TypeScript 约定 | Python 约定 |
|-----------------|-------------|
| `camelCase` 变量名 | `snake_case` 变量名 |
| `PascalCase` 类名 | `PascalCase` 类名 |
| `UPPER_CASE` 常量 | `UPPER_CASE` 常量 |
| `.ts` 文件扩展名 | `.py` 文件扩展名 |
| `interface` | `Protocol` 或 `BaseModel` |
| `type` 别名 | `TypeAlias` 或 `type` (3.12+) |

### B. 异步模式转换

```typescript
// TypeScript
async function fetchData(): Promise<Data> {
  const response = await fetch(url);
  return await response.json();
}
```

```python
# Python
async def fetch_data() -> Data:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### C. 错误处理模式

```typescript
// TypeScript
class ServiceError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'ServiceError';
  }
}
```

```python
# Python
class ServiceError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
        self.name = 'ServiceError'
```

---

## 详细模块映射表

### @midscene/shared 完整文件映射

| 原始路径 | Python 路径 | 优先级 |
|----------|-------------|--------|
| `src/index.ts` | `shared/__init__.py` | P0 |
| `src/common.ts` | `shared/common.py` | P0 |
| `src/logger.ts` | `shared/logger.py` | P0 |
| `src/utils.ts` | `shared/utils.py` | P0 |
| `src/constants/index.ts` | `shared/constants/__init__.py` | P0 |
| `src/env/index.ts` | `shared/env/__init__.py` | P0 |
| `src/env/basic.ts` | `shared/env/basic.py` | P0 |
| `src/extractor/index.ts` | `shared/extractor/__init__.py` | P1 |
| `src/extractor/web-extractor.ts` | `shared/extractor/web_extractor.py` | P1 |
| `src/extractor/dom-util.ts` | `shared/extractor/dom_util.py` | P1 |
| `src/extractor/locator.ts` | `shared/extractor/locator.py` | P1 |
| `src/img/index.ts` | `shared/img/__init__.py` | P1 |
| `src/types/index.ts` | `shared/types/__init__.py` | P0 |
| `src/mcp/index.ts` | `shared/mcp/__init__.py` | P2 |
| `src/polyfills/index.ts` | - (不需要) | - |

### @midscene/core 完整文件映射

| 原始路径 | Python 路径 | 优先级 |
|----------|-------------|--------|
| `src/index.ts` | `core/__init__.py` | P0 |
| `src/service/index.ts` | `core/service.py` | P0 |
| `src/task-runner.ts` | `core/task_runner.py` | P0 |
| `src/types.ts` | `core/types.py` | P0 |
| `src/utils.ts` | `core/utils.py` | P0 |
| `src/agent/agent.ts` | `core/agent/agent.py` | P0 |
| `src/agent/task-cache.ts` | `core/agent/task_cache.py` | P1 |
| `src/agent/tasks.ts` | `core/agent/task_executor.py` | P0 |
| `src/agent/execution-session.ts` | `core/agent/execution_session.py` | P1 |
| `src/ai-model/index.ts` | `core/ai_model/__init__.py` | P0 |
| `src/ai-model/llm-planning.ts` | `core/ai_model/llm_planning.py` | P0 |
| `src/ai-model/inspect.ts` | `core/ai_model/inspect.py` | P0 |
| `src/ai-model/ui-tars-planning.ts` | `core/ai_model/ui_tars_planning.py` | P1 |
| `src/ai-model/conversation-history.ts` | `core/ai_model/conversation_history.py` | P1 |
| `src/ai-model/prompt/*.ts` | `core/ai_model/prompt/*.py` | P0 |
| `src/ai-model/service-caller/*.ts` | `core/ai_model/service_caller/*.py` | P0 |
| `src/device/index.ts` | `core/device/__init__.py` | P0 |
| `src/yaml/index.ts` | `core/yaml/__init__.py` | P0 |
| `src/yaml.ts` | `core/yaml/parser.py` | P0 |

### @midscene/web 完整文件映射

| 原始路径 | Python 路径 | 优先级 |
|----------|-------------|--------|
| `src/index.ts` | `web/__init__.py` | P0 |
| `src/web-element.ts` | `web/web_element.py` | P0 |
| `src/web-page.ts` | `web/web_page.py` | P0 |
| `src/utils.ts` | `web/utils.py` | P0 |
| `src/playwright/index.ts` | `web/playwright/__init__.py` | P0 |
| `src/playwright/page.ts` | `web/playwright/page.py` | P0 |
| `src/playwright/ai-fixture.ts` | `web/playwright/fixture.py` | P1 |
| `src/puppeteer/index.ts` | `web/puppeteer/__init__.py` | P1 |
| `src/puppeteer/page.ts` | `web/puppeteer/page.py` | P1 |
| `src/static/index.ts` | `web/static/__init__.py` | P2 |
| `src/chrome-extension/*` | - (不迁移) | - |
| `src/bridge-mode/*` | - (不迁移) | - |
| `src/mcp-server.ts` | - (可选迁移) | P2 |

### @midscene/cli 完整文件映射

| 原始路径 | Python 路径 | 优先级 |
|----------|-------------|--------|
| `src/index.ts` | `cli/__main__.py` | P0 |
| `src/args.ts` | `cli/args.py` | P0 |
| `src/batch-runner.ts` | `cli/batch_runner.py` | P0 |
| `src/config-factory.ts` | `cli/config_factory.py` | P0 |
| `src/printer.ts` | `cli/printer.py` | P0 |
| `src/tty-renderer.ts` | `cli/tty_renderer.py` | P1 |
| `src/create-yaml-player.ts` | `cli/yaml_player.py` | P0 |
| `src/cli-utils.ts` | `cli/utils.py` | P0 |

---

## pyproject.toml 示例

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "midscene"
version = "1.0.0"
description = "AI-powered UI automation for Web, Android, and iOS"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11,<4.0"
authors = [
    {name = "Midscene Team", email = "midscene@example.com"},
]
keywords = [
    "AI",
    "automation",
    "testing",
    "playwright",
    "browser",
    "UI",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Testing",
    "Topic :: Software Development :: Quality Assurance",
]
dependencies = [
    "openai>=1.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.24.0",
    "Pillow>=10.0.0",
    "playwright>=1.40.0",
    "click>=8.0.0",
    "rich>=13.0.0",
    "deepmerge>=1.1.0",
    "packaging>=23.0",
    "aiohttp>=3.9.0",
    "typing-extensions>=4.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
]

[project.scripts]
midscene = "midscene.cli:main"

[project.urls]
Homepage = "https://midscenejs.com/"
Documentation = "https://midscenejs.com/"
Repository = "https://github.com/web-infra-dev/midscene"

[tool.hatch.build.targets.wheel]
packages = ["src/midscene"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

*文档版本: 1.0*  
*创建日期: 2024-12-31*  
*最后更新: 2024-12-31*
