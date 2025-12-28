# 核心功能
- 启动基于 WebDriverAgent 的 iOS Playground：交互式配置 WDA 地址、建立设备连接，并启动 Playground HTTP 服务。
- 提供端口可用性检测、WDA 连接循环、用户引导与自动打开浏览器。

# 逻辑流程
```mermaid
flowchart TD
  A[main] --> B[configureWebDriverAgent 默认 localhost:8100 或用户输入]
  B --> C[循环尝试连接 WDA -> new IOSDevice(wdaConfig) -> connect]
  C -->|成功| D[显示设备信息]
  C -->|失败| E[提示用户 选择重配/查看说明/退出]
  D --> F[创建 agentFactory -> 新建 IOSDevice+IOSAgent]
  F --> G[创建 PlaygroundServer(agentFactory, staticDir)]
  G --> H[findAvailablePort 从 PLAYGROUND_SERVER_PORT 开始寻找]
  H --> I[launch server -> 输出地址/ID]
  I --> J[open 浏览器访问 Playground]
```

# 关键细节
- 核心变量：`wdaConfig` 记录用户选择的 WDA 主机/端口；`staticDir` 指向静态资源；使用 `PLAYGROUND_SERVER_PORT` 默认端口，必要时递增寻找可用端口。
- 条件逻辑：连接失败时通过 Inquirer 提供三种选择；端口检测超过最大尝试次数直接退出；输入主机时去除 http 前缀。
- 异常处理：连接/启动失败打印错误并退出；WDA 配置与服务器启动过程中捕获错误并提示。
- 数据流：用户输入或默认配置 -> 创建设备/代理 -> 启动 Playground 服务 -> 打开浏览器访问。

# 跨文件调用关系
- 本文件调用：`IOSDevice` 与 `IOSAgent` 提供实际自动化能力；`PlaygroundServer` 创建可视化操控；常量来自 `@midscene/shared/constants`；使用 `@inquirer/prompts` 获取用户输入。
- 被调用场景：由 `bin/ios-playground` 可执行脚本加载此入口，供本地调试/演示使用。
