# WDAManager.ts

## 0. 文件概述
WDAManager.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export interface WDAConfig {`
- `export class WDAManager extends BaseServiceManager {`

### 1.2 类定义
- **WDAManager**: 类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **execAsync**: 常量
- **debugWDA**: 常量
- **key**: 常量
- **url**: 常量
- **response**: 常量
- **responseText**: 常量
- **startTime**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **execAsync**: 定义的常量
- **debugWDA**: 定义的常量
- **key**: 定义的常量
- **url**: 定义的常量
- **response**: 定义的常量
- **responseText**: 定义的常量
- **startTime**: 定义的常量

### 3.2 依赖项
- `import { exec } from 'node:child_process';`
- `import { promisify } from 'node:util';`
- `import { DEFAULT_WDA_PORT } from '@midscene/shared/constants';`
- `import { getDebug } from '@midscene/shared/logger';`
- `import { BaseServiceManager } from './ServiceManager';`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { exec } from 'node:child_process';
- import { promisify } from 'node:util';
- import { DEFAULT_WDA_PORT } from '@midscene/shared/constants';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export interface WDAConfig {
- export class WDAManager extends BaseServiceManager {
