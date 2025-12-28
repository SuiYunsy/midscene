# batch-runner.ts

## 0. 文件概述
batch-runner.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export interface BatchRunnerConfig {`
- `export { BatchRunner };`

### 1.2 类定义
- **BatchRunner**: 类定义

### 1.3 函数定义  
- **to()**: 函数

### 1.4 常量定义
- **fileContextList**: 常量
- **fileConfig**: 常量
- **context**: 常量
- **needsBrowser**: 常量
- **clonedFileConfig**: 常量
- **executionConfig**: 常量
- **executedResults**: 常量
- **notExecutedContexts**: 常量
- **allFileContexts**: 常量
- **player**: 常量
- **summaryContents**: 常量
- **summary**: 常量
- **executeFile**: 常量
- **allFileContext**: 常量
- **startTime**: 常量
- **endTime**: 常量
- **duration**: 常量
- **executedContext**: 常量
- **limit**: 常量
- **tasks**: 常量
- **executedContext**: 常量
- **stopLock**: 常量
- **tasks**: 常量
- **executedContext**: 常量
- **results**: 常量
- **hasFailedTasks**: 常量
- **hasPlayerError**: 常量
- **content**: 常量
- **indexPath**: 常量
- **outputDir**: 常量
- **indexData**: 常量
- **relativePath**: 常量
- **successful**: 常量
- **failed**: 常量
- **partialFailed**: 常量
- **notExecuted**: 常量
- **summary**: 常量
- **success**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **fileContextList**: 定义的常量
- **fileConfig**: 定义的常量
- **context**: 定义的常量
- **needsBrowser**: 定义的常量
- **clonedFileConfig**: 定义的常量
- **executionConfig**: 定义的常量
- **executedResults**: 定义的常量
- **notExecutedContexts**: 定义的常量
- **allFileContexts**: 定义的常量
- **player**: 定义的常量
- **summaryContents**: 定义的常量
- **summary**: 定义的常量
- **executeFile**: 定义的常量
- **allFileContext**: 定义的常量
- **startTime**: 定义的常量
- **endTime**: 定义的常量
- **duration**: 定义的常量
- **executedContext**: 定义的常量
- **limit**: 定义的常量
- **tasks**: 定义的常量
- **executedContext**: 定义的常量
- **stopLock**: 定义的常量
- **tasks**: 定义的常量
- **executedContext**: 定义的常量
- **results**: 定义的常量
- **hasFailedTasks**: 定义的常量
- **hasPlayerError**: 定义的常量
- **content**: 定义的常量
- **indexPath**: 定义的常量
- **outputDir**: 定义的常量
- **indexData**: 定义的常量
- **relativePath**: 定义的常量
- **successful**: 定义的常量
- **failed**: 定义的常量
- **partialFailed**: 定义的常量
- **notExecuted**: 定义的常量
- **summary**: 定义的常量
- **success**: 定义的常量

### 3.2 依赖项
- `import { existsSync, mkdirSync, writeFileSync } from 'node:fs';`
- `import { readFileSync } from 'node:fs';`
- `import { dirname, relative, resolve } from 'node:path';`
- `import type {`
- `import { type ScriptPlayer, parseYamlScript } from '@midscene/core/yaml';`

（共 12 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
- import { readFileSync } from 'node:fs';
- import { dirname, relative, resolve } from 'node:path';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export interface BatchRunnerConfig {
- export { BatchRunner };
