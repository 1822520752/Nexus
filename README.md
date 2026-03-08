<div align="center">

# Nexus

### 您的本地AI智能中枢

**Your Local AI Command Center**

[![GitHub release](https://img.shields.io/github/v/release/1822520752/Nexus?include_prereleases&label=version)](https://github.com/1822520752/Nexus/releases)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/1822520752/Nexus/release.yml?label=build&logo=github)](https://github.com/1822520752/Nexus/actions)
[![GitHub Downloads](https://img.shields.io/github/downloads/1822520752/Nexus/total?label=downloads)](https://github.com/1822520752/Nexus/releases)
[![GitHub Stars](https://img.shields.io/github/stars/1822520752/Nexus?style=social)](https://github.com/1822520752/Nexus/stargazers)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tauri](https://img.shields.io/badge/Tauri-v2-24C8D8.svg)](https://tauri.app/)
[![Vue](https://img.shields.io/badge/Vue-3.4-4FC08D.svg)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg)](https://www.typescriptlang.org/)

[English](#english) | [中文](#中文)

</div>

---

## 中文

### 🎯 产品定位

Nexus 是一个**100%本地处理**的AI指挥中心，统一调度所有AI模型，自动执行本地任务。让数据不出本地，真正为你工作。

### ✨ 核心特性

#### 🔒 隐私安全

- **100%本地处理** - 数据不上传云端
- **AES-256加密** - 敏感数据加密存储
- **离线可用** - 核心功能无需网络连接

#### 🤖 统一AI模型接入

- **多模型支持** - Ollama、OpenAI、DeepSeek 等
- **一键切换** - 快速在不同模型间切换
- **状态监控** - 实时检测模型可用性

#### 📚 本地知识库

- **文档上传** - 支持 PDF、Markdown、TXT 等格式
- **智能分块** - 自适应文本分块算法
- **向量检索** - 混合检索策略（关键词+向量）

#### ⚡ 本地动作执行

- **安全沙箱** - 所有命令执行前需用户确认
- **预定义动作** - 整理文件、创建笔记等常用操作
- **脚本支持** - 自定义 Python 脚本扩展功能

#### 🧠 三层记忆架构

- **瞬时记忆** - 滑动窗口上下文管理（100K tokens）
- **工作记忆** - 知识图谱 + 向量存储
- **长期记忆** - 跨会话记忆检索

### 🛠️ 技术栈

| 模块       | 技术                          | 说明                |
| ---------- | ----------------------------- | ------------------- |
| 桌面框架   | Tauri v2                      | Rust 后端，轻量高效 |
| 前端 UI    | Vue 3 + TypeScript + Tailwind | 组件化开发          |
| 后端逻辑   | Python (FastAPI)              | AI 生态丰富         |
| 向量数据库 | SQLite-vec                    | 单文件，无需部署    |
| 模型调用   | LiteLLM                       | 统一 AI 接口        |

### 📦 安装

#### 前置要求

- Node.js 18+
- Python 3.11+
- Rust 1.70+
- pnpm 或 npm

#### 从源码构建

```bash
# 克隆仓库
git clone https://github.com/your-username/nexus.git
cd nexus

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

### 🚀 快速开始

#### 1. 配置 AI 模型

启动应用后，点击左侧「模型管理」添加模型：

**Ollama（本地模型）**

```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llama2

# Nexus 会自动检测本地 Ollama 服务
```

**OpenAI / DeepSeek**

- 点击「添加模型」
- 选择提供商
- 输入 API Key
- 保存配置

#### 2. 上传知识库文档

- 点击左侧「文档管理」
- 拖拽上传 PDF、Markdown 或 TXT 文件
- 等待文档处理完成
- 在对话中引用文档内容

#### 3. 使用动作执行

- 点击左侧「动作面板」
- 选择预定义动作或自定义脚本
- 确认执行权限
- 查看执行结果

### 📖 功能详解

#### 统一AI模型接入层

```typescript
// 前端调用示例
import { useModelsStore } from "@/stores/models";

const modelsStore = useModelsStore();

// 获取可用模型列表
await modelsStore.fetchModels();

// 切换当前模型
modelsStore.setCurrentModel(modelId);

// 发送消息
const response = await modelsStore.sendMessage({
  content: "你好，请介绍一下自己",
  conversationId: "xxx",
});
```

#### 本地知识库系统

```python
# 后端 API 调用示例
import httpx

# 上传文档
async with httpx.AsyncClient() as client:
    response = await client.post(
        'http://localhost:8000/api/v1/documents/upload',
        files={'file': open('document.pdf', 'rb')}
    )

# 搜索文档
response = await client.post(
    'http://localhost:8000/api/v1/search/hybrid',
    json={'query': '如何使用 Nexus？', 'top_k': 5}
)
```

#### 三层记忆架构

```python
# 记忆服务使用示例
from app.services.memory import MemoryService

memory_service = MemoryService()

# 添加消息到上下文
await memory_service.add_message_to_context(
    role='user',
    content='我喜欢使用 Python 编程'
)

# 检索相关记忆
memories = await memory_service.retrieve_relevant_memories(
    query='编程语言',
    top_k=5
)
```

### 🎨 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│  Nexus                              ─ □ ×  │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  🤖 模型选择  │   对话区域                                   │
│  ┌─────────┐ │   ┌────────────────────────────────────────┐ │
│  │ GPT-4   │ │   │ 用户: 你好，请介绍一下自己              │ │
│  └─────────┘ │   │                                        │ │
│              │   │ 助手: 我是 Nexus，您的本地AI智能中枢...  │ │
│  📁 文档管理  │   │                                        │ │
│  📝 动作面板  │   └────────────────────────────────────────┘ │
│  🧠 记忆管理  │                                              │
│  ⚙️ 设置     │   ┌────────────────────────────────────────┐ │
│              │   │ 输入消息...                    [发送]   │ │
│              │   └────────────────────────────────────────┘ │
├──────────────┴──────────────────────────────────────────────┤
│  状态: 已连接 Ollama (llama2) | 内存: 512MB | 版本 1.0.0    │
└─────────────────────────────────────────────────────────────┘
```

### ⌨️ 快捷键

| 快捷键         | 功能     |
| -------------- | -------- |
| `Ctrl + Enter` | 发送消息 |
| `Ctrl + L`     | 清空对话 |
| `Ctrl + N`     | 新建对话 |
| `Ctrl + S`     | 保存设置 |
| `Ctrl + ,`     | 打开设置 |

### 🔧 配置文件

#### 环境变量 (`.env`)

```env
# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/nexus.db

# 向量维度
VECTOR_DIMENSION=1536

# 加密密钥（自动生成）
ENCRYPTION_KEY=your-encryption-key

# 日志级别
LOG_LEVEL=INFO
```

#### Tauri 配置 (`src-tauri/tauri.conf.json`)

```json
{
  "productName": "Nexus",
  "version": "1.0.0",
  "identifier": "com.nexus.app",
  "build": {
    "devUrl": "http://localhost:1420",
    "frontendDist": "../dist"
  }
}
```

### 🧪 测试

```bash
# 运行后端测试
cd backend
pytest

# 运行前端测试
npm run test

# 生成测试覆盖率报告
pytest --cov=app tests/
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

### 🤝 贡献指南

我们欢迎所有形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

请查看 [贡献指南](CONTRIBUTING.md) 了解更多详情。

### 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

### 🙏 致谢

- [Tauri](https://tauri.app/) - 跨平台桌面应用框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [Ollama](https://ollama.ai/) - 本地大模型运行工具
- [SQLite-vec](https://github.com/asg017/sqlite-vec) - SQLite 向量扩展

---

## English

### 🎯 Product Positioning

Nexus is a **100% local processing** AI command center that unifies all AI models and automatically executes local tasks. Keep your data local and make AI work for you.

### ✨ Core Features

#### 🔒 Privacy & Security

- **100% Local Processing** - Data never leaves your device
- **AES-256 Encryption** - Sensitive data encrypted at rest
- **Offline Capable** - Core features work without internet

#### 🤖 Unified AI Model Access

- **Multi-model Support** - Ollama, OpenAI, DeepSeek, and more
- **One-click Switching** - Quickly switch between models
- **Status Monitoring** - Real-time model availability detection

#### 📚 Local Knowledge Base

- **Document Upload** - Support for PDF, Markdown, TXT formats
- **Smart Chunking** - Adaptive text chunking algorithm
- **Vector Retrieval** - Hybrid search (keyword + vector)

#### ⚡ Local Action Execution

- **Secure Sandbox** - All commands require user confirmation
- **Predefined Actions** - File organization, note creation, etc.
- **Script Support** - Custom Python script extensions

#### 🧠 Three-Layer Memory Architecture

- **Instant Memory** - Sliding window context (100K tokens)
- **Working Memory** - Knowledge graph + vector storage
- **Long-term Memory** - Cross-session memory retrieval

### 🛠️ Tech Stack

| Module            | Technology                    | Description                       |
| ----------------- | ----------------------------- | --------------------------------- |
| Desktop Framework | Tauri v2                      | Rust backend, lightweight         |
| Frontend UI       | Vue 3 + TypeScript + Tailwind | Component-based development       |
| Backend Logic     | Python (FastAPI)              | Rich AI ecosystem                 |
| Vector Database   | SQLite-vec                    | Single file, no deployment needed |
| Model Integration | LiteLLM                       | Unified AI interface              |

### 📦 Installation

#### Prerequisites

- Node.js 18+
- Python 3.11+
- Rust 1.70+
- pnpm or npm

#### Build from Source

```bash
# Clone repository
git clone https://github.com/your-username/nexus.git
cd nexus

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

### 🚀 Quick Start

#### 1. Configure AI Models

After launching, click "Model Management" on the left sidebar:

**Ollama (Local Models)**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama2

# Nexus auto-detects local Ollama service
```

**OpenAI / DeepSeek**

- Click "Add Model"
- Select provider
- Enter API Key
- Save configuration

#### 2. Upload Knowledge Base Documents

- Click "Document Management" on the left
- Drag and drop PDF, Markdown, or TXT files
- Wait for processing to complete
- Reference document content in conversations

#### 3. Use Action Execution

- Click "Action Panel" on the left
- Select predefined actions or custom scripts
- Confirm execution permissions
- View execution results

### ⌨️ Keyboard Shortcuts

| Shortcut       | Function           |
| -------------- | ------------------ |
| `Ctrl + Enter` | Send message       |
| `Ctrl + L`     | Clear conversation |
| `Ctrl + N`     | New conversation   |
| `Ctrl + S`     | Save settings      |
| `Ctrl + ,`     | Open settings      |

### 🧪 Testing

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
npm run test

# Generate coverage report
pytest --cov=app tests/
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

We welcome all forms of contribution!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Create Pull Request

See [Contributing Guide](CONTRIBUTING.md) for more details.

### 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

### 🙏 Acknowledgments

- [Tauri](https://tauri.app/) - Cross-platform desktop framework
- [Vue.js](https://vuejs.org/) - Progressive JavaScript framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [SQLite-vec](https://github.com/asg017/sqlite-vec) - SQLite vector extension

---

<div align="center">

**[⬆ Back to Top](#nexus)**

Made with ❤️ by Nexus Team

</div>
