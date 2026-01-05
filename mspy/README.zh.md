# mspy - Midscene Python 实现

基于纯视觉的Web自动化测试框架，Python 3.11+ 实现。

## 特性

- 仅支持 **qwen3-vl** 模型
- 仅保留 **aiAct** 自动规划功能
- 支持 **Playwright** Web端
- 支持 HTTP/SOCKS 代理
- 支持跳过 SSL 证书验证
- 对话历史默认最多保留 2 张截图
- 简化的截图报告

## 快速开始

### 1. 创建虚拟环境

```bash
cd mspy
uv venv --python 3.11
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
uv pip install -r requirements.txt
playwright install chromium
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写您的 API 配置
```

### 4. 运行快速体验

```bash
# Python 脚本方式
uv run python quick.py

# YAML 脚本方式
uv run python -m mspy.cli.runner quick.yaml --headed
```

## 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| MIDSCENE_MODEL_NAME | 模型名称 | 是 |
| MIDSCENE_MODEL_BASE_URL | API 地址 | 是 |
| MIDSCENE_MODEL_API_KEY | API 密钥 | 是 |
| MIDSCENE_MODEL_FAMILY | 模型家族（固定为 qwen3-vl） | 是 |
| MIDSCENE_MODEL_HTTP_PROXY | HTTP 代理 | 否 |
| MIDSCENE_MODEL_SOCKS_PROXY | SOCKS 代理 | 否 |
| MIDSCENE_MODEL_SKIP_CERT_VERIFICATION | 跳过 SSL 验证 | 否 |
| MIDSCENE_MAX_IMAGES_IN_HISTORY | 历史最大图片数 | 否 |
| MIDSCENE_REPLANNING_CYCLE_LIMIT | 重规划次数限制 | 否 |

## 支持的动作

- **Tap** - 点击
- **RightClick** - 右键点击
- **DoubleClick** - 双击
- **Hover** - 悬停
- **Input** - 输入文本
- **KeyboardPress** - 按键
- **Scroll** - 滚动
- **DragAndDrop** - 拖放
- **Navigate** - 导航
- **Reload** - 刷新
- **GoBack** - 后退
- **Print_Assert_Result** - 断言结果
- **sleep** - 等待

## YAML 脚本格式

```yaml
web:
  url: https://example.com
  headless: false
  viewWidth: 1280
  viewHeight: 720

tasks:
  - name: 任务名称
    flow:
      - aiAct: "执行某个操作"
      - sleep: 1000
```

## 目录结构

```
mspy/
├── shared/          # 共享模块：配置、日志、工具
├── core/            # 核心模块：Agent、规划、任务执行
├── web/             # Web模块：Playwright集成
├── cli/             # CLI模块：YAML脚本执行器
├── requirements.txt # 依赖
├── .env.example     # 环境变量示例
├── quick.py         # 快速体验脚本
└── quick.yaml       # 快速体验YAML
```

## 与 TypeScript 版本的差异

- 仅支持 qwen3-vl 模型，移除了其他模型支持
- 移除了 DOM 树提取、markup、drawbox 等功能
- 移除了即时操作 API（aiTap、aiAsk 等）
- 移除了缓存机制
- 移除了 MCP 功能
- 简化了报告生成（仅截图）
