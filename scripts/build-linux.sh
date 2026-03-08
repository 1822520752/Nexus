#!/bin/bash
# ============================================================
# Nexus Linux 构建脚本
# 用于在 Linux 平台上构建安装包
# ============================================================

set -e

# ============================================================
# 配置变量
# ============================================================
CONFIGURATION="Release"
TARGET="x86_64-unknown-linux-gnu"
SKIP_FRONTEND=false
CLEAN=false
OUTPUT_PATH="./release"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 辅助函数
# ============================================================

# 输出带颜色的日志信息
# @param string $message - 日志消息
# @param string $level - 日志级别 (info, success, warning, error)
log() {
    local message="$1"
    local level="${2:-info}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        success) echo -e "${GREEN}[$timestamp] [SUCCESS] $message${NC}" ;;
        warning) echo -e "${YELLOW}[$timestamp] [WARNING] $message${NC}" ;;
        error)   echo -e "${RED}[$timestamp] [ERROR] $message${NC}" ;;
        *)       echo -e "${BLUE}[$timestamp] [INFO] $message${NC}" ;;
    esac
}

# 检查命令是否存在
# @param string $command - 要检查的命令
# @return bool - 命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 显示帮助信息
show_help() {
    echo "Nexus Linux 构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help           显示帮助信息"
    echo "  -c, --clean          清理构建目录后重新构建"
    echo "  -s, --skip-frontend  跳过前端构建"
    echo "  -o, --output         指定输出目录 (默认: ./release)"
    echo ""
    echo "示例:"
    echo "  $0                  # 构建应用"
    echo "  $0 -c -o ./dist     # 清理构建并输出到 ./dist"
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--clean)
                CLEAN=true
                shift
                ;;
            -s|--skip-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
            -o|--output)
                OUTPUT_PATH="$2"
                shift 2
                ;;
            *)
                log "未知选项: $1" "error"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查构建环境
check_build_environment() {
    log "检查构建环境..."
    
    local errors=()
    
    # 检查 Node.js
    if ! command_exists node; then
        errors+=("Node.js 未安装。请安装 Node.js 20+")
    else
        log "Node.js 版本: $(node --version)" "success"
    fi
    
    # 检查 npm
    if ! command_exists npm; then
        errors+=("npm 未安装")
    else
        log "npm 版本: $(npm --version)" "success"
    fi
    
    # 检查 Rust
    if ! command_exists rustc; then
        errors+=("Rust 未安装。请从 https://rustup.rs/ 安装 Rust")
    else
        log "Rust 版本: $(rustc --version)" "success"
    fi
    
    # 检查 Cargo
    if ! command_exists cargo; then
        errors+=("Cargo 未安装")
    else
        log "Cargo 版本: $(cargo --version)" "success"
    fi
    
    # 检查系统依赖
    log "检查系统依赖..."
    local system_deps=(
        "libgtk-3-dev"
        "libwebkit2gtk-4.1-dev"
        "libappindicator3-dev"
        "librsvg2-dev"
        "patchelf"
    )
    
    local missing_deps=()
    for dep in "${system_deps[@]}"; do
        if ! dpkg -l | grep -q "$dep"; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log "缺少以下系统依赖:" "warning"
        for dep in "${missing_deps[@]}"; do
            log "  - $dep" "warning"
        done
        log "正在安装系统依赖..."
        sudo apt-get update
        sudo apt-get install -y "${missing_deps[@]}"
    fi
    
    if [ ${#errors[@]} -gt 0 ]; then
        log "构建环境检查失败:" "error"
        for error in "${errors[@]}"; do
            log "  - $error" "error"
        done
        exit 1
    fi
    
    log "构建环境检查通过" "success"
}

# 清理构建目录
clean_build_directory() {
    log "清理构建目录..."
    
    local dirs_to_clean=(
        "./dist"
        "./src-tauri/target/release"
        "./src-tauri/target/debug"
    )
    
    for dir in "${dirs_to_clean[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log "已清理: $dir"
        fi
    done
    
    log "清理完成" "success"
}

# 构建前端
build_frontend() {
    log "开始构建前端..."
    
    # 安装依赖
    log "安装前端依赖..."
    npm ci
    
    # 类型检查
    log "运行 TypeScript 类型检查..."
    npx vue-tsc --noEmit
    
    # 构建前端
    log "构建前端资源..."
    npm run build
    
    log "前端构建完成" "success"
}

# 构建 Tauri 应用
build_tauri() {
    log "开始构建 Tauri 应用..."
    
    # 添加 Rust 目标
    log "检查 Rust 目标: $TARGET"
    rustup target add "$TARGET"
    
    # 构建 Tauri
    log "构建 Tauri 应用..."
    cargo tauri build --target "$TARGET"
    
    log "Tauri 构建完成" "success"
}

# 复制构建产物
copy_build_artifacts() {
    log "复制构建产物..."
    
    # 创建输出目录
    mkdir -p "$OUTPUT_PATH"
    
    # 获取版本号
    local version=$(node -p "require('./package.json').version")
    
    # 复制 DEB
    local deb_files=$(find "./src-tauri/target/$TARGET/release/bundle/deb" -name "*.deb" 2>/dev/null || true)
    for file in $deb_files; do
        local dest_name="Nexus_${version}_amd64.deb"
        cp "$file" "$OUTPUT_PATH/$dest_name"
        log "已复制: $dest_name"
    done
    
    # 复制 AppImage
    local appimage_files=$(find "./src-tauri/target/$TARGET/release/bundle/appimage" -name "*.AppImage" 2>/dev/null || true)
    for file in $appimage_files; do
        local dest_name="Nexus_${version}_x64.AppImage"
        cp "$file" "$OUTPUT_PATH/$dest_name"
        log "已复制: $dest_name"
    done
    
    log "构建产物已复制到: $OUTPUT_PATH" "success"
}

# 生成构建报告
generate_build_report() {
    log "生成构建报告..."
    
    local version=$(node -p "require('./package.json').version")
    local build_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    local report="========================================
Nexus Linux 构建报告
========================================

构建时间: $build_time
版本号: $version
目标平台: $TARGET

构建产物:
"
    
    for file in "$OUTPUT_PATH"/*; do
        if [ -f "$file" ]; then
            local size=$(du -h "$file" | cut -f1)
            report+="  - $(basename "$file") ($size)
"
        fi
    done
    
    report+="
========================================"
    
    echo -e "$report"
    echo "$report" > "$OUTPUT_PATH/build-report.txt"
}

# ============================================================
# 主构建流程
# ============================================================

main() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Nexus Linux 构建脚本${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # 解析命令行参数
    parse_args "$@"
    
    # 切换到项目根目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    cd "$PROJECT_ROOT"
    
    log "项目根目录: $PROJECT_ROOT"
    
    # 检查构建环境
    check_build_environment
    
    # 清理构建目录
    if [ "$CLEAN" = true ]; then
        clean_build_directory
    fi
    
    # 构建前端
    if [ "$SKIP_FRONTEND" = false ]; then
        build_frontend
    fi
    
    # 构建 Tauri
    build_tauri
    
    # 复制构建产物
    copy_build_artifacts
    
    # 生成构建报告
    generate_build_report
    
    echo ""
    log "构建完成!" "success"
    echo ""
}

# 执行主函数
main "$@"
