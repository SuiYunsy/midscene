# 核心功能
- 提供 WebDriver HTTP 请求封装，统一超时控制、JSON 解析、错误包装与调试日志。
- 定义 `WebDriverRequestError` 错误类型，包含 HTTP 状态码和响应体便于上层定位问题。

# 逻辑流程
```mermaid
flowchart TD
  A[makeWebDriverRequest(baseUrl, method, endpoint, data, timeout)] --> B[拼接 URL & 记录调试日志]
  B --> C[创建 AbortController 设置超时]
  C --> D[fetch 请求 JSON/文本响应]
  D --> E{response.ok?}
  E -->|否| F[构造 WebDriverRequestError 抛出]
  E -->|是| G[返回解析后的响应数据]
  F --> H[异常处理: 区分超时/自定义错误/其他错误]
```

# 关键细节
- 核心变量：`RequestOptions` 接口描述方法/URL/数据/超时；`debugRequest` 日志实例；`timeoutId` 控制超时取消。
- 条件逻辑：根据 `content-type` 判断 JSON 解析还是文本；`response.ok` 失败时提取 error/message 字段。
- 异常处理：自定义错误直接透传；`AbortError` 转换为超时错误；其他错误记录日志后包装成 `WebDriverRequestError`。
- 数据流：输入 baseUrl+endpoint+payload -> fetch 请求 -> 解析响应/抛出错误；输出为 JSON/文本或自定义错误对象。

# 跨文件调用关系
- 本文件调用：依赖 `@midscene/shared/logger` 获取调试日志；使用浏览器 fetch/AbortController。
- 被调用场景：`WebDriverClient.makeRequest` 统一调用此函数发送 HTTP；`src/index.ts` 导出以便其他模块直接复用请求能力。
