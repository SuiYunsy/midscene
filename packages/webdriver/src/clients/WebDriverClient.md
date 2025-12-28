# 核心功能
- 封装对 WebDriverAgent 的 HTTP 调用，负责创建/删除会话、截屏、窗口尺寸与设备信息查询。
- 管理基础连接参数（host/port/timeout）及会话 ID 的生命周期校验。
- 通过统一的 `makeRequest` 方法复用请求封装和调试日志。

# 逻辑流程
```mermaid
flowchart TD
  A[构造函数: 读取 options 默认端口/主机/超时] --> B[初始化 baseUrl 与调试日志]
  B --> C[createSession: POST /session 保存 sessionId]
  C --> D[takeScreenshot/ getWindowSize 等操作前 ensureSession]
  D --> E[makeRequest 包装调用 makeWebDriverRequest]
  E --> F[返回结果或抛出错误]
  C --> G[deleteSession: DELETE /session/{id} 后清空状态]
  B --> H[getDeviceInfo: GET /status 解析 device 信息]
```

# 关键细节
- 核心变量：`sessionId` 保存当前会话；`baseUrl` 由 host/port 拼接；`timeout` 控制请求超时。
- 条件判断：操作前调用 `ensureSession`，若无会话即抛错；`getDeviceInfo` 通过可选链判断响应是否包含设备字段。
- 异常处理：创建/删除会话时捕获异常并记录 debug；`deleteSession` 失败不抛出以便清理；`ensureSession` 同步抛出提示调用顺序。
- 数据流：输入外部能力参数或请求数据 -> 通过 `makeWebDriverRequest` 发起 HTTP -> 输出标准 WebDriver 响应或解析后的数据（截图 base64、窗口尺寸、设备信息）。

# 跨文件调用关系
- 本文件调用：`@midscene/shared/constants` 提供默认端口，`@midscene/shared/logger` 提供调试日志，`makeWebDriverRequest` 发送 HTTP 请求，类型依赖 `clients/types`.
- 被调用场景：`src/index.ts` 导出 `WebDriverClient` 供外部使用，可能由 Android/iOS 集成或 CLI 调用用于自动化交互。
