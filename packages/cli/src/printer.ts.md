# printer.ts

## 0. 文件概述
printer.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export interface MidsceneYamlFileContext {`
- `export const isTTY = process.env.MIDSCENE_CLI_LOG_ON_NON_TTY`
- `export const indent = '  ';`
- `export const spinnerInterval = 80;`
- `export const spinnerFrames = ['◰', '◳', '◲', '◱']; // https://github.com/sindresorhus/cli-spinners/blob/main/spinners.json`
- `export const currentSpinningFrame = () => {`
- `export const contextInfo = (context: MidsceneYamlFileContext) => {`
- `export const singleTaskInfo = (task: ScriptPlayerTaskStatus) => {`
- `export const contextTaskListSummary = (`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- **indicatorForStatus()**: 函数
- **paddingLines()**: 函数

### 1.4 常量定义
- **isTTY**: 常量
- **indent**: 常量
- **spinnerInterval**: 常量
- **spinnerFrames**: 常量
- **currentSpinningFrame**: 常量
- **contextInfo**: 常量
- **filePath**: 常量
- **filePathToShow**: 常量
- **fileNameToPrint**: 常量
- **fileStatusText**: 常量
- **contextActionText**: 常量
- **errorText**: 常量
- **outputFile**: 常量
- **outputText**: 常量
- **reportFile**: 常量
- **reportText**: 常量
- **agentStatusTip**: 常量
- **agentStatusText**: 常量
- **mergedText**: 常量
- **singleTaskInfo**: 常量
- **actionText**: 常量
- **errorText**: 常量
- **statusText**: 常量
- **mergedLine**: 常量
- **contextTaskListSummary**: 常量
- **prefixLines**: 常量
- **currentLine**: 常量
- **suffixText**: 常量
- **lines**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **isTTY**: 定义的常量
- **indent**: 定义的常量
- **spinnerInterval**: 定义的常量
- **spinnerFrames**: 定义的常量
- **currentSpinningFrame**: 定义的常量
- **contextInfo**: 定义的常量
- **filePath**: 定义的常量
- **filePathToShow**: 定义的常量
- **fileNameToPrint**: 定义的常量
- **fileStatusText**: 定义的常量
- **contextActionText**: 定义的常量
- **errorText**: 定义的常量
- **outputFile**: 定义的常量
- **outputText**: 定义的常量
- **reportFile**: 定义的常量
- **reportText**: 定义的常量
- **agentStatusTip**: 定义的常量
- **agentStatusText**: 定义的常量
- **mergedText**: 定义的常量
- **singleTaskInfo**: 定义的常量
- **actionText**: 定义的常量
- **errorText**: 定义的常量
- **statusText**: 定义的常量
- **mergedLine**: 定义的常量
- **contextTaskListSummary**: 定义的常量
- **prefixLines**: 定义的常量
- **currentLine**: 定义的常量
- **suffixText**: 定义的常量
- **lines**: 定义的常量

### 3.2 依赖项
- `import { basename, dirname, relative } from 'node:path';`
- `import type {`
- `import type { ScriptPlayer } from '@midscene/core/yaml';`
- `import chalk from 'chalk';`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { basename, dirname, relative } from 'node:path';
- import type {
- import type { ScriptPlayer } from '@midscene/core/yaml';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export interface MidsceneYamlFileContext {
- export const isTTY = process.env.MIDSCENE_CLI_LOG_ON_NON_TTY
- export const indent = '  ';
