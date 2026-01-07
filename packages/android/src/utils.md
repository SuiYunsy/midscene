# 核心功能
- 使用 `appium-adb` 查询已连接的 Android 设备列表并记录调试信息。
- 对外暴露单一函数 `getConnectedDevices`，为 Agent 创建流程提供设备发现能力。

# 逻辑流程
```mermaid
flowchart TD
  A[getConnectedDevices] --> B[ADB.createADB(adbExecTimeout=60000)]
  B --> C[adb.getConnectedDevices]
  C --> D[记录设备数量日志]
  C --> E[返回设备数组]
  B --> F{异常?}
  F -->|是| G[console.error 并抛出包装错误]
```

# 关键细节
- 核心变量：`debugUtils` 日志实例；`adbExecTimeout` 设置 60s 防止阻塞。
- 条件判断：捕获 `appium-adb` 创建或查询异常，统一包装提示文档链接。
- 异常处理：打印错误到 stderr，并抛出新的 Error（带 cause），指导用户查看文档。
- 数据流：无输入或可选配置 -> 创建 ADB 实例 -> 获取设备数组 -> 调试日志 -> 返回设备列表。

# 跨文件调用关系
- 本文件调用：`@midscene/shared/logger` 输出调试；`appium-adb` 负责实际设备交互。
- 被调用场景：`agentFromAdbDevice` 用于默认选择设备；其他工具可能直接调用以展示设备列表；`src/index.ts` 导出该函数给外部使用。
