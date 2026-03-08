/// <reference types="vite/client" />

/**
 * 环境变量类型声明
 */
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
  readonly TAURI_PLATFORM: string
  readonly TAURI_DEBUG: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

/**
 * Vue 单文件组件类型声明
 */
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
