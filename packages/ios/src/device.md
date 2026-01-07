# 核心功能
- 封装基于 WebDriverAgent 的 iOS 设备操作：连接/会话管理、截图、输入、滚动/拖拽、Home/App Switcher、WDA 直接请求等。
- 定义并注册 iOS 平台特定的 ActionSpace 动作（Launch、RunWdaRequest、IOSHomeButton、IOSAppSwitcher），并复用通用点击/输入/滚动动作。
- 处理屏幕尺寸、DPR、手势坐标、键盘关闭等细节，确保操作与 AI 上下文一致。

# 逻辑流程
```mermaid
flowchart TD
  A[构造 IOSDevice(opts)] --> B[初始化 WDA Backend+Manager with host/port]
  B --> C[actionSpace 组装默认动作+平台动作+自定义动作]
  D[connect] --> E[wdaManager.start()]
  E --> F[wdaBackend.createSession -> 获取设备信息]
  F --> G[更新 deviceId/description -> 获取屏幕尺寸]
  H[launch/openUrl/runWdaRequest 等调用] --> I[wdaBackend 对应接口]
  J[screenshotBase64] --> K[wdaBackend.takeScreenshot -> base64 封装]
  L[输入/键盘/滚动/拖拽等操作] --> M[调用 wdaBackend 手势接口 + 辅助算法/缓存]
  N[destroy] --> O[wdaBackend.deleteSession + wdaManager.stop]
```

# 关键细节
- 核心变量：`deviceId`（连接后更新为 UDID）、`wdaBackend`/`wdaManager`（负责 HTTP 与服务状态）、`devicePixelRatio` 缓存屏幕倍率、`customActions` 扩展动作集合。
- 条件逻辑：`connect` 前校验未销毁；屏幕信息与 DPR 首次获取后缓存；滚动到边界采用截图对比避免无限滚动；键盘处理优先 WDA dismiss，失败回退手势。
- 异常处理：连接/启动应用/截图等失败时记录调试日志并抛出错误；清理阶段错误吞噬仅日志；滚动异常捕获后继续尝试。
- 数据流：输入动作/坐标/文本 -> 调用 WDA 接口（tap/swipe/keys/settings）-> 输出截图 base64、尺寸、或执行结果；ActionSpace 定义绑定到上层 Agent。

# 跨文件调用关系
- 本文件调用：`@midscene/core` 动作定义/类型/工具、`@midscene/shared` 常量/图像处理/日志、`@midscene/webdriver` 的 `WDAManager`、`ios-webdriver-client` 作为后端。
- 被调用场景：`IOSAgent` 作为设备实例使用其 ActionSpace；`agentFromWebDriverAgent` 在连接后构建 Agent；`src/index.ts` 直接导出供外部使用。
