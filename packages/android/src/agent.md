# 核心功能
- 基于 `@midscene/core/agent` 的通用 Agent 构建 Android 端代理，包装设备动作（启动 App、执行 ADB、返回/主页/多任务）。
- 提供 `agentFromAdbDevice` 便捷方法：自动选择已连接设备并创建 `AndroidDevice` 与 `AndroidAgent`。
- 通过动作包装器与 ActionSpace 机制，将设备能力暴露为统一的可调用异步方法。

# 逻辑流程
```mermaid
flowchart TD
  A[构造 AndroidAgent(device, opts)] --> B[创建 launch/runAdbShell/back/home/recentApps 包装]
  B --> C[wrapActionInActionSpace 生成可调用动作]
  D[agentFromAdbDevice(deviceId?, opts?)] --> E[缺少 deviceId? -> getConnectedDevices]
  E --> F{是否有设备?}
  F -->|否| G[抛出无设备错误]
  F -->|是| H[选择首个设备ID]
  H --> I[new AndroidDevice(deviceId, opts)]
  I --> J[device.connect()]
  J --> K[返回 new AndroidAgent(device, opts)]
```

# 关键细节
- 核心变量：`AndroidAgent` 继承 `PageAgent<AndroidDevice>`，利用父类的 ActionSpace 包装器；`AndroidAgentOpt` 直接复用通用 `AgentOpt`。
- 条件判断：`agentFromAdbDevice` 若无 deviceId 则查询已连接设备并默认取第一个；未找到设备时抛出明确提示。
- 异常处理：设备列表为空时抛出带指导信息的错误；构造过程中依赖 `AndroidDevice.connect` 内部可能抛出连接异常。
- 数据流：输入设备 ID/可选配置 -> 获取/连接设备 -> 返回绑定了动作包装的 Agent 实例，供上层执行动作。

# 跨文件调用关系
- 本文件调用：依赖 `AndroidDevice`（device.ts）提供设备操作；`getConnectedDevices`（utils.ts）列出设备；`PageAgent.wrapActionInActionSpace` 生成动作；`@midscene/shared/logger` 输出调试。
- 被调用场景：`src/index.ts` 导出 `AndroidAgent` 与 `agentFromAdbDevice`；CLI 或核心流程通过该代理执行 Android 自动化动作。
