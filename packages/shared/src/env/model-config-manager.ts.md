# model-config-manager.ts

## 0. 文件概述
model-config-manager.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export class ModelConfigManager {`

### 1.2 类定义
- **ModelConfigManager**: 类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **defaultConfig**: 常量
- **insightConfig**: 常量
- **planningConfig**: 常量
- **serverUrl**: 常量
- **modelConfig**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **defaultConfig**: 定义的常量
- **insightConfig**: 定义的常量
- **planningConfig**: 定义的常量
- **serverUrl**: 定义的常量
- **modelConfig**: 定义的常量

### 3.2 依赖项
- `import type { GlobalConfigManager } from './global-config-manager';`
- `import { decideModelConfigFromIntentConfig } from './parse-model-config';`
- `import type {`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import type { GlobalConfigManager } from './global-config-manager';
- import { decideModelConfigFromIntentConfig } from './parse-model-config';
- import type {

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export class ModelConfigManager {
