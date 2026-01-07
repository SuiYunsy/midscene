# cli-utils.ts

## 0. 文件概述
cli-utils.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export const parseProcessArgs = async (): Promise<{`
- `export async function matchYamlFiles(`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- **kebabToCamel()**: 函数
- **camelToKebab()**: 函数
- **to()**: 函数
- **matchYamlFiles()**: 函数

### 1.4 常量定义
- **debug**: 常量
- **parseProcessArgs**: 常量
- **args**: 常量
- **argv**: 常量
- **transformedArgv**: 常量
- **ensureBothFormats**: 常量
- **result**: 常量
- **camelKey**: 常量
- **kebabKey**: 常量
- **ignore**: 常量
- **files**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **debug**: 定义的常量
- **parseProcessArgs**: 定义的常量
- **args**: 定义的常量
- **argv**: 定义的常量
- **transformedArgv**: 定义的常量
- **ensureBothFormats**: 定义的常量
- **result**: 定义的常量
- **camelKey**: 定义的常量
- **kebabKey**: 定义的常量
- **ignore**: 定义的常量
- **files**: 定义的常量

### 3.2 依赖项
- `import { existsSync, statSync } from 'node:fs';`
- `import { join } from 'node:path';`
- `import { getDebug } from '@midscene/shared/logger';`
- `import { glob } from 'glob';`
- `import { hideBin } from 'yargs/helpers';`

（共 7 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { existsSync, statSync } from 'node:fs';
- import { join } from 'node:path';
- import { getDebug } from '@midscene/shared/logger';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export const parseProcessArgs = async (): Promise<{
- export async function matchYamlFiles(
