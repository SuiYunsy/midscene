# inject-report-html-plugin.ts

## 0. 文件概述
inject-report-html-plugin.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export function injectReportHtmlFromCore(packageDir: string) {`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- **injectReportHtmlFromCore()**: 函数

### 1.4 常量定义
- **MAGIC_STRING**: 常量
- **REPLACED_MARK**: 常量
- **REG_EXP_FOR_REPLACE**: 常量
- **coreUtilsPath**: 常量
- **coreContent**: 常量
- **markerIndex**: 常量
- **jsonStart**: 常量
- **jsonString**: 常量
- **finalContent**: 常量
- **distDir**: 常量
- **jsFiles**: 常量
- **filePath**: 常量
- **content**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **MAGIC_STRING**: 定义的常量
- **REPLACED_MARK**: 定义的常量
- **REG_EXP_FOR_REPLACE**: 定义的常量
- **coreUtilsPath**: 定义的常量
- **coreContent**: 定义的常量
- **markerIndex**: 定义的常量
- **jsonStart**: 定义的常量
- **jsonString**: 定义的常量
- **finalContent**: 定义的常量
- **distDir**: 定义的常量
- **jsFiles**: 定义的常量
- **filePath**: 定义的常量
- **content**: 定义的常量

### 3.2 依赖项
- `import fs from 'node:fs';`
- `import path from 'node:path';`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import fs from 'node:fs';
- import path from 'node:path';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export function injectReportHtmlFromCore(packageDir: string) {
