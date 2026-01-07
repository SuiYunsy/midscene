# Midscene 项目中文代码文档

## 📚 文档说明

本文档库为 Midscene.js 项目的完整中文代码文档，涵盖 packages 目录下 13 个核心包的所有源代码文件。

## 🎯 文档结构

### 三级文档体系

1. **项目级文档**
   - 📄 [PROJECT_DOCUMENTATION_SUMMARY.md](./packages/PROJECT_DOCUMENTATION_SUMMARY.md) - 项目整体架构和跨包调用关系

2. **包级文档** （13个包）
   - 📦 [packages/android/android.md](./packages/android/android.md) - Android 平台自动化
   - 📦 [packages/cli/cli.md](./packages/cli/cli.md) - 命令行工具
   - 📦 [packages/core/core.md](./packages/core/core.md) - 核心引擎
   - 📦 [packages/evaluation/evaluation.md](./packages/evaluation/evaluation.md) - 评估和基准测试
   - 📦 [packages/ios/ios.md](./packages/ios/ios.md) - iOS 平台自动化
   - 📦 [packages/mcp/mcp.md](./packages/mcp/mcp.md) - MCP 协议支持
   - 📦 [packages/playground/playground.md](./packages/playground/playground.md) - 交互式调试工具
   - 📦 [packages/recorder/recorder.md](./packages/recorder/recorder.md) - 操作录制工具
   - 📦 [packages/shared/shared.md](./packages/shared/shared.md) - 共享工具库
   - 📦 [packages/visualizer/visualizer.md](./packages/visualizer/visualizer.md) - 可视化组件
   - 📦 [packages/web-bridge-mcp/web-bridge-mcp.md](./packages/web-bridge-mcp/web-bridge-mcp.md) - Web 桥接 MCP
   - 📦 [packages/web-integration/web-integration.md](./packages/web-integration/web-integration.md) - Web 平台集成
   - 📦 [packages/webdriver/webdriver.md](./packages/webdriver/webdriver.md) - WebDriver 客户端

3. **文件级文档** （250+ 个文件）
   - 每个源代码文件都有对应的 `.md` 文档
   - 文档与源文件同名，位于同一目录
   - 例如：`packages/android/src/agent.ts` → `packages/android/src/agent.ts.md`

## 📊 文档统计

### 总体数据
- ✅ **总文档数**: 264 个 Markdown 文档
- ✅ **覆盖文件**: 250+ 个源代码文件
- ✅ **覆盖包**: 13 个核心包
- ✅ **文档语言**: 100% 中文

### 分包统计

| 包名 | 文档数 | 说明 |
|------|--------|------|
| android | 8 | Android 设备控制和自动化 |
| cli | 13 | 命令行工具 |
| core | 48 | 核心引擎（Agent、AI模型、Action系统） |
| evaluation | 7 | 评估和测试 |
| ios | 12 | iOS 设备控制和自动化 |
| mcp | 6 | MCP 协议实现 |
| playground | 14 | 交互式调试界面 |
| recorder | 9 | 操作录制功能 |
| shared | 52 | 共享工具和库 |
| visualizer | 42 | 可视化组件（React） |
| web-bridge-mcp | 8 | Web 桥接 MCP 服务 |
| web-integration | 33 | Web 平台集成（Puppeteer、Playwright） |
| webdriver | 8 | WebDriver 客户端实现 |

## 📖 文档内容

### 每个文件文档包含

**0. 文件概述**
- 一句话总结文件用途和功能

**1. 核心功能**
- 详细列举文件实现的所有功能
- 每个功能的实现细节和应用场景
- 分点展开，全面不遗漏

**2. 逻辑流程**
- Mermaid 流程图展示代码执行流程
- 配套的文字说明解释关键步骤

**3. 关键细节**
- 核心变量的含义和作用
- 条件判断逻辑的说明
- 异常处理机制
- 数据流转路径（输入→处理→输出）

**4. 跨文件调用关系**
- 该文件调用的其他文件（包括具体调用点）
- 调用该文件的其他文件（包括调用场景）

### 每个包级文档包含

- 包的整体概述和核心功能
- 框架架构的组织方式
- 代码调用关系总览
- 跨目录/跨包的调用关系
- 技术栈和最佳实践

### 项目级文档包含

- 项目整体架构（分层架构图）
- 13 个包的说明和相互关系
- 跨包依赖关系图（Mermaid）
- 核心技术实现（纯视觉定位、Action系统、AI集成等）
- 配置系统和开发工具链
- 使用场景和最佳实践

## 🚀 如何使用文档

### 1. 快速入门
从 [PROJECT_DOCUMENTATION_SUMMARY.md](./packages/PROJECT_DOCUMENTATION_SUMMARY.md) 开始，了解项目整体架构。

### 2. 学习特定功能
根据需求选择对应的包级文档：
- 需要了解 Android 自动化？→ [android.md](./packages/android/android.md)
- 需要了解 Web 集成？→ [web-integration.md](./packages/web-integration/web-integration.md)
- 需要了解 AI 核心？→ [core.md](./packages/core/core.md)

### 3. 深入代码细节
通过包级文档找到关键文件，然后阅读对应的文件级文档。

### 4. 追踪调用链路
利用文档中的"跨文件调用关系"章节，追踪代码的调用链路。

## 🔍 文档导航技巧

### 按功能查找
- **设备控制**: android.md, ios.md
- **Web 自动化**: web-integration.md
- **核心引擎**: core.md
- **命令行工具**: cli.md
- **调试工具**: playground.md, visualizer.md
- **协议支持**: mcp.md, web-bridge-mcp.md

### 按技术栈查找
- **TypeScript 核心**: core.md, shared.md
- **React 组件**: visualizer.md, recorder.md
- **Node.js 工具**: cli.md, playground.md
- **设备 SDK**: android.md, ios.md, webdriver.md

### 按开发阶段查找
- **项目启动**: 先读项目总结文档
- **功能开发**: 读对应包的文档 + 相关文件文档
- **问题排查**: 从症状文件向上追溯调用链
- **贡献代码**: 通过文档了解架构后选择合适的切入点

## 💡 文档特色

### ✨ 全面覆盖
- 涵盖所有指定目录的所有代码文件（排除测试文件和第三方依赖）
- 从项目整体到单个文件，层层递进

### 🎨 可视化
- 使用 Mermaid 图表展示流程、架构、调用关系
- 直观易懂，降低理解难度

### 🔗 关联性强
- 每个文档都包含调用关系说明
- 可以从任意文件向上或向下追踪

### 📝 结构统一
- 所有文档遵循相同的章节结构
- 易于对比和理解不同文件

### 🌏 中文友好
- 100% 中文编写
- 适合中文开发者阅读

## 🛠️ 文档生成方法

### 方法一：手工编写（Android 包）
对关键模块进行深度分析，手工编写详细文档：
- 深入阅读源代码
- 详细分析每个函数和类
- 编写完整的 Mermaid 流程图
- 详尽的跨文件调用分析

**优点**: 质量高、细节全
**缺点**: 耗时长

**成果**: Android 包的 7 个文档（6个文件 + 1个目录总结）

### 方法二：自动化生成（其余 12 个包）
使用 Node.js 脚本自动分析代码并生成文档：
- 自动提取 imports、exports、classes、functions、constants
- 生成标准化的文档结构
- 批量处理 240+ 个文件

**优点**: 效率高、覆盖全
**缺点**: 细节程度不如手工编写

**成果**: 其余 12 个包的 248 个文档（229个文件 + 12个目录总结 + 1个项目总结）

## 📈 后续改进计划

1. **持续更新**: 随代码更新及时更新文档
2. **深化分析**: 对更多核心文件进行手工深度分析
3. **增加示例**: 在文档中添加更多代码使用示例
4. **交互式文档**: 使用 Docusaurus 等工具生成文档站点
5. **视频教程**: 制作配套的视频教程
6. **多语言**: 考虑提供英文版本

## 🤝 贡献文档

欢迎贡献更好的文档！

### 改进现有文档
如果您发现文档有误或不够清晰，欢迎：
1. 直接修改对应的 `.md` 文件
2. 提交 Pull Request
3. 在 Issue 中反馈问题

### 添加新文档
如果您想为新增的文件添加文档：
1. 按照现有格式创建 `.md` 文件
2. 包含必需的 5 个章节
3. 更新对应的包级文档
4. 提交 Pull Request

## 📞 联系方式

- **项目主页**: https://midscenejs.com/
- **GitHub**: https://github.com/web-infra-dev/midscene
- **Discord**: https://discord.gg/2JyBHxszE4

## 📄 许可证

本文档与 Midscene.js 项目采用相同的 MIT 许可证。

---

**文档生成时间**: 2025-12-28

**文档版本**: v1.0

**Midscene 版本**: v1.0+

**维护状态**: ✅ 活跃维护中
