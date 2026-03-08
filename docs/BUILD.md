# Nexus 构建指南

本文档介绍如何从源码构建 Nexus 应用程序。

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [平台特定说明](#平台特定说明)
- [构建脚本](#构建脚本)
- [GitHub Actions 自动构建](#github-actions-自动构建)
- [代码签名](#代码签名)
- [故障排除](#故障排除)

---

## 环境要求

### 通用依赖

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | >= 20.0.0 | JavaScript 运行时 |
| npm | >= 10.0.0 | Node.js 包管理器 |
| Rust | >= 1.75.0 | 系统编程语言 |
| Cargo | 最新版 | Rust 包管理器 |

### 平台特定依赖

#### Windows

- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (C++ 工作负载)
- [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (Windows 10/11 已内置)

#### macOS

- Xcode Command Line Tools: `xcode-select --install`
- macOS 10.13 或更高版本

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
  libgtk-3-dev \
  libwebkit2gtk-4.1-dev \
  libappindicator3-dev \
  librsvg2-dev \
  patchelf \
  libasound2-dev
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/nexus-app/nexus.git
cd nexus
```

### 2. 安装依赖

```bash
# 安装前端依赖
npm install

# Rust 依赖会在构建时自动安装
```

### 3. 开发模式

```bash
npm run tauri dev
```

### 4. 构建发布版本

```bash
npm run tauri build
```

---

## 平台特定说明

### Windows 构建

#### 使用构建脚本

```powershell
# 在项目根目录执行
.\scripts\build-windows.ps1
```

#### 构建脚本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-Configuration` | 构建配置 | Release |
| `-Target` | Rust 目标 | x86_64-pc-windows-msvc |
| `-SkipFrontend` | 跳过前端构建 | false |
| `-Clean` | 清理后重新构建 | false |
| `-OutputPath` | 输出目录 | .\release |

#### 示例

```powershell
# 清理构建
.\scripts\build-windows.ps1 -Clean

# 指定输出目录
.\scripts\build-windows.ps1 -OutputPath .\dist

# 跳过前端构建 (仅构建 Tauri)
.\scripts\build-windows.ps1 -SkipFrontend
```

#### 输出文件

构建完成后，在 `release` 目录下会生成：

- `Nexus_{version}_x64-setup.exe` - NSIS 安装程序
- `Nexus_{version}_x64.msi` - MSI 安装包

---

### macOS 构建

#### 使用构建脚本

```bash
# 添加执行权限
chmod +x scripts/build-macos.sh

# 执行构建
./scripts/build-macos.sh
```

#### 构建脚本参数

| 参数 | 说明 |
|------|------|
| `-h, --help` | 显示帮助信息 |
| `-c, --clean` | 清理后重新构建 |
| `-s, --skip-frontend` | 跳过前端构建 |
| `-t, --target` | 指定目标架构 |
| `-o, --output` | 指定输出目录 |

#### 示例

```bash
# 构建所有架构 (Intel + Apple Silicon)
./scripts/build-macos.sh

# 仅构建 Apple Silicon 版本
./scripts/build-macos.sh -t aarch64-apple-darwin

# 仅构建 Intel 版本
./scripts/build-macos.sh -t x86_64-apple-darwin

# 清理构建
./scripts/build-macos.sh -c
```

#### 输出文件

- `Nexus_{version}_x64.dmg` - Intel Mac DMG
- `Nexus_{version}_aarch64.dmg` - Apple Silicon DMG
- `Nexus_{version}_*.app.tar.gz` - 应用程序压缩包

---

### Linux 构建

#### 使用构建脚本

```bash
# 添加执行权限
chmod +x scripts/build-linux.sh

# 执行构建
./scripts/build-linux.sh
```

#### 构建脚本参数

| 参数 | 说明 |
|------|------|
| `-h, --help` | 显示帮助信息 |
| `-c, --clean` | 清理后重新构建 |
| `-s, --skip-frontend` | 跳过前端构建 |
| `-o, --output` | 指定输出目录 |

#### 示例

```bash
# 标准构建
./scripts/build-linux.sh

# 清理构建并指定输出目录
./scripts/build-linux.sh -c -o ./dist
```

#### 输出文件

- `Nexus_{version}_amd64.deb` - Debian/Ubuntu 包
- `Nexus_{version}_x64.AppImage` - AppImage 便携版

---

## 构建脚本

项目提供了三个平台的构建脚本：

| 脚本 | 平台 | 路径 |
|------|------|------|
| `build-windows.ps1` | Windows | `scripts/` |
| `build-macos.sh` | macOS | `scripts/` |
| `build-linux.sh` | Linux | `scripts/` |

### 脚本功能

所有构建脚本都包含以下功能：

1. **环境检查** - 验证必要的工具和依赖
2. **依赖安装** - 自动安装缺失的依赖
3. **前端构建** - 编译 Vue.js 应用
4. **Tauri 构建** - 编译 Rust 后端并打包
5. **产物整理** - 复制并重命名构建产物
6. **构建报告** - 生成构建摘要

---

## GitHub Actions 自动构建

项目配置了 GitHub Actions 自动化构建流程。

### CI 工作流 (ci.yml)

触发条件：
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 或 `develop` 分支

执行内容：
- 前端代码检查 (ESLint, Prettier)
- 前端类型检查 (TypeScript)
- 后端代码检查 (Ruff)
- 后端类型检查 (MyPy)
- Rust 代码检查 (rustfmt, clippy)
- 多平台构建测试

### Release 工作流 (release.yml)

触发条件：
- 推送版本标签 (如 `v1.0.0`)
- 手动触发 (workflow_dispatch)

执行内容：
- 构建 Windows 安装包 (MSI, NSIS)
- 构建 macOS 安装包 (DMG - Intel & Apple Silicon)
- 构建 Linux 安装包 (DEB, AppImage)
- 创建 GitHub Release Draft

### 手动触发发布

1. 进入 GitHub Actions 页面
2. 选择 "Release" 工作流
3. 点击 "Run workflow"
4. 输入版本号 (如 `v1.0.0`)
5. 点击 "Run workflow"

---

## 代码签名

### Windows 代码签名

1. 获取代码签名证书
2. 在 `tauri.conf.json` 中配置：

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_CERTIFICATE_THUMBPRINT",
      "digestAlgorithm": "sha256",
      "timestampUrl": "http://timestamp.digicert.com"
    }
  }
}
```

3. 在 GitHub Secrets 中配置：
   - `TAURI_PRIVATE_KEY` - Tauri 签名私钥
   - `TAURI_KEY_PASSWORD` - 私钥密码

### macOS 代码签名

1. 获取 Apple Developer 证书
2. 在 GitHub Secrets 中配置：
   - `APPLE_CERTIFICATE` - Base64 编码的证书
   - `APPLE_CERTIFICATE_PASSWORD` - 证书密码
   - `APPLE_SIGNING_IDENTITY` - 签名身份
   - `APPLE_ID` - Apple ID
   - `APPLE_PASSWORD` - App-specific password
   - `APPLE_TEAM_ID` - Team ID

---

## 故障排除

### 常见问题

#### 1. Rust 编译错误

**问题**: Rust 编译失败，提示找不到某些库

**解决方案**:
```bash
# 更新 Rust 工具链
rustup update stable

# 清理并重新构建
cargo clean
cargo build
```

#### 2. 前端构建错误

**问题**: npm 构建失败

**解决方案**:
```bash
# 清理 node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install

# 清理构建缓存
npm run build -- --force
```

#### 3. Linux 依赖缺失

**问题**: 构建时提示找不到 GTK 或 WebKit 库

**解决方案**:
```bash
# 安装所有必需依赖
sudo apt install -y \
  libgtk-3-dev \
  libwebkit2gtk-4.1-dev \
  libappindicator3-dev \
  librsvg2-dev \
  patchelf
```

#### 4. macOS 签名失败

**问题**: 代码签名失败

**解决方案**:
- 确保证书已正确导入到 Keychain
- 检查签名身份是否正确
- 确认 Apple ID 和密码配置正确

#### 5. Windows WebView2 问题

**问题**: 应用启动时提示 WebView2 未安装

**解决方案**:
- Windows 10/11 通常已内置 WebView2
- 如需手动安装，下载 [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

### 获取帮助

如果遇到其他问题：

1. 查看 [GitHub Issues](https://github.com/nexus-app/nexus/issues)
2. 提交新的 Issue 并附上：
   - 操作系统和版本
   - Node.js、Rust 版本
   - 完整的错误日志
   - 复现步骤

---

## 附录

### 项目结构

```
nexus/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml           # CI 工作流
│   │   └── release.yml      # 发布工作流
│   ├── dependabot.yml       # 依赖更新配置
│   └── ISSUE_TEMPLATE/      # Issue 模板
├── scripts/
│   ├── build-windows.ps1    # Windows 构建脚本
│   ├── build-macos.sh       # macOS 构建脚本
│   └── build-linux.sh       # Linux 构建脚本
├── src/                     # 前端源码
├── src-tauri/               # Tauri/Rust 源码
│   ├── src/
│   ├── Cargo.toml
│   └── tauri.conf.json      # Tauri 配置
├── backend/                 # Python 后端
├── package.json
└── docs/
    └── BUILD.md             # 本文档
```

### 相关链接

- [Tauri 官方文档](https://tauri.app/v2/guides/)
- [Vue.js 文档](https://vuejs.org/)
- [Rust 学习资源](https://www.rust-lang.org/learn)
