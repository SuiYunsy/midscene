# fs.ts

## 0. 文件概述
fs.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export function getRunningPkgInfo(dir?: string): PkgInfo | null {`
- `export function findNearestPackageJson(dir: string): string | null {`
- `export function getElementInfosScriptContent() {`
- `export async function getExtraReturnLogic(tree = false) {`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- **getRunningPkgInfo()**: 函数
- **findNearestPackageJson()**: 函数
- **getElementInfosScriptContent()**: 函数
- **getExtraReturnLogic()**: 函数

### 1.4 常量定义
- **pkgCacheMap**: 常量
- **dirToCheck**: 常量
- **pkgDir**: 常量
- **pkgJsonFile**: 常量
- **packageJsonPath**: 常量
- **parentDir**: 常量
- **htmlElementScript**: 常量
- **elementInfosScriptContent**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **pkgCacheMap**: 定义的常量
- **dirToCheck**: 定义的常量
- **pkgDir**: 定义的常量
- **pkgJsonFile**: 定义的常量
- **packageJsonPath**: 定义的常量
- **parentDir**: 定义的常量
- **htmlElementScript**: 定义的常量
- **elementInfosScriptContent**: 定义的常量

### 3.2 依赖项
- `import { existsSync, readFileSync } from 'node:fs';`
- `import { dirname, join } from 'node:path';`
- `import { ifInBrowser, ifInWorker } from '../utils';`


## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { existsSync, readFileSync } from 'node:fs';
- import { dirname, join } from 'node:path';
- import { ifInBrowser, ifInWorker } from '../utils';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export function getRunningPkgInfo(dir?: string): PkgInfo | null {
- export function findNearestPackageJson(dir: string): string | null {
- export function getElementInfosScriptContent() {
