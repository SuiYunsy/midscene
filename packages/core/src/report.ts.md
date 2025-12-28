# report.ts

## 0. 文件概述
report.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export class ReportMergingTool {`

### 1.2 类定义
- **ReportMergingTool**: 类定义

### 1.3 函数定义  
- **to()**: 函数

### 1.4 常量定义
- **scriptRegex**: 常量
- **fileContent**: 常量
- **match**: 常量
- **targetDir**: 常量
- **reportInfo**: 常量
- **dumpString**: 常量
- **reportAttributes**: 常量
- **reportHtmlStr**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **scriptRegex**: 定义的常量
- **fileContent**: 定义的常量
- **match**: 定义的常量
- **targetDir**: 定义的常量
- **reportInfo**: 定义的常量
- **dumpString**: 定义的常量
- **reportAttributes**: 定义的常量
- **reportHtmlStr**: 定义的常量

### 3.2 依赖项
- `import * as fs from 'node:fs';`
- `import * as path from 'node:path';`
- `import { getMidsceneRunSubDir } from '@midscene/shared/common';`
- `import { getReportFileName } from './agent';`
- `import type { ReportFileWithAttributes } from './types';`

（共 6 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import * as fs from 'node:fs';
- import * as path from 'node:path';
- import { getMidsceneRunSubDir } from '@midscene/shared/common';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export class ReportMergingTool {
