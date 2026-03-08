# ============================================================
# Nexus Windows 构建脚本
# 用于在 Windows 平台上构建安装包
# ============================================================

param(
    [string]$Configuration = "Release",
    [string]$Target = "x86_64-pc-windows-msvc",
    [switch]$SkipFrontend = $false,
    [switch]$SkipBackend = $false,
    [switch]$Clean = $false,
    [string]$OutputPath = ".\release"
)

# ============================================================
# 辅助函数
# ============================================================

/**
 * 输出带颜色的日志信息
 * @param string $Message - 日志消息
 * @param string $Level - 日志级别 (Info, Success, Warning, Error)
 */
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $prefix = switch ($Level) {
        "Success" { "[SUCCESS]" }
        "Warning" { "[WARNING]" }
        "Error"   { "[ERROR]" }
        default   { "[INFO]" }
    }
    
    $color = switch ($Level) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error"   { "Red" }
        default   { "White" }
    }
    
    Write-Host "[$timestamp] $prefix $Message" -ForegroundColor $color
}

/**
 * 检查命令是否存在
 * @param string $Command - 要检查的命令
 * @return bool - 命令是否存在
 */
function Test-Command {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

/**
 * 检查构建环境
 */
function Test-BuildEnvironment {
    Write-Log "检查构建环境..."
    
    $errors = @()
    
    # 检查 Node.js
    if (-not (Test-Command "node")) {
        $errors += "Node.js 未安装。请从 https://nodejs.org/ 安装 Node.js 20+"
    } else {
        $nodeVersion = node --version
        Write-Log "Node.js 版本: $nodeVersion" -Level "Success"
    }
    
    # 检查 npm
    if (-not (Test-Command "npm")) {
        $errors += "npm 未安装"
    } else {
        $npmVersion = npm --version
        Write-Log "npm 版本: $npmVersion" -Level "Success"
    }
    
    # 检查 Rust
    if (-not (Test-Command "rustc")) {
        $errors += "Rust 未安装。请从 https://rustup.rs/ 安装 Rust"
    } else {
        $rustVersion = rustc --version
        Write-Log "Rust 版本: $rustVersion" -Level "Success"
    }
    
    # 检查 Cargo
    if (-not (Test-Command "cargo")) {
        $errors += "Cargo 未安装"
    } else {
        $cargoVersion = cargo --version
        Write-Log "Cargo 版本: $cargoVersion" -Level "Success"
    }
    
    # 检查 Python (可选，用于后端)
    if (Test-Command "python") {
        $pythonVersion = python --version
        Write-Log "Python 版本: $pythonVersion" -Level "Success"
    } else {
        Write-Log "Python 未安装，将跳过后端构建" -Level "Warning"
    }
    
    if ($errors.Count -gt 0) {
        Write-Log "构建环境检查失败:" -Level "Error"
        $errors | ForEach-Object { Write-Log "  - $_" -Level "Error" }
        exit 1
    }
    
    Write-Log "构建环境检查通过" -Level "Success"
}

/**
 * 清理构建目录
 */
function Clear-BuildDirectory {
    Write-Log "清理构建目录..."
    
    $dirsToClean = @(
        ".\dist",
        ".\src-tauri\target\release",
        ".\src-tauri\target\debug"
    )
    
    foreach ($dir in $dirsToClean) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force
            Write-Log "已清理: $dir"
        }
    }
    
    Write-Log "清理完成" -Level "Success"
}

/**
 * 构建前端
 */
function Build-Frontend {
    Write-Log "开始构建前端..."
    
    # 安装依赖
    Write-Log "安装前端依赖..."
    npm ci
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "前端依赖安装失败" -Level "Error"
        exit 1
    }
    
    # 类型检查
    Write-Log "运行 TypeScript 类型检查..."
    npx vue-tsc --noEmit
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "TypeScript 类型检查失败" -Level "Error"
        exit 1
    }
    
    # 构建前端
    Write-Log "构建前端资源..."
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "前端构建失败" -Level "Error"
        exit 1
    }
    
    Write-Log "前端构建完成" -Level "Success"
}

/**
 * 构建 Tauri 应用
 */
function Build-Tauri {
    Write-Log "开始构建 Tauri 应用..."
    
    # 添加 Rust 目标
    Write-Log "检查 Rust 目标: $Target"
    rustup target add $Target
    
    # 构建 Tauri
    Write-Log "构建 Tauri 应用 (目标: $Target)..."
    cargo tauri build --target $Target
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Tauri 构建失败" -Level "Error"
        exit 1
    }
    
    Write-Log "Tauri 构建完成" -Level "Success"
}

/**
 * 复制构建产物
 */
function Copy-BuildArtifacts {
    Write-Log "复制构建产物..."
    
    # 创建输出目录
    if (-not (Test-Path $OutputPath)) {
        New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    }
    
    # 获取版本号
    $packageJson = Get-Content ".\package.json" | ConvertFrom-Json
    $version = $packageJson.version
    
    # 复制 MSI
    $msiFiles = Get-ChildItem -Path ".\src-tauri\target\$Target\release\bundle\msi\*.msi" -ErrorAction SilentlyContinue
    foreach ($file in $msiFiles) {
        $destName = "Nexus_${version}_x64.msi"
        Copy-Item $file.FullName -Destination (Join-Path $OutputPath $destName) -Force
        Write-Log "已复制: $destName"
    }
    
    # 复制 NSIS
    $nsisFiles = Get-ChildItem -Path ".\src-tauri\target\$Target\release\bundle\nsis\*.exe" -ErrorAction SilentlyContinue
    foreach ($file in $nsisFiles) {
        $destName = "Nexus_${version}_x64-setup.exe"
        Copy-Item $file.FullName -Destination (Join-Path $OutputPath $destName) -Force
        Write-Log "已复制: $destName"
    }
    
    Write-Log "构建产物已复制到: $OutputPath" -Level "Success"
}

/**
 * 生成构建报告
 */
function New-BuildReport {
    Write-Log "生成构建报告..."
    
    $packageJson = Get-Content ".\package.json" | ConvertFrom-Json
    $version = $packageJson.version
    
    $report = @"
========================================
Nexus Windows 构建报告
========================================

构建时间: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
版本号: $version
目标平台: $Target
配置: $Configuration

构建产物:
"@
    
    $artifacts = Get-ChildItem -Path $OutputPath -File
    foreach ($artifact in $artifacts) {
        $size = "{0:N2} MB" -f ($artifact.Length / 1MB)
        $report += "`n  - $($artifact.Name) ($size)"
    }
    
    $report += "`n`n========================================"
    
    Write-Host $report
    $report | Out-File -FilePath (Join-Path $OutputPath "build-report.txt") -Encoding UTF8
}

# ============================================================
# 主构建流程
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Nexus Windows 构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到项目根目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Log "项目根目录: $projectRoot"

# 检查构建环境
Test-BuildEnvironment

# 清理构建目录
if ($Clean) {
    Clear-BuildDirectory
}

# 构建前端
if (-not $SkipFrontend) {
    Build-Frontend
}

# 构建 Tauri
Build-Tauri

# 复制构建产物
Copy-BuildArtifacts

# 生成构建报告
New-BuildReport

Write-Host ""
Write-Log "构建完成!" -Level "Success"
Write-Host ""
