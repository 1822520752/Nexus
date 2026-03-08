<script setup lang="ts">
/**
 * 设置视图组件
 * 提供应用配置和偏好设置界面
 */
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useI18n } from '@/composables'
import { ThemeSettings, ColorSettings, LanguageSettings } from '@/components/settings'
import type { AppSettings } from '@/types'

// ==================== 组合式函数 ====================

const settingsStore = useSettingsStore()
const { t } = useI18n()

// ==================== 响应式状态 ====================

/**
 * 当前激活的设置标签
 */
const activeTab = ref<'appearance' | 'general' | 'advanced'>('appearance')

// ==================== 计算属性 ====================

/**
 * 当前设置
 */
const settings = computed(() => settingsStore.settings)

/**
 * 设置标签列表
 */
const tabs = computed(() => [
  { key: 'appearance', label: t('settings.appearance'), icon: 'palette' },
  { key: 'general', label: t('settings.general'), icon: 'cog' },
  { key: 'advanced', label: '高级', icon: 'beaker' }
])

// ==================== 方法 ====================

/**
 * 更新设置
 * @param key - 设置键名
 * @param value - 设置值
 */
const updateSetting = async <K extends keyof AppSettings>(
  key: K,
  value: AppSettings[K]
): Promise<void> => {
  await settingsStore.updateSetting(key, value)
}

/**
 * 重置设置
 */
const resetSettings = (): void => {
  if (confirm(t('settings.resetConfirm'))) {
    settingsStore.resetSettings()
  }
}

/**
 * 切换标签
 * @param key - 标签键
 */
const switchTab = (key: typeof activeTab.value): void => {
  activeTab.value = key
}
</script>

<template>
  <div class="h-full flex flex-col overflow-hidden">
    <!-- 头部 -->
    <header class="px-6 py-4 border-b border-secondary-700">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-white">{{ t('settings.title') }}</h1>
          <p class="text-sm text-secondary-400">自定义您的应用偏好</p>
        </div>
        
        <!-- 重置按钮 -->
        <button
          @click="resetSettings"
          class="px-4 py-2 text-sm text-secondary-400 hover:text-white bg-secondary-800 hover:bg-secondary-700 rounded-lg border border-secondary-700 transition-colors"
        >
          {{ t('settings.reset') }}
        </button>
      </div>
    </header>

    <!-- 内容区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左侧标签导航 -->
      <nav class="w-48 border-r border-secondary-700 py-4">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="switchTab(tab.key as typeof activeTab)"
          :class="[
            'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
            activeTab === tab.key
              ? 'bg-primary-500/10 text-primary-400 border-r-2 border-primary-500'
              : 'text-secondary-400 hover:text-white hover:bg-secondary-800'
          ]"
        >
          <!-- 图标 -->
          <svg v-if="tab.icon === 'palette'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
          </svg>
          <svg v-else-if="tab.icon === 'cog'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <svg v-else-if="tab.icon === 'beaker'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          
          <span class="text-sm font-medium">{{ tab.label }}</span>
        </button>
      </nav>

      <!-- 右侧设置内容 -->
      <main class="flex-1 overflow-y-auto p-6">
        <div class="max-w-2xl">
          <!-- 外观设置 -->
          <div v-if="activeTab === 'appearance'" class="space-y-8">
            <ThemeSettings />
            <ColorSettings />
            <LanguageSettings />
          </div>

          <!-- 常规设置 -->
          <div v-else-if="activeTab === 'general'" class="space-y-6">
            <section class="card">
              <h2 class="text-lg font-semibold text-white mb-4">{{ t('chat.conversation') }}</h2>

              <div class="space-y-4">
                <!-- 自动保存 -->
                <div class="flex items-center justify-between">
                  <div>
                    <label class="text-white">{{ t('settings.autoSave') }}</label>
                    <p class="text-sm text-secondary-400">自动保存对话历史</p>
                  </div>
                  <button
                    :class="[
                      'relative w-12 h-6 rounded-full transition-colors',
                      settings.autoSave ? 'bg-primary-600' : 'bg-secondary-700'
                    ]"
                    @click="updateSetting('autoSave', !settings.autoSave)"
                  >
                    <span
                      :class="[
                        'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                        settings.autoSave ? 'left-7' : 'left-1'
                      ]"
                    ></span>
                  </button>
                </div>

                <!-- Enter 发送 -->
                <div class="flex items-center justify-between">
                  <div>
                    <label class="text-white">{{ t('settings.sendOnEnter') }}</label>
                    <p class="text-sm text-secondary-400">按 Enter 键发送消息</p>
                  </div>
                  <button
                    :class="[
                      'relative w-12 h-6 rounded-full transition-colors',
                      settings.sendOnEnter ? 'bg-primary-600' : 'bg-secondary-700'
                    ]"
                    @click="updateSetting('sendOnEnter', !settings.sendOnEnter)"
                  >
                    <span
                      :class="[
                        'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                        settings.sendOnEnter ? 'left-7' : 'left-1'
                      ]"
                    ></span>
                  </button>
                </div>

                <!-- 显示 Token 数量 -->
                <div class="flex items-center justify-between">
                  <div>
                    <label class="text-white">{{ t('settings.showTokenCount') }}</label>
                    <p class="text-sm text-secondary-400">在对话中显示 Token 使用量</p>
                  </div>
                  <button
                    :class="[
                      'relative w-12 h-6 rounded-full transition-colors',
                      settings.showTokenCount ? 'bg-primary-600' : 'bg-secondary-700'
                    ]"
                    @click="updateSetting('showTokenCount', !settings.showTokenCount)"
                  >
                    <span
                      :class="[
                        'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                        settings.showTokenCount ? 'left-7' : 'left-1'
                      ]"
                    ></span>
                  </button>
                </div>
              </div>
            </section>
          </div>

          <!-- 高级设置 -->
          <div v-else-if="activeTab === 'advanced'" class="space-y-6">
            <section class="card">
              <h2 class="text-lg font-semibold text-white mb-4">连接设置</h2>

              <div class="space-y-4">
                <!-- 后端地址 -->
                <div>
                  <label class="text-white">{{ t('settings.backendUrl') }}</label>
                  <p class="text-sm text-secondary-400 mb-2">Python FastAPI 后端服务地址</p>
                  <input
                    :value="settings.backendUrl"
                    type="text"
                    class="input"
                    placeholder="http://localhost:8000"
                    @change="updateSetting('backendUrl', ($event.target as HTMLInputElement).value)"
                  />
                </div>
              </div>
            </section>

            <!-- 快捷键说明 -->
            <section class="card">
              <h2 class="text-lg font-semibold text-white mb-4">快捷键</h2>
              
              <div class="space-y-3">
                <div class="flex items-center justify-between py-2 border-b border-secondary-700">
                  <span class="text-secondary-300">{{ t('shortcut.sendMessage') }}</span>
                  <kbd class="px-2 py-1 bg-secondary-700 rounded text-sm font-mono">Ctrl + Enter</kbd>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-secondary-700">
                  <span class="text-secondary-300">{{ t('shortcut.clearChat') }}</span>
                  <kbd class="px-2 py-1 bg-secondary-700 rounded text-sm font-mono">Ctrl + L</kbd>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-secondary-700">
                  <span class="text-secondary-300">{{ t('shortcut.newConversation') }}</span>
                  <kbd class="px-2 py-1 bg-secondary-700 rounded text-sm font-mono">Ctrl + N</kbd>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-secondary-700">
                  <span class="text-secondary-300">{{ t('shortcut.openSettings') }}</span>
                  <kbd class="px-2 py-1 bg-secondary-700 rounded text-sm font-mono">Ctrl + ,</kbd>
                </div>
                <div class="flex items-center justify-between py-2">
                  <span class="text-secondary-300">{{ t('shortcut.saveSettings') }}</span>
                  <kbd class="px-2 py-1 bg-secondary-700 rounded text-sm font-mono">Ctrl + S</kbd>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* 键盘按键样式 */
kbd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
