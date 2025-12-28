# 目录核心功能
- 集成 iOS WebDriverAgent 自动化能力：环境检测、设备控制、代理封装、Playground 启动以及专用 WebDriver 客户端。
- 提供从环境校验 -> 连接 WDA -> 构建设备/代理 -> 启动 Playground 的完整链路。

# 架构与组织方式
- `src/device.ts`：核心设备实现，封装 WDA 操作与 ActionSpace。
- `src/agent.ts`：代理封装及自动化工厂 `agentFromWebDriverAgent`。
- `src/ios-webdriver-client.ts`：继承通用客户端的 iOS 扩展。
- `src/utils.ts`：环境检测工具。
- `src/bin.ts`：Playground 交互式启动入口。
- `src/index.ts`：聚合导出。

# 调用关系总览
- 入口 `index.ts` 向外暴露设备、代理、客户端与环境工具。
- `agentFromWebDriverAgent` 先调用 `checkIOSEnvironment`，再使用 `IOSDevice.connect`，最终返回 `IOSAgent`。
- `IOSDevice` 使用 `IOSWebDriverClient` 与 `WDAManager` 执行具体 WDA 请求；`IOSWebDriverClient` 复用 `makeWebDriverRequest` 并扩展 iOS 特性。
- Playground 入口通过 `IOSDevice`/`IOSAgent` 创建 `PlaygroundServer`，对外提供可视化操作。

# 目录核心功能总结
- 覆盖 iOS 自动化的检测、连接、操作与调试；强调 WDA 兼容性与用户引导（错误信息、交互式选择）。
