# Nexus（本地AI智能中枢）MVP 规范文档

## Why
当前AI工具存在隐私焦虑、工具碎片化、上下文丢失、行动力弱等核心痛点。Nexus旨在打造一个100%本地处理的AI指挥中心，统一调度所有模型，自动执行本地任务，让数据不出本地，真正为用户工作。

## What Changes
- 创建基于 Tauri v2 + Vue3 + Python(FastAPI) 的桌面应用架构
- 实现统一AI模型接入层，支持 Ollama、OpenAI、DeepSeek 等多模型
- 构建本地知识库系统，支持文档上传、向量化存储和智能检索
- 开发本地动作执行引擎，安全执行文件操作和系统命令
- 实现三层记忆架构（瞬时/工作/长期记忆）
- 打造现代化用户界面，支持深色/浅色主题和多语言

## Impact
- 新项目初始化，无现有代码影响
- 目标用户：隐私敏感型用户、开发者、高效率工作者、智能设备爱好者
- 核心价值：隐私安全、统一入口、长期记忆、本地执行

---

## ADDED Requirements

### Requirement: 统一AI模型接入层（MVP核心）

系统应提供统一的AI模型接入能力，支持多种本地和云端模型的无缝切换。

#### Scenario: 多模型切换
- **WHEN** 用户点击模型选择下拉菜单
- **THEN** 显示所有已配置模型（Ollama本地模型、GPT-4、DeepSeek等），并标注当前状态（可用/不可用/加载中）

#### Scenario: 快速配置新模型
- **WHEN** 用户点击"添加模型"按钮
- **THEN** 弹出配置界面，支持输入API Key或本地模型路径，一键完成配置

#### Scenario: 对话历史管理
- **WHEN** 用户查看对话历史
- **THEN** 显示本地加密存储的所有对话记录，支持按时间/模型筛选

### Requirement: 本地知识库系统（MVP核心）

系统应支持用户上传文档，并基于文档内容进行智能问答。

#### Scenario: 文档上传与解析
- **WHEN** 用户拖拽上传PDF、Markdown、TXT等格式文档
- **THEN** 系统自动解析文档内容，提取文本并进行向量化存储

#### Scenario: 智能检索问答
- **WHEN** 用户提出与文档相关的问题
- **THEN** 系统基于向量检索返回最相关的文档片段，并结合AI生成回答

#### Scenario: 文档管理
- **WHEN** 用户访问文档管理界面
- **THEN** 显示已上传文档列表，支持删除、重命名等操作

### Requirement: 本地动作执行引擎（MVP核心）

系统应支持AI安全地执行本地文件操作和系统命令。

#### Scenario: 安全沙箱确认
- **WHEN** AI请求执行本地命令
- **THEN** 弹出确认对话框，显示命令详情，需用户明确授权后执行

#### Scenario: 预定义动作执行
- **WHEN** 用户选择预定义动作（如"整理Downloads文件夹"）
- **THEN** 系统安全执行对应操作，并显示执行结果

#### Scenario: 自定义脚本支持
- **WHEN** 用户编写并保存Python脚本
- **THEN** 脚本可在对话中被AI调用，扩展系统功能

### Requirement: 三层记忆架构（差异化核心）

系统应实现突破大模型上下文限制的长期记忆能力。

#### Scenario: 瞬时记忆管理
- **WHEN** 进行对话交互
- **THEN** 系统使用滑动窗口管理上下文，扩展至100K tokens

#### Scenario: 工作记忆更新
- **WHEN** 对话中产生重要信息
- **THEN** 系统自动将信息存入向量数据库和知识图谱，支持分钟级更新

#### Scenario: 长期记忆检索
- **WHEN** 用户提问涉及历史信息
- **THEN** 系统跨会话检索相关记忆片段，提供连贯回答

#### Scenario: 记忆管理
- **WHEN** 用户访问记忆管理界面
- **THEN** 显示所有记忆片段，支持查看、编辑、删除操作

### Requirement: 用户界面与交互

系统应提供现代、简洁、高效的用户界面。

#### Scenario: 主界面布局
- **WHEN** 用户启动应用
- **THEN** 显示左侧模型选择/文档管理面板，右侧对话区域

#### Scenario: 流式响应显示
- **WHEN** AI生成回复
- **THEN** 实时流式显示响应内容，支持Markdown格式和代码高亮

#### Scenario: 主题切换
- **WHEN** 用户切换主题
- **THEN** 应用立即切换深色/浅色模式，支持自定义颜色

#### Scenario: 快捷键支持
- **WHEN** 用户按下快捷键（Ctrl+Enter发送、Ctrl+L清空等）
- **THEN** 执行对应操作

### Requirement: 技术架构

系统应基于指定技术栈构建。

#### Scenario: 桌面框架
- **WHEN** 构建桌面应用
- **THEN** 使用 Tauri v2 作为框架，Rust后端，比Electron更轻量

#### Scenario: 前端开发
- **WHEN** 开发用户界面
- **THEN** 使用 Vue3 + TypeScript + Tailwind CSS，组件化开发

#### Scenario: 后端逻辑
- **WHEN** 实现AI逻辑
- **THEN** 使用 Python (FastAPI)，AI生态最丰富

#### Scenario: 数据存储
- **WHEN** 存储向量数据
- **THEN** 使用 SQLite-vec 单文件数据库，无需部署服务器

### Requirement: 数据安全

系统应确保用户数据安全。

#### Scenario: 本地存储
- **WHEN** 保存用户数据（对话、文档、记忆）
- **THEN** 所有数据存储在用户本地，不上传云端

#### Scenario: 加密存储
- **WHEN** 存储敏感数据
- **THEN** 使用 AES-256 加密

#### Scenario: 离线功能
- **WHEN** 无网络连接
- **THEN** 核心AI功能（本地模型）仍可正常使用

### Requirement: 性能指标

系统应满足性能要求。

#### Scenario: 启动性能
- **WHEN** 用户启动应用
- **THEN** 首次启动<5秒，后续启动<1秒

#### Scenario: 响应速度
- **WHEN** 用户发送消息
- **THEN** AI响应延迟<800ms（本地模型）/1.5s（云端模型）

#### Scenario: 资源占用
- **WHEN** 应用运行
- **THEN** 内存<1.5GB，CPU<50%（单线程）

### Requirement: 兼容性

系统应支持多平台运行。

#### Scenario: 操作系统支持
- **WHEN** 用户在不同平台使用
- **THEN** 支持 Windows 10+、macOS 12+、Linux (Ubuntu 22.04+)

#### Scenario: 硬件要求
- **WHEN** 用户安装应用
- **THEN** 支持 Intel/AMD 64位处理器，8GB RAM，10GB可用磁盘空间
