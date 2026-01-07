# launcher.ts

## 0. 文件概述
launcher.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export interface LaunchPlaygroundOptions {`
- `export interface LaunchPlaygroundResult {`
- `export function playgroundForAgent(agent: Agent) {`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- **playgroundForAgent()**: 函数
- **openInBrowser()**: 函数

### 1.4 常量定义
- **webPage**: 常量
- **server**: 常量
- **launchedServer**: 常量
- **url**: 常量
- **child**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **webPage**: 定义的常量
- **server**: 定义的常量
- **launchedServer**: 定义的常量
- **url**: 定义的常量
- **child**: 定义的常量

### 3.2 依赖项
- `import { spawn } from 'node:child_process';`
- `import type { Agent, Agent as PageAgent } from '@midscene/core/agent';`
- `import { PLAYGROUND_SERVER_PORT } from '@midscene/shared/constants';`
- `import cors from 'cors';`
- `import PlaygroundServer from './server';`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { spawn } from 'node:child_process';
- import type { Agent, Agent as PageAgent } from '@midscene/core/agent';
- import { PLAYGROUND_SERVER_PORT } from '@midscene/shared/constants';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export interface LaunchPlaygroundOptions {
- export interface LaunchPlaygroundResult {
- export function playgroundForAgent(agent: Agent) {
