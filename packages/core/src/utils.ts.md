# utils.ts

## 0. 文件概述
utils.ts - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export { appendFileSync } from 'node:fs';`
- `export const groupedActionDumpFileExt = 'web-dump.json';`
- `export function processCacheConfig(`
- `export function getReportTpl() {`
- `export function insertScriptBeforeClosingHtml(`
- `export function reportHTMLContent(`
- `export function writeDumpReport(`
- `export function writeLogFile(opts: {`
- `export function getTmpDir(): string | null {`
- `export function getTmpFile(fileExtWithoutDot: string): string | null {`
- `export function overlapped(container: Rect, target: Rect) {`
- `export async function sleep(ms: number) {`
- `export function replacerForPageObject(_key: string, value: any) {`
- `export function stringifyDumpData(data: any, indents?: number) {`
- `export function getVersion() {`
- `export function uploadTestInfoToServer({`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- **processCacheConfig()**: 函数
- **getReportTpl()**: 函数
- **insertScriptBeforeClosingHtml()**: 函数
- **reportHTMLContent()**: 函数
- **writeDumpReport()**: 函数
- **writeLogFile()**: 函数
- **getTmpDir()**: 函数
- **getTmpFile()**: 函数
- **overlapped()**: 函数
- **sleep()**: 函数
- **replacerForPageObject()**: 函数
- **stringifyDumpData()**: 函数
- **getVersion()**: 函数
- **debugLog()**: 函数
- **uploadTestInfoToServer()**: 函数

### 1.4 常量定义
- **groupedActionDumpFileExt**: 常量
- **envEnabled**: 常量
- **reportInitializedMap**: 常量
- **reportTpl**: 常量
- **htmlEndTag**: 常量
- **stat**: 常量
- **readSize**: 常量
- **start**: 常量
- **buffer**: 常量
- **fd**: 常量
- **tailStr**: 常量
- **htmlEndIdx**: 常量
- **beforeHtmlInTail**: 常量
- **htmlEndPos**: 常量
- **writeToFile**: 常量
- **attributesArr**: 常量
- **reportPath**: 常量
- **jsonPath**: 常量
- **targetDir**: 常量
- **gitIgnorePath**: 常量
- **gitPath**: 常量
- **filePath**: 常量
- **runningPkgInfo**: 常量
- **tmpPath**: 常量
- **tmpDir**: 常量
- **filename**: 常量
- **debugMode**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **groupedActionDumpFileExt**: 定义的常量
- **envEnabled**: 定义的常量
- **reportInitializedMap**: 定义的常量
- **reportTpl**: 定义的常量
- **htmlEndTag**: 定义的常量
- **stat**: 定义的常量
- **readSize**: 定义的常量
- **start**: 定义的常量
- **buffer**: 定义的常量
- **fd**: 定义的常量
- **tailStr**: 定义的常量
- **htmlEndIdx**: 定义的常量
- **beforeHtmlInTail**: 定义的常量
- **htmlEndPos**: 定义的常量
- **writeToFile**: 定义的常量
- **attributesArr**: 定义的常量
- **reportPath**: 定义的常量
- **jsonPath**: 定义的常量
- **targetDir**: 定义的常量
- **gitIgnorePath**: 定义的常量
- **gitPath**: 定义的常量
- **filePath**: 定义的常量
- **runningPkgInfo**: 定义的常量
- **tmpPath**: 定义的常量
- **tmpDir**: 定义的常量
- **filename**: 定义的常量
- **debugMode**: 定义的常量

### 3.2 依赖项
- `import { execSync } from 'node:child_process';`
- `import * as fs from 'node:fs';`
- `import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';`
- `import { tmpdir } from 'node:os';`
- `import * as path from 'node:path';`

（共 11 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { execSync } from 'node:child_process';
- import * as fs from 'node:fs';
- import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export { appendFileSync } from 'node:fs';
- export const groupedActionDumpFileExt = 'web-dump.json';
- export function processCacheConfig(
