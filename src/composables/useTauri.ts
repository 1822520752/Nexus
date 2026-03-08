/**
 * Tauri API 组合式函数
 * 封装 Tauri 命令调用
 */
import { invoke } from '@tauri-apps/api/core'
import { ref } from 'vue'

/**
 * 使用 Tauri 命令的组合式函数
 */
export function useTauri() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  /**
   * 调用 Tauri 命令
   * @param command - 命令名称
   * @param args - 命令参数
   */
  const callCommand = async <T>(command: string, args?: Record<string, unknown>): Promise<T | null> => {
    isLoading.value = true
    error.value = null

    try {
      const result = await invoke<T>(command, args)
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      console.error(`Tauri 命令 ${command} 执行失败: - useTauri.ts:29`, e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 问候命令（测试用）
   * @param name - 名称
   */
  const greet = async (name: string): Promise<string | null> => {
    return callCommand<string>('greet', { name })
  }

  /**
   * 获取应用信息
   */
  const getAppInfo = async (): Promise<string | null> => {
    return callCommand<string>('get_app_info')
  }

  return {
    isLoading,
    error,
    callCommand,
    greet,
    getAppInfo,
  }
}
