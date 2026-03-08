<script setup lang="ts">
/**
 * 语言设置组件
 * 提供多语言切换功能
 */
import { computed } from 'vue'
import { useI18n } from '@/composables'
import type { LanguageCode } from '@/composables/useI18n'

// ==================== 组合式函数 ====================

const { 
  currentLanguage, 
  currentLanguageConfig, 
  supportedLanguages, 
  setLanguage,
  isChinese,
  isEnglish
} = useI18n()

// ==================== 计算属性 ====================

/**
 * 当前语言图标
 */
const currentLangIcon = computed(() => {
  return isChinese.value ? '🇨🇳' : '🇺🇸'
})

// ==================== 方法 ====================

/**
 * 选择语言
 * @param code - 语言代码
 */
const selectLanguage = (code: LanguageCode): void => {
  setLanguage(code)
}

/**
 * 获取语言图标
 * @param code - 语言代码
 */
const getLanguageIcon = (code: LanguageCode): string => {
  switch (code) {
    case 'zh-CN':
      return '🇨🇳'
    case 'en-US':
      return '🇺🇸'
    default:
      return '🌐'
  }
}
</script>

<template>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold text-white">{{ t('settings.language') }}</h3>
    
    <!-- 当前语言显示 -->
    <div class="p-4 bg-secondary-800 rounded-lg border border-secondary-700">
      <div class="flex items-center gap-3">
        <span class="text-3xl">{{ currentLangIcon }}</span>
        <div>
          <div class="text-white font-medium">{{ currentLanguageConfig?.nativeName }}</div>
          <div class="text-sm text-secondary-400">{{ currentLanguageConfig?.name }}</div>
        </div>
      </div>
    </div>

    <!-- 语言选项列表 -->
    <div class="space-y-2">
      <button
        v-for="lang in supportedLanguages"
        :key="lang.code"
        @click="selectLanguage(lang.code)"
        :class="[
          'w-full flex items-center gap-3 p-4 rounded-xl border-2 transition-all duration-200',
          currentLanguage === lang.code
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-secondary-700 bg-secondary-800 hover:border-secondary-600'
        ]"
      >
        <!-- 语言图标 -->
        <span class="text-2xl">{{ getLanguageIcon(lang.code) }}</span>
        
        <!-- 语言信息 -->
        <div class="flex-1 text-left">
          <div
            :class="[
              'font-medium',
              currentLanguage === lang.code ? 'text-primary-400' : 'text-white'
            ]"
          >
            {{ lang.nativeName }}
          </div>
          <div class="text-sm text-secondary-400">{{ lang.name }}</div>
        </div>

        <!-- 选中标记 -->
        <div
          v-if="currentLanguage === lang.code"
          class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center"
        >
          <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
      </button>
    </div>

    <!-- 语言说明 -->
    <div class="p-4 bg-secondary-800/50 rounded-lg border border-secondary-700/50">
      <div class="flex items-start gap-3">
        <svg class="w-5 h-5 text-secondary-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div class="text-sm text-secondary-400">
          <p class="mb-2">切换语言后，界面将立即更新为所选语言。</p>
          <p>支持的语言：简体中文、English (US)</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>
