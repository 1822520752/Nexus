/**
 * 应用设置状态管理 Store
 * 管理用户偏好设置和应用配置
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { AppSettings } from '@/types'

/**
 * 默认设置
 */
const defaultSettings: AppSettings = {
  theme: 'dark',
  language: 'zh-CN',
  defaultModel: '',
  autoSave: true,
  sendOnEnter: true,
  showTokenCount: true,
  backendUrl: 'http://localhost:8000'
}

/**
 * 本地存储键名
 */
const STORAGE_KEY = 'nexus-settings'

export const useSettingsStore = defineStore('settings', () => {
  // ==================== 状态 ====================

  /**
   * 应用设置
   */
  const settings = ref<AppSettings>(loadSettings())

  /**
   * 是否正在保存
   */
  const isSaving = ref(false)

  // ==================== 监听器 ====================

  /**
   * 监听设置变化，自动保存到本地存储
   */
  watch(
    settings,
    (newSettings) => {
      saveSettings(newSettings)
    },
    { deep: true }
  )

  // ==================== 方法 ====================

  /**
   * 更新单个设置项
   * @param key - 设置键名
   * @param value - 设置值
   */
  const updateSetting = async <K extends keyof AppSettings>(
    key: K,
    value: AppSettings[K]
  ): Promise<void> => {
    isSaving.value = true
    try {
      settings.value[key] = value
      // watch 会自动触发保存
    } finally {
      isSaving.value = false
    }
  }

  /**
   * 批量更新设置
   * @param newSettings - 新设置对象
   */
  const updateSettings = async (newSettings: Partial<AppSettings>): Promise<void> => {
    isSaving.value = true
    try {
      Object.assign(settings.value, newSettings)
    } finally {
      isSaving.value = false
    }
  }

  /**
   * 重置为默认设置
   */
  const resetSettings = (): void => {
    settings.value = { ...defaultSettings }
  }

  /**
   * 导出设置为 JSON
   */
  const exportSettings = (): string => {
    return JSON.stringify(settings.value, null, 2)
  }

  /**
   * 导入设置
   * @param jsonString - JSON 格式的设置字符串
   */
  const importSettings = (jsonString: string): boolean => {
    try {
      const imported = JSON.parse(jsonString) as Partial<AppSettings>
      Object.assign(settings.value, imported)
      return true
    } catch {
      return false
    }
  }

  // ==================== 辅助函数 ====================

  /**
   * 从本地存储加载设置
   */
  function loadSettings(): AppSettings {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<AppSettings>
        return { ...defaultSettings, ...parsed }
      }
    } catch (e) {
      console.error('加载设置失败:', e)
    }
    return { ...defaultSettings }
  }

  /**
   * 保存设置到本地存储
   */
  function saveSettings(settingsToSave: AppSettings): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settingsToSave))
    } catch (e) {
      console.error('保存设置失败:', e)
    }
  }

  return {
    // 状态
    settings,
    isSaving,

    // 方法
    updateSetting,
    updateSettings,
    resetSettings,
    exportSettings,
    importSettings
  }
})
