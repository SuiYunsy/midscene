# 核心功能
- 管理 iOS WebDriverAgent (WDA) 服务生命周期，提供单例访问、启动检测与状态等待。
- 负责检查 WDA 端口可用、提示手动启动步骤，并维护运行状态标记。
- 通过继承 `BaseServiceManager` 继承端点/重启能力，结合调试日志输出运行情况。

# 逻辑流程
```mermaid
flowchart TD
  A[getInstance(port,host)] --> B{缓存中存在?}
  B -->|是| C[返回现有实例]
  B -->|否| D[创建新 WDAManager 存入 Map]
  D --> C
  C --> E[start]
  E --> F{已启动?}
  F -->|是| G[记录日志直接返回]
  F -->|否| H[isWDARunning 检查端口]
  H -->|已运行| I[标记 isStarted=true]
  H -->|未运行| J[startWDA -> checkWDAPreparation]
  J --> K[waitForWDA 等待就绪或超时]
  K --> I
  I --> L[可通过 restart/stop 控制]
```

# 关键细节
- 核心变量：`config` 保存端口/主机/BundleId 等配置，`isStarted` 标记运行状态，`instances` Map 实现多端口单例。
- 条件逻辑：`start` 内先短路已启动或端口已被占用；`waitForWDA` 轮询直到超时抛错。
- 异常处理：启动失败、未准备好时抛出带引导文案的错误；`stop` 过程捕获异常仅日志输出。
- 数据流：输入为 `WDAConfig` 或默认端口；经过 `checkWDAPreparation` 检查、`isWDARunning` 网络请求；输出为状态更新与异常提示。

# 跨文件调用关系
- 本文件调用：调用 `@midscene/shared/logger` 获取调试日志，使用 `BaseServiceManager` 继承基础能力，依赖 `DEFAULT_WDA_PORT` 常量并通过 `fetch` 检查 `/status`。
- 被调用场景：`src/index.ts` 导出 `WDAManager` 与 `WDAConfig` 类型供外部管理 iOS WebDriverAgent 服务；上层客户端可通过 `WDAManager.getInstance` 控制服务生命周期。
