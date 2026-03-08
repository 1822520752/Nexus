<div align="center">

# Nexus

### Your Local AI Command Center

**您的本地AI智能中枢**

[![GitHub release](https://img.shields.io/github/v/release/1822520752/Nexus?include_prereleases&label=version)](https://github.com/1822520752/Nexus/releases)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/1822520752/Nexus/release.yml?label=build&logo=github)](https://github.com/1822520752/Nexus/actions/workflows/release.yml)
[![GitHub Downloads](https://img.shields.io/github/downloads/1822520752/Nexus/total?label=downloads)](https://github.com/1822520752/Nexus/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[![Tauri](https://img.shields.io/badge/Tauri-v2-24C8D8.svg)](https://tauri.app/)
[![Vue](https://img.shields.io/badge/Vue-3.4-4FC08D.svg)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg)](https://www.typescriptlang.org/)

**[English](#english)** | **[中文](#中文)**

<img src="https://star-history.com/#1822520752/Nexus&Date" alt="Star History Chart" width="600"/>

</div>

---

## English

### 🎯 Overview

Nexus is a **100% local processing** AI command center that unifies all AI models and automatically executes local tasks. Keep your data local and make AI truly work for you.

### ✨ Key Features

#### 🔒 Privacy & Security

- **100% Local Processing** - Your data never leaves your device
- **AES-256 Encryption** - Sensitive data encrypted at rest
- **Offline Capable** - Core features work without internet

#### 🤖 Unified AI Model Access

- **Multi-model Support** - Seamlessly switch between Ollama, OpenAI, DeepSeek, and more
- **One-click Switching** - Quickly switch between different models
- **Status Monitoring** - Real-time detection of model availability

#### 📚 Local Knowledge Base

- **Document Upload** - Support for PDF, Markdown, TXT, DOCX, HTML formats
- **Smart Chunking** - Adaptive text chunking algorithm (paragraph/semantic/hybrid)
- **Vector Retrieval** - Hybrid search strategy (keyword + vector)

#### ⚡ Local Action Execution

- **Secure Sandbox** - All commands require user confirmation before execution
- **Predefined Actions** - File organization, note creation, system info queries
- **Script Support** - Custom Python script extensions with safe execution

#### 🧠 Three-Layer Memory Architecture

- **Instant Memory** - Sliding window context management (100K tokens)
- **Working Memory** - Knowledge graph + vector storage, minute-level updates
- **Long-term Memory** - Cross-session memory retrieval with importance scoring

### 🛠️ Tech Stack

| Module            | Technology                                                                          | Description                              |
| ----------------- | ----------------------------------------------------------------------------------- | ---------------------------------------- |
| Desktop Framework | [Tauri v2](https://tauri.app/)                                                      | Rust backend, lightweight and secure     |
| Frontend UI       | [Vue 3](https://vuejs.org/) + TypeScript + [Tailwind CSS](https://tailwindcss.com/) | Component-based development              |
| Backend Logic     | [Python](https://python.org/) + [FastAPI](https://fastapi.tiangolo.com/)            | Rich AI ecosystem                        |
| Vector Database   | [SQLite-vec](https://github.com/asg017/sqlite-vec)                                  | Single file, no server deployment needed |
| Model Integration | [LiteLLM](https://github.com/BerriAI/litellm)                                       | Unified AI interface                     |

### 📦 Installation

#### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Python](https://python.org/) 3.11+
- [Rust](https://www.rust-lang.org/) 1.70+
- [Ollama](https://ollama.ai/) (optional, for local models)

#### Quick Start

```bash
# Clone the repository
git clone https://github.com/1822520752/Nexus.git
cd Nexus

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Start development server
cd ..
npm run tauri dev
```

### 🚀 Usage Guide

#### 1. Configure AI Models

After launching, click **"Model Management"** in the left sidebar:

**Ollama (Local Models)**

```bash
# Install Ollama
# Windows: Download from https://ollama.ai/download
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Download a model
ollama pull llama2
ollama pull mistral

# Nexus will auto-detect local Ollama service at http://localhost:11434
```

**OpenAI / DeepSeek**

- Click **"Add Model"**
- Select provider (OpenAI/DeepSeek)
- Enter your API Key
- Save configuration

#### 2. Upload Knowledge Base Documents

- Click **"Document Management"** in the left sidebar
- Drag and drop PDF, Markdown, or TXT files
- Wait for processing to complete
- Reference document content in conversations

#### 3. Use Action Execution

- Click **"Action Panel"** in the left sidebar
- Select predefined actions or custom scripts
- Review and confirm execution permissions
- View execution results

### ⌨️ Keyboard Shortcuts

| Shortcut       | Action             |
| -------------- | ------------------ |
| `Ctrl + Enter` | Send message       |
| `Ctrl + L`     | Clear conversation |
| `Ctrl + N`     | New conversation   |
| `Ctrl + S`     | Save settings      |
| `Ctrl + ,`     | Open settings      |

### 🔧 Configuration

#### Environment Variables (`.env`)

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/nexus.db

# Vector dimension (OpenAI embedding)
VECTOR_DIMENSION=1536

# Log level
LOG_LEVEL=INFO
```

### 🧪 Testing

```bash
# Run backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app tests/

# Run frontend tests
npm run test
```

### 📦 Build & Release

```bash
# Windows
.\scripts\build-windows.ps1

# macOS
./scripts/build-macos.sh

# Linux
./scripts/build-linux.sh
```

Or use GitHub Actions for automatic builds:

```bash
git tag v1.0.0
git push --tags
```

### 🤝 Contributing

We welcome all contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- [Tauri](https://tauri.app/) - Cross-platform desktop framework
- [Vue.js](https://vuejs.org/) - Progressive JavaScript framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [SQLite-vec](https://github.com/asg017/sqlite-vec) - SQLite vector extension

---

## 中文

### 🎯 产品概述

Nexus 是一个**100%本地处理**的AI指挥中心，统一调度所有AI模型，自动执行本地任务。让数据不出本地，真正为你工作。

### ✨ 核心特性

#### 🔒 隐私安全

- **100%本地处理** - 数据不上传云端
- **AES-256加密** - 敏感数据加密存储
- **离线可用** - 核心功能无需网络连接

#### 🤖 统一AI模型接入

- **多模型支持** - 无缝切换 Ollama、OpenAI、DeepSeek 等
- **一键切换** - 快速在不同模型间切换
- **状态监控** - 实时检测模型可用性

#### 📚 本地知识库

- **文档上传** - 支持 PDF、Markdown、TXT、DOCX、HTML 格式
- **智能分块** - 自适应文本分块算法（段落/语义/混合）
- **向量检索** - 混合检索策略（关键词+向量）

#### ⚡ 本地动作执行

- **安全沙箱** - 所有命令执行前需用户确认
- **预定义动作** - 整理文件、创建笔记、系统信息查询
- **脚本支持** - 自定义 Python 脚本扩展，安全执行

#### 🧠 三层记忆架构

- **瞬时记忆** - 滑动窗口上下文管理（100K tokens）
- **工作记忆** - 知识图谱 + 向量存储，分钟级更新
- **长期记忆** - 跨会话记忆检索，重要性评分

### 🛠️ 技术栈

| 模块       | 技术                                                                                | 说明                   |
| ---------- | ----------------------------------------------------------------------------------- | ---------------------- |
| 桌面框架   | [Tauri v2](https://tauri.app/)                                                      | Rust 后端，轻量安全    |
| 前端 UI    | [Vue 3](https://vuejs.org/) + TypeScript + [Tailwind CSS](https://tailwindcss.com/) | 组件化开发             |
| 后端逻辑   | [Python](https://python.org/) + [FastAPI](https://fastapi.tiangolo.com/)            | AI 生态丰富            |
| 向量数据库 | [SQLite-vec](https://github.com/asg017/sqlite-vec)                                  | 单文件，无需部署服务器 |
| 模型调用   | [LiteLLM](https://github.com/BerriAI/litellm)                                       | 统一 AI 接口           |

### 📦 安装

#### 前置要求

- [Node.js](https://nodejs.org/) 18+
- [Python](https://python.org/) 3.11+
- [Rust](https://www.rust-lang.org/) 1.70+
- [Ollama](https://ollama.ai/)（可选，用于本地模型）

#### 快速开始

```bash
# 克隆仓库
git clone https://github.com/1822520752/Nexus.git
cd Nexus

# 安装前端依赖
npm install

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动开发服务器
cd ..
npm run tauri dev
```

### 🚀 使用指南

#### 1. 配置 AI 模型

启动应用后，点击左侧**「模型管理」**：

**Ollama（本地模型）**

```bash
# 安装 Ollama
# Windows: 从 https://ollama.ai/download 下载
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llama2
ollama pull mistral

# Nexus 会自动检测本地 Ollama 服务 (http://localhost:11434)
```

**OpenAI / DeepSeek**

- 点击**「添加模型」**
- 选择提供商（OpenAI/DeepSeek）
- 输入 API Key
- 保存配置

#### 2. 上传知识库文档

- 点击左侧**「文档管理」**
- 拖拽上传 PDF、Markdown 或 TXT 文件
- 等待文档处理完成
- 在对话中引用文档内容

#### 3. 使用动作执行

- 点击左侧**「动作面板」**
- 选择预定义动作或自定义脚本
- 查看并确认执行权限
- 查看执行结果

### ⌨️ 快捷键

| 快捷键         | 功能     |
| -------------- | -------- |
| `Ctrl + Enter` | 发送消息 |
| `Ctrl + L`     | 清空对话 |
| `Ctrl + N`     | 新建对话 |
| `Ctrl + S`     | 保存设置 |
| `Ctrl + ,`     | 打开设置 |

### 🔧 配置

#### 环境变量 (`.env`)

```env
# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/nexus.db

# 向量维度（OpenAI embedding）
VECTOR_DIMENSION=1536

# 日志级别
LOG_LEVEL=INFO
```

### 🧪 测试

```bash
# 运行后端测试
cd backend
pytest

# 带覆盖率报告
pytest --cov=app tests/

# 运行前端测试
npm run test
```

### 📦 构建发布

```bash
# Windows
.\scripts\build-windows.ps1

# macOS
./scripts/build-macos.sh

# Linux
./scripts/build-linux.sh
```

或使用 GitHub Actions 自动构建：

```bash
git tag v1.0.0
git push --tags
```

### 🤝 贡献

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

### 🙏 致谢

- [Tauri](https://tauri.app/) - 跨平台桌面应用框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Ollama](https://ollama.ai/) - 本地大模型运行工具
- [SQLite-vec](https://github.com/asg017/sqlite-vec) - SQLite 向量扩展

---

<div align="center">

**[⬆ Back to Top](#nexus)**

Made with ❤️ by [Nexus Team](https://github.com/1822520752)

</div>
