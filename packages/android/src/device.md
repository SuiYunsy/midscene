# 核心功能
- 封装 Android 设备接入与操作，基于 `appium-adb` 提供连接、截图、滚动、输入、拖拽等动作，并将动作注册到 Midscene 的 ActionSpace。
- 处理分辨率/缩放、显示编号、多屏、输入法策略等兼容性细节，保证坐标与手势正确。
- 提供拉起 App/URL、执行 ADB 命令、YADB 辅助输入、截屏/强制截屏、键盘控制等全链路能力。

# 逻辑流程
```mermaid
flowchart TD
  A[构造 AndroidDevice(deviceId, options)] --> B[保存配置/自定义动作]
  B --> C[actionSpace 返回默认+平台+自定义动作]
  B --> D[getAdb/ connect 建立 ADB 连接]
  D --> E[初始化描述/屏幕尺寸缓存]
  E --> F[动作调用如 launch/scroll/screenshot 基于 ADB 执行]
  F --> G[输入类动作 -> ensureYadb/keyboardType/hideKeyboard]
  F --> H[滚动/拖拽 -> adjustCoordinates 缩放处理]
  F --> I[screenshotBase64 -> 优先 adb.takeScreenshot -> fallback screencap -> base64]
  F --> J[size/getScreenSize -> 解析 dumpsys/wm 输出并缓存]
  K[destroy] --> L[释放 ADB 状态标记]
```

# 关键细节
- 核心变量：`deviceId` 设备标识；`adb`/`connectingAdb` 连接实例与异步锁；`devicePixelRatio`、`scalingRatio` 控制坐标缩放；`cachedScreenSize/cachedOrientation` 缓存屏幕信息；`yadbPushed` 确保辅助二进制只推送一次。
- 条件逻辑：`getAdb` 复用已连实例或等待连接；`getScreenSize` 优先使用 displayId 的 dumpsys 结果，失败再用 `wm size`；滚动/拖拽根据方向调整起止点并限制越界；键盘清理根据策略选择 yadb 或批量删除。
- 异常处理：连接失败、截图无效、滚动方向错误等均抛出带提示的错误；多数 ADB 调用通过代理包装错误信息并附带文档链接；部分清理/停止操作吞噬错误仅日志。
- 数据流：输入动作参数/坐标/文本 -> 通过缩放与调整 -> ADB shell/专用 API 执行 -> 输出动作结果（字符串、布尔、Base64 截图或无返回）。屏幕信息/密度解析后写入缓存供后续调用。

# 跨文件调用关系
- 本文件调用：大量依赖 `@midscene/core` 的动作定义、类型校验（zod）、工具函数 `getTmpFile/sleep/repeat`，以及 `@midscene/shared` 的环境变量/图片工具/UUID/日志等；`appium-adb` 提供底层设备控制；`createRequire` 定位 yadb 二进制。
- 被调用场景：`AndroidAgent` 持有并调用设备实例执行动作；`agentFromAdbDevice` 构造并连接设备；`src/index.ts` 导出以供外部直接使用。
