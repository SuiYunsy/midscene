# index.tsx

## 0. 文件概述
index.tsx - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export const PlaygroundResultView: React.FC<PlaygroundResultProps> = ({`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **PlaygroundResultView**: 常量
- **shouldPrioritizeResult**: 常量
- **errorNode**: 常量
- **resultOutput**: 常量
- **reportContent**: 常量
- **reportContent**: 常量
- **resultOutput**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **PlaygroundResultView**: 定义的常量
- **shouldPrioritizeResult**: 定义的常量
- **errorNode**: 定义的常量
- **resultOutput**: 定义的常量
- **reportContent**: 定义的常量
- **reportContent**: 定义的常量
- **resultOutput**: 定义的常量

### 3.2 依赖项
- `import { LoadingOutlined } from '@ant-design/icons';`
- `import { noReplayAPIs } from '@midscene/playground';`
- `import { Spin } from 'antd';`
- `import type React from 'react';`
- `import type { PlaygroundResult as PlaygroundResultType } from '../../types';`

（共 11 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { LoadingOutlined } from '@ant-design/icons';
- import { noReplayAPIs } from '@midscene/playground';
- import { Spin } from 'antd';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export const PlaygroundResultView: React.FC<PlaygroundResultProps> = ({
