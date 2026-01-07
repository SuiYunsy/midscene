# io-server.ts

## 0. 文件概述
io-server.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export const killRunningServer = async (port?: number, host = 'localhost') => {`
- `export class BridgeServer {`

### 1.2 类定义
- **BridgeServer**: 类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **killRunningServer**: 常量
- **client**: 常量
- **httpServer**: 常量
- **url**: 常量
- **clientVersion**: 常量
- **id**: 常量
- **response**: 常量
- **error**: 常量
- **call**: 常量
- **errorMessage**: 常量
- **payload**: 常量
- **call**: 常量
- **call**: 常量
- **message**: 常量
- **id**: 常量
- **timeoutId**: 常量
- **closeProcess**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **killRunningServer**: 定义的常量
- **client**: 定义的常量
- **httpServer**: 定义的常量
- **url**: 定义的常量
- **clientVersion**: 定义的常量
- **id**: 定义的常量
- **response**: 定义的常量
- **error**: 定义的常量
- **call**: 定义的常量
- **errorMessage**: 定义的常量
- **payload**: 定义的常量
- **call**: 定义的常量
- **call**: 定义的常量
- **message**: 定义的常量
- **id**: 定义的常量
- **timeoutId**: 定义的常量
- **closeProcess**: 定义的常量

### 3.2 依赖项
- `import { createServer } from 'node:http';`
- `import { sleep } from '@midscene/core/utils';`
- `import { logMsg } from '@midscene/shared/utils';`
- `import { Server, type Socket as ServerSocket } from 'socket.io';`
- `import { io as ClientIO } from 'socket.io-client';`

（共 6 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { createServer } from 'node:http';
- import { sleep } from '@midscene/core/utils';
- import { logMsg } from '@midscene/shared/utils';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export const killRunningServer = async (port?: number, host = 'localhost') => {
- export class BridgeServer {
