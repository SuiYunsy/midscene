# 目录核心功能
- 提供基于 ADB 的 Android 自动化能力：设备连接、动作执行、Agent 封装与环境配置桥接。
- 入口统一导出设备类、Agent、设备发现工具及环境配置覆盖函数，供核心/CLI 直接调用。

# 架构与组织方式
- `src/device.ts`：实现具体 Android 设备控制与动作集合，是核心实现。
- `src/agent.ts`：继承核心 Agent，将设备动作包装成可调用方法，并提供从 ADB 设备快速构建 Agent 的工厂。
- `src/utils.ts`：轻量工具，负责查询已连接设备。
- `src/index.ts`：包出口，聚合导出主要能力。
- `bin/`、`demo/` 等提供工具和示例，不在代码文档范围。

# 调用关系总览
- `index.ts` 导出 `AndroidDevice`、`AndroidAgent`、`agentFromAdbDevice` 与 `getConnectedDevices`。
- `AndroidAgent` 构造时依赖 `AndroidDevice` 的 ActionSpace；`agentFromAdbDevice` 先用 `getConnectedDevices` 选择设备再初始化设备与 Agent。
- 设备实现大量依赖 `@midscene/core` 动作定义与 `@midscene/shared` 工具（日志、环境配置、图片处理）。

# 目录核心功能总结
- 完整的 Android 端自动化执行链路：从设备发现 -> ADB 连接 -> 动作定义/执行 -> Agent 封装。
- 关注兼容性（多显示、DPI、输入法策略）及稳健性（超时、错误包装、调试日志）。 
