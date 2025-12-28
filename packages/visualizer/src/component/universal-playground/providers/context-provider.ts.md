# context-provider.ts

## 0. 文件概述
context-provider.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export abstract class BaseContextProvider implements ContextProvider {`
- `export class AgentContextProvider extends BaseContextProvider {`
- `export class StaticContextProvider extends BaseContextProvider {`
- `export class NoOpContextProvider implements ContextProvider {`

### 1.2 类定义
- **BaseContextProvider**: 类定义
- **AgentContextProvider**: 类定义
- **StaticContextProvider**: 类定义
- **NoOpContextProvider**: 类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **agent**: 常量
- **context**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **agent**: 定义的常量
- **context**: 定义的常量

### 3.2 依赖项
- `import type { UIContext } from '@midscene/core';`
- `import type { ContextProvider } from '../../../types';`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import type { UIContext } from '@midscene/core';
- import type { ContextProvider } from '../../../types';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export abstract class BaseContextProvider implements ContextProvider {
- export class AgentContextProvider extends BaseContextProvider {
- export class StaticContextProvider extends BaseContextProvider {
