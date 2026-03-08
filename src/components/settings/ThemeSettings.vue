<script setup lang="ts">
/**
 * 主题设置组件
 * 提供深色/浅色/跟随系统主题切换功能
 */
import { computed } from 'vue'
import { useTheme, useI18n } from '@/composables'
import type { ThemeMode } from '@/composables/useTheme'

// ==================== 组合式函数 ====================

const { themeMode, actualTheme, isDark, setThemeMode, toggleTheme } = useTheme()
const { t } = useI18n()

// ==================== 计算属性 ====================

/**
 * 主题选项列表
 */
const themeOptions = computed(() => [
  {
    value: 'light' as ThemeMode,
    label: t('settings.theme.light'),
    description: '使用浅色主题',
    icon: 'sun'
  },
  {
    value: 'dark' as ThemeMode,
    label: t('settings.theme.dark'),
    description: '使用深色主题',
    icon: 'moon'
  },
  {
    value: 'system' as ThemeMode,
    label: t('settings.theme.system'),
    description: '跟随系统主题设置',
    icon: 'computer'
  }
])

// ==================== 方法 ====================

/**
 * 选择主题
 * @param mode - 主题模式
 */
const selectTheme = (mode: ThemeMode): void => {
  setThemeMode(mode)
}

/**
 * 获取主题图标
 * @param icon - 图标名称
 */
const getThemeIcon = (icon: string): string => {
  return icon
}
</script>

<template>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold text-white">{{ t('settings.theme') }}</h3>
    
    <!-- 主题选项 -->
    <div class="grid grid-cols-3 gap-3">
      <button
        v-for="option in themeOptions"
        :key="option.value"
        @click="selectTheme(option.value)"
        :class="[
          'flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200',
          themeMode === option.value
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-secondary-700 bg-secondary-800 hover:border-secondary-600'
        ]"
      >
        <!-- 图标 -->
        <div
          :class="[
            'w-12 h-12 rounded-full flex items-center justify-center',
            themeMode === option.value
              ? 'bg-primary-500 text-white'
              : 'bg-secondary-700 text-secondary-400'
          ]"
        >
          <!-- 太阳图标 -->
          <svg v-if="option.icon === 'sun'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
          
          <!-- 月亮图标 -->
          <svg v-else-if="option.icon === 'moon'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
          
          <!-- 电脑图标 -->
          <svg v-else-if="option.icon === 'computer'" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        </div>

        <!-- 标签 -->
        <span
          :class="[
            'text-sm font-medium',
            themeMode === option.value ? 'text-primary-400' : 'text-secondary-300'
          ]"
        >
          {{ option.label }}
        </span>

        <!-- 描述 -->
        <span class="text-xs text-secondary-500 text-center">
          {{ option.description }}
        </span>
      </button>
    </div>

    <!-- 当前状态 -->
    <div class="p-4 bg-secondary-800 rounded-lg border border-secondary-700">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div
            :class="[
              'w-3 h-3 rounded-full',
              isDark ? 'bg-indigo-500' : 'bg-yellow-500'
            ]"
          ></div>
          <span class="text-sm text-secondary-300">
            当前主题: 
            <span class="text-white font-medium">
              {{ actualTheme === 'dark' ? '深色模式' : '浅色模式' }}
            </span>
          </span>
        </div>
        
        <button
          @click="toggleTheme"
          class="px-3 py-1.5 text-sm bg-secondary-700 hover:bg-secondary-600 rounded-lg transition-colors"
        >
          快速切换
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>
