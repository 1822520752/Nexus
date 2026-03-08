//! # 应用程序配置模块
//!
//! 定义应用程序的全局配置常量和设置

/// 应用程序名称
pub const APP_NAME: &str = "Nexus";

/// 应用程序版本
pub const APP_VERSION: &str = "0.1.0";

/// 应用程序描述
pub const APP_DESCRIPTION: &str = "本地AI智能中枢";

/// 默认后端服务地址
pub const DEFAULT_BACKEND_URL: &str = "http://localhost:8000";

/// 默认后端服务端口
pub const DEFAULT_BACKEND_PORT: u16 = 8000;

/// 应用程序配置结构体
#[derive(Debug, Clone)]
pub struct AppConfig {
    /// 应用名称
    pub name: String,
    /// 应用版本
    pub version: String,
    /// 后端服务地址
    pub backend_url: String,
    /// 后端服务端口
    pub backend_port: u16,
}

impl Default for AppConfig {
    /// 创建默认配置
    fn default() -> Self {
        Self {
            name: APP_NAME.to_string(),
            version: APP_VERSION.to_string(),
            backend_url: DEFAULT_BACKEND_URL.to_string(),
            backend_port: DEFAULT_BACKEND_PORT,
        }
    }
}

impl AppConfig {
    /// 创建新的配置实例
    pub fn new() -> Self {
        Self::default()
    }
}
