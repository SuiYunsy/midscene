# 目录核心功能
- 提供与 iOS WebDriverAgent 通讯的客户端与服务管理能力，统一导出请求工具与基础类型。
- 通过管理器控制 WDA 服务生命周期，客户端封装基础 WebDriver API 请求，方便其他平台模块复用。

# 架构与组织方式
- `src/managers`: 服务管理抽象与 WDA 具体实现，负责端口/主机维护与启动检查。
- `src/clients`: WebDriver HTTP 客户端与交互类型定义，承载主要业务调用。
- `src/utils`: 请求层封装与错误类型。
- `src/index.ts`: 聚合导出，作为包入口。

# 目录调用关系总览
- 入口 `src/index.ts` 向外暴露管理器、客户端、类型与请求工具。
- `WebDriverClient` 依赖 `makeWebDriverRequest` 发送 HTTP；`WDAManager` 继承 `BaseServiceManager` 管理生命周期。
- 共享常量/日志均来自 `@midscene/shared` 包：`DEFAULT_WDA_PORT`、`WEBDRIVER_ELEMENT_ID_KEY`、`getDebug` 等。

# 子文件概览
- `managers/ServiceManager.ts`：定义服务管理接口与基础抽象。
- `managers/WDAManager.ts`：实现 iOS WebDriverAgent 的运行状态管理。
- `clients/WebDriverClient.ts`：封装会话创建/截图/窗口尺寸等 WebDriver 调用。
- `clients/types.ts`：声明会话、元素、设备与尺寸等类型。
- `utils/request.ts`：统一 HTTP 请求与错误包装。
- `index.ts`：出口聚合。
