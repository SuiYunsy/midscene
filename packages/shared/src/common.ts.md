# common.ts

## 0. 文件概述
common.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export const defaultRunDirName = 'midscene_run';`
- `export const getMidsceneRunDir = () => {`
- `export const getMidsceneRunBaseDir = () => {`
- `export const getMidsceneRunSubDir = (`
- `export const ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED =`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **defaultRunDirName**: 常量
- **getMidsceneRunDir**: 常量
- **getMidsceneRunBaseDir**: 常量
- **getMidsceneRunSubDir**: 常量
- **basePath**: 常量
- **logPath**: 常量
- **ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **defaultRunDirName**: 定义的常量
- **getMidsceneRunDir**: 定义的常量
- **getMidsceneRunBaseDir**: 定义的常量
- **getMidsceneRunSubDir**: 定义的常量
- **basePath**: 定义的常量
- **logPath**: 定义的常量
- **ERROR_CODE_NOT_IMPLEMENTED_AS_DESIGNED**: 定义的常量

### 3.2 依赖项
- `import { existsSync, mkdirSync } from 'node:fs';`
- `import { tmpdir } from 'node:os';`
- `import path from 'node:path';`
- `import { getBasicEnvValue } from './env/basic';`
- `import { MIDSCENE_RUN_DIR } from './env/types';`

（共 6 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { existsSync, mkdirSync } from 'node:fs';
- import { tmpdir } from 'node:os';
- import path from 'node:path';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export const defaultRunDirName = 'midscene_run';
- export const getMidsceneRunDir = () => {
- export const getMidsceneRunBaseDir = () => {
