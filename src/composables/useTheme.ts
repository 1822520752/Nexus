/**
 * 主题管理 Composable
 * 提供主题切换、颜色配置等功能
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/**
 * 主题类型
 */
export type ThemeMode = 'light' | 'dark' | 'system'

/**
 * 主题颜色配置
 */
export interface ThemeColors {
  primary: string
  secondary: string
  accent: string
  background: string
  surface: string
  text: string
}

/**
 * 预设主题颜色
 */
const presetColors: Record<string, ThemeColors> = {
  blue: {
    primary: '#3b82f6',
    secondary: '#64748b',
    accent: '#06b6d4',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f8fafc'
  },
  purple: {
    primary: '#8b5cf6',
    secondary: '#6b7280',
    accent: '#ec4899',
    background: '#0c0a1d',
    surface: '#1a1625',
    text: '#faf5ff'
  },
  green: {
    primary: '#10b981',
    secondary: '#6b7280',
    accent: '#14b8a6',
    background: '#022c22',
    surface: '#064e3b',
    text: '#ecfdf5'
  },
  orange: {
    primary: '#f97316',
    secondary: '#6b7280',
    accent: '#eab308',
    background: '#1c1917',
    surface: '#292524',
    text: '#fafaf9'
  }
}

/**
 * 系统主题媒体查询
 */
const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')

/**
 * 当前系统主题
 */
const systemTheme = ref<'light' | 'dark'>(darkModeQuery.matches ? 'dark' : 'light')

/**
 * 监听系统主题变化
 */
const handleSystemThemeChange = (e: MediaQueryListEvent) => {
  systemTheme.value = e.matches ? 'dark' : 'light'
}

/**
 * 主题管理 Hook
 */
export function useTheme() {
  const settingsStore = useSettingsStore()

  /**
   * 当前选中的颜色主题
   */
  const currentColorTheme = ref<string>('blue')

  /**
   * 当前主题模式
   */
  const themeMode = computed<ThemeMode>({
    get: () => settingsStore.settings.theme,
    set: (value) => settingsStore.updateSetting('theme', value)
  })

  /**
   * 实际应用的主题（解析 system 模式）
   */
  const actualTheme = computed<'light' | 'dark'>(() => {
    if (themeMode.value === 'system') {
      return systemTheme.value
    }
    return themeMode.value
  })

  /**
   * 是否为深色模式
   */
  const isDark = computed(() => actualTheme.value === 'dark')

  /**
   * 当前主题颜色
   */
  const themeColors = computed<ThemeColors>(() => {
    return presetColors[currentColorTheme.value] || presetColors.blue
  })

  /**
   * 切换主题模式
   */
  const toggleTheme = (): void => {
    const modes: ThemeMode[] = ['light', 'dark', 'system']
    const currentIndex = modes.indexOf(themeMode.value)
    const nextIndex = (currentIndex + 1) % modes.length
    themeMode.value = modes[nextIndex]
  }

  /**
   * 设置主题模式
   * @param mode - 主题模式
   */
  const setThemeMode = (mode: ThemeMode): void => {
    themeMode.value = mode
  }

  /**
   * 设置颜色主题
   * @param colorTheme - 颜色主题名称
   */
  const setColorTheme = (colorTheme: string): void => {
    if (presetColors[colorTheme]) {
      currentColorTheme.value = colorTheme
      applyThemeColors(presetColors[colorTheme])
    }
  }

  /**
   * 应用主题颜色到 CSS 变量
   * @param colors - 主题颜色配置
   */
  const applyThemeColors = (colors: ThemeColors): void => {
    const root = document.documentElement
    root.style.setProperty('--color-primary', colors.primary)
    root.style.setProperty('--color-secondary', colors.secondary)
    root.style.setProperty('--color-accent', colors.accent)
    root.style.setProperty('--color-background', colors.background)
    root.style.setProperty('--color-surface', colors.surface)
    root.style.setProperty('--color-text', colors.text)
  }

  /**
   * 应用主题到 DOM
   */
  const applyTheme = (): void => {
    const root = document.documentElement
    
    // 移除旧主题类
    root.classList.remove('light', 'dark')
    
    // 添加新主题类
    root.classList.add(actualTheme.value)
    
    // 更新 CSS 变量
    if (isDark.value) {
      root.style.colorScheme = 'dark'
    } else {
      root.style.colorScheme = 'light'
    }
  }

  /**
   * 获取所有预设颜色主题
   */
  const getAvailableColorThemes = (): string[] => {
    return Object.keys(presetColors)
  }

  /**
   * 获取预设颜色配置
   * @param name - 主题名称
   */
  const getPresetColors = (name: string): ThemeColors | undefined => {
    return presetColors[name]
  }

  // 监听主题变化
  watch(actualTheme, applyTheme, { immediate: true })

  // 组件挂载时添加系统主题监听
  onMounted(() => {
    darkModeQuery.addEventListener('change', handleSystemThemeChange)
    applyTheme()
  })

  // 组件卸载时移除监听
  onUnmounted(() => {
    darkModeQuery.removeEventListener('change', handleSystemThemeChange)
  })

  return {
    // 状态
    themeMode,
    actualTheme,
    isDark,
    currentColorTheme,
    themeColors,

    // 方法
    toggleTheme,
    setThemeMode,
    setColorTheme,
    applyThemeColors,
    getAvailableColorThemes,
    getPresetColors
  }
}

// 导出预设颜色供外部使用
export { presetColors }
