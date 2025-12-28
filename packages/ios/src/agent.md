# 核心功能
- 基于核心 Agent 封装 iOS 设备代理，提供启动 App/URL、执行 WDA 请求、Home 与 App Switcher 操作的类型安全包装方法。
- `agentFromWebDriverAgent` 自动检查本地 iOS 环境、连接 WDA 并返回已连接的 `IOSAgent`。

# 逻辑流程
```mermaid
flowchart TD
  A[构造 IOSAgent(device, opts)] --> B[wrapActionInActionSpace 创建 launch/runWdaRequest/home/appSwitcher 包装方法]
  C[agentFromWebDriverAgent(opts?)] --> D[checkIOSEnvironment]
  D -->|不可用| E[抛出环境错误]
  D -->|可用| F[new IOSDevice(opts)]
  F --> G[device.connect()]
  G --> H[返回 new IOSAgent(device, opts)]
```

# 关键细节
- 核心变量：`IOSAgent` 继承 `PageAgent<IOSDevice>`；`IOSAgentOpt` 为通用 `AgentOpt`。
- 条件判断：环境检测失败时直接抛错，避免后续连接；动作包装根据是否有参数决定调用签名。
- 异常处理：`agentFromWebDriverAgent` 对环境不可用抛出友好错误；动作本身依赖设备实现的错误处理。
- 数据流：输入可选设备/代理配置 -> 环境检测 -> 构建设备并连接 -> 返回封装好 ActionSpace 的代理实例。

# 跨文件调用关系
- 本文件调用：`IOSDevice`、`checkIOSEnvironment`、核心 Agent 基类；调试日志来自 `@midscene/shared/logger`。
- 被调用场景：`src/index.ts` 导出 `IOSAgent` 与工厂；CLI/Playground 通过 `agentFromWebDriverAgent` 快速获取可用代理。 
