<div align="center">
  <img src="public/nexus.svg" alt="Nexus Logo" width="120" height="120" />
  
  <h1>Nexus</h1>
  
  <h3>Your Local AI Command Center</h3>
  <p><em>您的本地AI智能中枢</em></p>
  
  <p>
    <strong>100% Local Processing</strong> • 
    <strong>Privacy First</strong> • 
    <strong>Multi-Model Support</strong>
  </p>
  
  <p>
    <a href="https://github.com/1822520752/Nexus/releases">
      <img src="https://img.shields.io/github/v/release/1822520752/Nexus?include_prereleases&label=version&style=flat-square" alt="Version" />
    </a>
    <a href="https://github.com/1822520752/Nexus/actions/workflows/release.yml">
      <img src="https://img.shields.io/github/actions/workflow/status/1822520752/Nexus/release.yml?label=build&logo=github&style=flat-square" alt="Build Status" />
    </a>
    <a href="https://github.com/1822520752/Nexus/releases">
      <img src="https://img.shields.io/github/downloads/1822520752/Nexus/total?label=downloads&style=flat-square" alt="Downloads" />
    </a>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" />
    </a>
  </p>
  
  <p>
    <a href="https://tauri.app/">
      <img src="https://img.shields.io/badge/Tauri-v2-24C8D8?style=flat-square&logo=tauri&logoColor=white" alt="Tauri" />
    </a>
    <a href="https://vuejs.org/">
      <img src="https://img.shields.io/badge/Vue-3.4-4FC08D?style=flat-square&logo=vue.js&logoColor=white" alt="Vue" />
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
    </a>
    <a href="https://www.typescriptlang.org/">
      <img src="https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
    </a>
  </p>
  
  <p>
    <a href="#english">English</a> • 
    <a href="#中文">中文</a>
  </p>
  
  <a href="https://github.com/1822520752/Nexus">
    <img src="https://star-history.com/#1822520752/Nexus&Date" alt="Star History" width="600" />
  </a>
</div>

---

## English

### Why Nexus?

<table>
<tr>
<td width="50%">

**Privacy Anxiety?** No more. Your data stays on your device. Period.

**Tool Fragmentation?** One app for all AI models - Ollama, OpenAI, DeepSeek, and more.

**Context Lost?** Three-layer memory architecture keeps conversations flowing.

**Weak Action?** AI can actually execute local tasks safely.

</td>
<td width="50%" align="center">

```
┌─────────────────────────────────┐
│     ╔═══════════════════╗       │
│     ║                   ║       │
│     ║    🏠 NEXUS       ║       │
│     ║                   ║       │
│     ╚═══════════════════╝       │
│                                 │
│  ┌─────────┐  ┌─────────────┐   │
│  │ Models  │  │   Chat      │   │
│  ├─────────┤  ├─────────────┤   │
│  │ Docs    │  │   Area      │   │
│  ├─────────┤  │             │   │
│  │ Actions │  │             │   │
│  ├─────────┤  │             │   │
│  │ Memory  │  └─────────────┘   │
│  └─────────┘                    │
│                                 │
└─────────────────────────────────┘
```

</td>
</tr>
</table>

### ✨ Features

<table>
<tr>
<th width="25%">🔒 Privacy & Security</th>
<th width="25%">🤖 Multi-Model AI</th>
<th width="25%">📚 Local Knowledge Base</th>
<th width="25%">⚡ Action Engine</th>
</tr>
<tr>
<td>

- 100% Local Processing
- AES-256 Encryption
- Offline Capable
- No Cloud Required

</td>
<td>

- Ollama (Local)
- OpenAI GPT-4
- DeepSeek
- One-Click Switch

</td>
<td>

- PDF, MD, TXT Support
- Smart Chunking
- Vector Search
- Hybrid Retrieval

</td>
<td>

- Secure Sandbox
- File Operations
- Custom Scripts
- User Confirmation

</td>
</tr>
</table>

### 🧠 Three-Layer Memory

```
┌──────────────────────────────────────────────────────────────┐
│                      MEMORY ARCHITECTURE                      │
├────────────────┬─────────────────┬───────────────────────────┤
│  ⚡ INSTANT    │  💼 WORKING     │  📚 LONG-TERM             │
│                │                 │                           │
│  100K tokens   │  Knowledge      │  Cross-session            │
│  sliding       │  Graph +        │  retrieval with           │
│  window        │  Vector Store   │  importance scoring       │
│                │                 │                           │
│  Real-time     │  Minute-level   │  Persistent               │
│  context       │  updates        │  storage                  │
└────────────────┴─────────────────┴───────────────────────────┘
```

### 🚀 Quick Start

```bash
# 1️⃣ Clone
git clone https://github.com/1822520752/Nexus.git
cd Nexus

# 2️⃣ Install
npm install
cd backend && pip install -r requirements.txt && cd ..

# 3️⃣ Initialize
python backend/scripts/init_db.py

# 4️⃣ Run
npm run tauri dev
```

<details>
<summary><b>📦 Prerequisites</b></summary>

| Requirement | Version | Download                                    |
| ----------- | ------- | ------------------------------------------- |
| Node.js     | 18+     | [nodejs.org](https://nodejs.org/)           |
| Python      | 3.11+   | [python.org](https://python.org/)           |
| Rust        | 1.70+   | [rust-lang.org](https://www.rust-lang.org/) |
| Ollama      | Latest  | [ollama.ai](https://ollama.ai/) (optional)  |

</details>

### 🎯 Usage

<details open>
<summary><b>1. Configure AI Models</b></summary>

**Ollama (Local Models)**

```bash
# Install Ollama → https://ollama.ai/download

# Download models
ollama pull llama2
ollama pull mistral
ollama pull codellama

# Nexus auto-detects at http://localhost:11434
```

**Cloud Models (OpenAI / DeepSeek)**

```
Settings → Models → Add Model → Enter API Key → Save
```

</details>

<details>
<summary><b>2. Knowledge Base</b></summary>

```
Drag & Drop → PDF/MD/TXT → Auto Process → Chat with Docs
```

Features:

- Adaptive text chunking (paragraph/semantic/hybrid)
- Vector embeddings with SQLite-vec
- Hybrid search (keyword + vector)
- Document management UI

</details>

<details>
<summary><b>3. Action Execution</b></summary>

| Action          | Description                    |
| --------------- | ------------------------------ |
| File Operations | Organize, move, rename, delete |
| Note Creation   | Create & manage markdown notes |
| System Info     | Get disk, memory, CPU info     |
| Custom Scripts  | Execute Python scripts safely  |

All actions require **user confirmation** before execution.

</details>

### ⌨️ Shortcuts

|      Key       | Action             |
| :------------: | ------------------ |
| `Ctrl + Enter` | Send message       |
|   `Ctrl + L`   | Clear conversation |
|   `Ctrl + N`   | New conversation   |
|   `Ctrl + S`   | Save settings      |
|   `Ctrl + ,`   | Open settings      |

### 📦 Build

```bash
# Windows
.\scripts\build-windows.ps1

# macOS
./scripts/build-macos.sh

# Linux
./scripts/build-linux.sh
```

Or auto-build via GitHub Actions:

```bash
git tag v1.0.0 && git push --tags
```

### 🤝 Contributing

We welcome contributions! See [Contributing Guide](CONTRIBUTING.md).

```bash
# Fork → Branch → Commit → Push → PR
git checkout -b feature/amazing-feature
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

---

## 中文

### 为什么选择 Nexus？

<table>
<tr>
<td width="50%">

**隐私焦虑？** 数据留在本地，绝不上传云端。

**工具碎片化？** 一个应用搞定所有 AI 模型。

**上下文丢失？** 三层记忆架构，对话连贯流畅。

**行动力弱？** AI 可以安全执行本地任务。

</td>
<td width="50%" align="center">

```
┌─────────────────────────────────┐
│     ╔═══════════════════╗       │
│     ║                   ║       │
│     ║    🏠 NEXUS       ║       │
│     ║                   ║       │
│     ╚═══════════════════╝       │
│                                 │
│  ┌─────────┐  ┌─────────────┐   │
│  │ 模型    │  │   对话      │   │
│  ├─────────┤  ├─────────────┤   │
│  │ 文档    │  │   区域      │   │
│  ├─────────┤  │             │   │
│  │ 动作    │  │             │   │
│  ├─────────┤  │             │   │
│  │ 记忆    │  └─────────────┘   │
│  └─────────┘                    │
│                                 │
└─────────────────────────────────┘
```

</td>
</tr>
</table>

### ✨ 核心功能

<table>
<tr>
<th width="25%">🔒 隐私安全</th>
<th width="25%">🤖 多模型 AI</th>
<th width="25%">📚 本地知识库</th>
<th width="25%">⚡ 动作引擎</th>
</tr>
<tr>
<td>

- 100% 本地处理
- AES-256 加密
- 离线可用
- 无需云端

</td>
<td>

- Ollama 本地
- OpenAI GPT-4
- DeepSeek
- 一键切换

</td>
<td>

- PDF/MD/TXT 支持
- 智能分块
- 向量搜索
- 混合检索

</td>
<td>

- 安全沙箱
- 文件操作
- 自定义脚本
- 用户确认

</td>
</tr>
</table>

### 🧠 三层记忆架构

```
┌──────────────────────────────────────────────────────────────┐
│                        记忆架构                               │
├────────────────┬─────────────────┬───────────────────────────┤
│  ⚡ 瞬时记忆   │  💼 工作记忆    │  📚 长期记忆              │
│                │                 │                           │
│  100K tokens   │  知识图谱 +     │  跨会话检索               │
│  滑动窗口      │  向量存储       │  重要性评分               │
│                │                 │                           │
│  实时上下文    │  分钟级更新     │  持久化存储               │
└────────────────┴─────────────────┴───────────────────────────┘
```

### 🚀 快速开始

```bash
# 1️⃣ 克隆
git clone https://github.com/1822520752/Nexus.git
cd Nexus

# 2️⃣ 安装
npm install
cd backend && pip install -r requirements.txt && cd ..

# 3️⃣ 初始化
python backend/scripts/init_db.py

# 4️⃣ 运行
npm run tauri dev
```

<details>
<summary><b>📦 前置要求</b></summary>

| 要求    | 版本   | 下载                                        |
| ------- | ------ | ------------------------------------------- |
| Node.js | 18+    | [nodejs.org](https://nodejs.org/)           |
| Python  | 3.11+  | [python.org](https://python.org/)           |
| Rust    | 1.70+  | [rust-lang.org](https://www.rust-lang.org/) |
| Ollama  | 最新版 | [ollama.ai](https://ollama.ai/)（可选）     |

</details>

### ⌨️ 快捷键

|      按键      | 功能     |
| :------------: | -------- |
| `Ctrl + Enter` | 发送消息 |
|   `Ctrl + L`   | 清空对话 |
|   `Ctrl + N`   | 新建对话 |
|   `Ctrl + S`   | 保存设置 |
|   `Ctrl + ,`   | 打开设置 |

### 🤝 贡献

欢迎参与贡献！查看 [贡献指南](CONTRIBUTING.md)。

---

<div align="center">

### 🙏 Acknowledgments

[![Tauri](https://img.shields.io/badge/Tauri-24C8D8?style=flat-square&logo=tauri&logoColor=white)](https://tauri.app/)
[![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white)](https://ollama.ai/)

---

**[⬆ Back to Top](#nexus)**

Made with ❤️ by [Nexus Team](https://github.com/1822520752)

</div>
