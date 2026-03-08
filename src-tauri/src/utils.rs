//! # 应用程序工具函数模块
//!
//! 提供常用的工具函数

use std::path::PathBuf;

/// 获取应用程序数据目录
///
/// # 返回
/// 应用程序数据目录路径
pub fn get_app_data_dir() -> Option<PathBuf> {
    dirs::data_local_dir().map(|p| p.join("Nexus"))
}

/// 获取应用程序配置目录
///
/// # 返回
/// 应用程序配置目录路径
pub fn get_app_config_dir() -> Option<PathBuf> {
    dirs::config_dir().map(|p| p.join("Nexus"))
}

/// 获取应用程序日志目录
///
/// # 返回
/// 应用程序日志目录路径
pub fn get_app_log_dir() -> Option<PathBuf> {
    dirs::data_local_dir().map(|p| p.join("Nexus").join("logs"))
}

/// 确保目录存在
///
/// # 参数
/// * `path` - 目录路径
///
/// # 返回
/// 成功返回 true，失败返回 false
pub fn ensure_dir_exists(path: &PathBuf) -> bool {
    if !path.exists() {
        std::fs::create_dir_all(path).is_ok()
    } else {
        true
    }
}

/// 格式化文件大小
///
/// # 参数
/// * `bytes` - 字节数
///
/// # 返回
/// 格式化后的文件大小字符串
pub fn format_file_size(bytes: u64) -> String {
    const KB: u64 = 1024;
    const MB: u64 = KB * 1024;
    const GB: u64 = MB * 1024;

    if bytes >= GB {
        format!("{:.2} GB", bytes as f64 / GB as f64)
    } else if bytes >= MB {
        format!("{:.2} MB", bytes as f64 / MB as f64)
    } else if bytes >= KB {
        format!("{:.2} KB", bytes as f64 / KB as f64)
    } else {
        format!("{} B", bytes)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_file_size() {
        assert_eq!(format_file_size(500), "500 B");
        assert_eq!(format_file_size(1024), "1.00 KB");
        assert_eq!(format_file_size(1048576), "1.00 MB");
        assert_eq!(format_file_size(1073741824), "1.00 GB");
    }
}
