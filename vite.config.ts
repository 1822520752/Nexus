/**
 * Vite 构建配置文件
 * 配置 Vue3 插件、路径别名和构建选项
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  // 路径别名配置
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@views': resolve(__dirname, 'src/views'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@composables': resolve(__dirname, 'src/composables'),
      '@types': resolve(__dirname, 'src/types'),
      '@assets': resolve(__dirname, 'src/assets')
    }
  },

  // 开发服务器配置
  server: {
    port: 1420,
    strictPort: true,
    host: true
  },

  // Tauri 环境特殊配置
  clearScreen: false,

  // 构建配置
  build: {
    // Tauri 使用 Chromium 在 Windows 和 macOS 上，使用 WebKit 在 Linux 上
    target: process.env.TAURI_PLATFORM === 'windows' ? 'chrome105' : 'safari14',
    // 生产环境移除 console 和 debugger
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    // 生成 source map 用于调试
    sourcemap: !!process.env.TAURI_DEBUG
  },

  // 环境变量前缀
  envPrefix: ['VITE_', 'TAURI_']
})
