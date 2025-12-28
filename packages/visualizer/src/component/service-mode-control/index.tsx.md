# index.tsx

## 0. 文件概述
index.tsx - TypeScript/JavaScript 源文件

## 1. 核心功能

### 1.1 导出项
- `export const ServiceModeControl: React.FC<ServiceModeControlProps> = ({`

### 1.2 类定义
- 无类定义

### 1.3 函数定义  
- 无函数定义

### 1.4 常量定义
- **TITLE_TEXT**: 常量
- **SWITCH_BUTTON_TEXT**: 常量
- **ServiceModeControl**: 常量
- **serverValid**: 常量
- **renderServerTip**: 常量
- **renderSwitchButton**: 常量
- **nextMode**: 常量
- **buttonText**: 常量
- **playgroundSDK**: 常量
- **statusContent**: 常量
- **title**: 常量

## 2. 逻辑流程

```mermaid
graph TD
    A[文件入口] --> B[处理逻辑]
    B --> C[输出结果]
```

**流程说明**: 该文件实现特定功能，通过导入依赖模块，定义类/函数/常量，并导出供其他模块使用。

## 3. 关键细节

### 3.1 核心变量
- **TITLE_TEXT**: 定义的常量
- **SWITCH_BUTTON_TEXT**: 定义的常量
- **ServiceModeControl**: 定义的常量
- **serverValid**: 定义的常量
- **renderServerTip**: 定义的常量
- **renderSwitchButton**: 定义的常量
- **nextMode**: 定义的常量
- **buttonText**: 定义的常量
- **playgroundSDK**: 定义的常量
- **statusContent**: 定义的常量
- **title**: 定义的常量

### 3.2 依赖项
- `import { PlaygroundSDK } from '@midscene/playground';`
- `import { Button, Tooltip } from 'antd';`
- `import type React from 'react';`
- `import { useEffect } from 'react';`
- `import { safeOverrideAIConfig } from '../../hooks/useSafeOverrideAIConfig';`

（共 9 个导入项）

## 4. 跨文件调用关系

### 4.1 该文件调用的其他文件
根据 import 语句，该文件依赖以下模块：
- import { PlaygroundSDK } from '@midscene/playground';
- import { Button, Tooltip } from 'antd';
- import type React from 'react';

### 4.2 调用该文件的其他文件
该文件通过以下导出项被其他模块使用：
- export const ServiceModeControl: React.FC<ServiceModeControlProps> = ({
