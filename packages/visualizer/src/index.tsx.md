# index.tsx

## 0. 文件概述
index.tsx - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export {`
- `export { useEnvConfig, useGlobalPreference } from './store/store';`
- `export {`
- `export { EnvConfig } from './component/env-config';`
- `export { EnvConfigReminder } from './component/env-config-reminder';`
- `export { NavActions } from './component/nav-actions';`
- `export type { NavActionsProps } from './component/nav-actions';`
- `export { Logo } from './component/logo';`
- `export { iconForStatus, timeCostStrElement } from './component/misc';`
- `export { useTheme } from './hooks/useTheme';`
- `export { useServerValid } from './hooks/useServerValid';`
- `export {`
- `export { PlaygroundResultView } from './component/playground-result';`
- `export type { PlaygroundResult } from './types';`
- `export { ServiceModeControl } from './component/service-mode-control';`
- `export { ContextPreview } from './component/context-preview';`
- `export { PromptInput } from './component/prompt-input';`
- `export { Player } from './component/player';`
- `export { Blackboard } from './component/blackboard';`
- `export { default as ScreenshotViewer } from './component/screenshot-viewer';`
- `export {`
- `export { timeStr, filterBase64Value } from './utils';`
- `export { default as ShinyText } from './component/shiny-text';`
- `export {`
- `export type {`
- `export {`
- `export {`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- 无常量定义

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- 无核心变量

### 3.2 依赖项
- 无外部依赖


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
- 无外部调用

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export {
- export { useEnvConfig, useGlobalPreference } from './store/store';
- export {
