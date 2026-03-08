//! # Nexus - 本地AI智能中枢
//!
//! Tauri 应用程序主入口文件
//! 负责初始化应用和处理系统命令

// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

/// 应用程序主入口函数
///
/// 初始化 Tauri 应用并运行主循环
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 获取主窗口
            let _window = app.get_webview_window("main").expect("无法获取主窗口");
            
            #[cfg(debug_assertions)]
            {
                // 开发模式下打开 DevTools
                _window.open_devtools();
            }
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // 在此处注册 Tauri 命令
            greet,
            get_app_info,
        ])
        .run(tauri::generate_context!())
        .expect("启动 Tauri 应用时出错");
}

/// 测试用的问候命令
///
/// # 参数
/// * `name` - 要问候的名称
///
/// # 返回
/// 问候字符串
#[tauri::command]
fn greet(name: &str) -> String {
    format!("你好, {}! 欢迎使用 Nexus!", name)
}

/// 获取应用程序信息
///
/// # 返回
/// 包含应用名称和版本的 JSON 字符串
#[tauri::command]
fn get_app_info() -> String {
    serde_json::json!({
        "name": "Nexus",
        "version": "0.1.0",
        "description": "本地AI智能中枢"
    })
    .to_string()
}
