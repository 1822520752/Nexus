<script setup lang="ts">
/**
 * 颜色配置组件
 * 提供主题颜色选择和自定义功能
 */
import { ref, computed } from 'vue'
import { useTheme, useI18n } from '@/composables'
import type { ThemeColors } from '@/composables/useTheme'

// ==================== 组合式函数 ====================

const { 
  currentColorTheme, 
  themeColors, 
  setColorTheme, 
  getAvailableColorThemes,
  getPresetColors,
  applyThemeColors 
} = useTheme()
const { t } = useI18n()

// ==================== 响应式状态 ====================

/**
 * 是否显示自定义颜色面板
 */
const showCustomPanel = ref(false)

/**
 * 自定义颜色配置
 */
const customColors = ref<ThemeColors>({
  primary: '#3b82f6',
  secondary: '#64748b',
  accent: '#06b6d4',
  background: '#0f172a',
  surface: '#1e293b',
  text: '#f8fafc'
})

// ==================== 计算属性 ====================

/**
 * 可用的颜色主题列表
 */
const availableThemes = computed(() => {
  const themes = getAvailableColorThemes()
  return themes.map(name => ({
    name,
    colors: getPresetColors(name)!
  }))
})

/**
 * 颜色名称映射
 */
const colorNameMap: Record<keyof ThemeColors, string> = {
  primary: '主色',
  secondary: '次色',
  accent: '强调色',
  background: '背景色',
  surface: '表面色',
  text: '文字色'
}

// ==================== 方法 ====================

/**
 * 选择颜色主题
 * @param themeName - 主题名称
 */
const selectColorTheme = (themeName: string): void => {
  setColorTheme(themeName)
  showCustomPanel.value = false
}

/**
 * 应用自定义颜色
 */
const applyCustomColors = (): void => {
  applyThemeColors(customColors.value)
}

/**
 * 重置自定义颜色
 */
const resetCustomColors = (): void => {
  const preset = getPresetColors('blue')
  if (preset) {
    customColors.value = { ...preset }
  }
}

/**
 * 更新单个颜色
 * @param key - 颜色键
 * @param value - 颜色值
 */
const updateColor = (key: keyof ThemeColors, value: string): void => {
  customColors.value[key] = value
}
</script>

<template>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold text-white">{{ t('settings.color') }}</h3>
    
    <!-- 预设颜色主题 -->
    <div class="grid grid-cols-2 gap-3">
      <button
        v-for="theme in availableThemes"
        :key="theme.name"
        @click="selectColorTheme(theme.name)"
        :class="[
          'relative p-4 rounded-xl border-2 transition-all duration-200',
          currentColorTheme === theme.name
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-secondary-700 bg-secondary-800 hover:border-secondary-600'
        ]"
      >
        <!-- 颜色预览 -->
        <div class="flex items-center gap-2 mb-3">
          <div
            class="w-6 h-6 rounded-full"
            :style="{ backgroundColor: theme.colors.primary }"
          ></div>
          <div
            class="w-6 h-6 rounded-full"
            :style="{ backgroundColor: theme.colors.accent }"
          ></div>
          <div
            class="w-6 h-6 rounded-full"
            :style="{ backgroundColor: theme.colors.secondary }"
          ></div>
        </div>

        <!-- 主题名称 -->
        <span
          :class="[
            'text-sm font-medium capitalize',
            currentColorTheme === theme.name ? 'text-primary-400' : 'text-secondary-300'
          ]"
        >
          {{ theme.name }}
        </span>

        <!-- 选中标记 -->
        <div
          v-if="currentColorTheme === theme.name"
          class="absolute top-2 right-2 w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center"
        >
          <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
      </button>
    </div>

    <!-- 自定义颜色按钮 -->
    <button
      @click="showCustomPanel = !showCustomPanel"
      class="w-full p-3 text-sm text-secondary-400 hover:text-white bg-secondary-800 hover:bg-secondary-700 rounded-lg border border-secondary-700 transition-colors flex items-center justify-center gap-2"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
        />
      </svg>
      {{ showCustomPanel ? '隐藏自定义颜色' : '自定义颜色' }}
    </button>

    <!-- 自定义颜色面板 -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="transform opacity-0 -translate-y-2"
      enter-to-class="transform opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="transform opacity-100 translate-y-0"
      leave-to-class="transform opacity-0 -translate-y-2"
    >
      <div
        v-if="showCustomPanel"
        class="p-4 bg-secondary-800 rounded-lg border border-secondary-700 space-y-4"
      >
        <h4 class="text-sm font-medium text-secondary-300">自定义颜色配置</h4>
        
        <!-- 颜色输入列表 -->
        <div class="space-y-3">
          <div
            v-for="(label, key) in colorNameMap"
            :key="key"
            class="flex items-center justify-between"
          >
            <label class="text-sm text-secondary-400">{{ label }}</label>
            <div class="flex items-center gap-2">
              <input
                type="color"
                :value="customColors[key]"
                @input="(e) => updateColor(key, (e.target as HTMLInputElement).value)"
                class="w-8 h-8 rounded cursor-pointer bg-transparent"
              />
              <input
                type="text"
                :value="customColors[key]"
                @input="(e) => updateColor(key, (e.target as HTMLInputElement).value)"
                class="w-24 px-2 py-1 text-xs bg-secondary-900 border border-secondary-700 rounded text-white font-mono"
              />
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex items-center gap-2 pt-2">
          <button
            @click="applyCustomColors"
            class="flex-1 px-3 py-2 text-sm bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
          >
            应用自定义颜色
          </button>
          <button
            @click="resetCustomColors"
            class="px-3 py-2 text-sm bg-secondary-700 hover:bg-secondary-600 rounded-lg transition-colors"
          >
            重置
          </button>
        </div>
      </div>
    </Transition>

    <!-- 当前颜色预览 -->
    <div class="p-4 bg-secondary-800 rounded-lg border border-secondary-700">
      <h4 class="text-sm font-medium text-secondary-300 mb-3">当前颜色</h4>
      <div class="flex items-center gap-4">
        <div
          v-for="(color, key) in themeColors"
          :key="key"
          class="flex flex-col items-center gap-1"
        >
          <div
            class="w-10 h-10 rounded-lg border border-secondary-600"
            :style="{ backgroundColor: color }"
          ></div>
          <span class="text-xs text-secondary-500">{{ colorNameMap[key] }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 颜色输入框样式 */
input[type="color"] {
  -webkit-appearance: none;
  border: none;
  padding: 0;
}

input[type="color"]::-webkit-color-swatch-wrapper {
  padding: 0;
}

input[type="color"]::-webkit-color-swatch {
  border: 2px solid theme('colors.secondary.600');
  border-radius: 4px;
}
</style>
