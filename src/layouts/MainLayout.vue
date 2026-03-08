<script setup lang="ts">
/**
 * 主界面布局组件
 * 提供左侧可折叠面板、右侧对话区域和底部状态栏
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme, useI18n, useShortcuts } from '@/composables'
import { useChatStore } from '@/stores/chat'
import { useModelsStore } from '@/stores/models'
import ModelSelector from '@/components/chat/ModelSelector.vue'

// ==================== 组合式函数 ====================

const router = useRouter()
const { isDark, toggleTheme, themeMode } = useTheme()
const { t, currentLanguage, setLanguage, supportedLanguages } = useI18n()
const chatStore = useChatStore()
const modelsStore = useModelsStore()

// ==================== 响应式状态 ====================

/**
 * 左侧面板是否折叠
 */
const isSidebarCollapsed = ref(false)

/**
 * 左侧面板宽度
 */
const sidebarWidth = ref(280)

/**
 * 当前激活的侧边栏项
 */
const activeSidebarItem = ref<'chat' | 'documents' | 'actions' | 'memory'>('chat')

/**
 * 是否显示设置面板
 */
const showSettingsPanel = ref(false)

/**
 * 状态栏消息
 */
const statusMessage = ref('就绪')

// ==================== 计算属性 ====================

/**
 * 当前模型名称
 */
const currentModelName = computed(() => {
  return modelsStore.currentModel?.name || t('chat.noModel')
})

/**
 * 对话数量
 */
const conversationCount = computed(() => chatStore.totalConversations)

// ==================== 方法 ====================

/**
 * 切换侧边栏折叠状态
 */
const toggleSidebar = (): void => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
}

/**
 * 切换侧边栏项
 * @param item - 侧边栏项标识
 */
const switchSidebarItem = (item: typeof activeSidebarItem.value): void => {
  activeSidebarItem.value = item
  
  // 根据选择的项目导航到对应路由
  switch (item) {
    case 'chat':
      router.push('/chat')
      break
    case 'documents':
      router.push('/documents')
      break
    case 'actions':
      router.push('/actions')
      break
    case 'memory':
      router.push('/memory')
      break
  }
}

/**
 * 新建对话
 */
const createNewConversation = (): void => {
  if (modelsStore.currentModel) {
    chatStore.createConversation(modelsStore.currentModel)
    statusMessage.value = t('chat.new')
  }
}

/**
 * 清空对话
 */
const clearConversations = (): void => {
  if (confirm(t('chat.deleteConfirm'))) {
    chatStore.clearAllConversations()
    statusMessage.value = t('common.success')
  }
}

/**
 * 打开设置
 */
const openSettings = (): void => {
  showSettingsPanel.value = true
  router.push('/settings')
}

/**
 * 关闭设置
 */
const closeSettings = (): void => {
  showSettingsPanel.value = false
}

/**
 * 切换语言
 */
const toggleLanguage = (): void => {
  const currentIndex = supportedLanguages.findIndex(
    lang => lang.code === currentLanguage.value
  )
  const nextIndex = (currentIndex + 1) % supportedLanguages.length
  setLanguage(supportedLanguages[nextIndex].code)
}

// ==================== 快捷键处理 ====================

/**
 * 处理发送消息快捷键
 */
const handleSendMessage = (): void => {
  window.dispatchEvent(new CustomEvent('shortcut:send-message'))
}

/**
 * 处理清空对话快捷键
 */
const handleClearChat = (): void => {
  clearConversations()
}

/**
 * 处理新建对话快捷键
 */
const handleNewConversation = (): void => {
  createNewConversation()
}

/**
 * 处理打开设置快捷键
 */
const handleOpenSettings = (): void => {
  openSettings()
}

// 注册快捷键
useShortcuts([
  {
    key: 'Enter',
    ctrl: true,
    handler: handleSendMessage,
    description: t('shortcut.sendMessage')
  },
  {
    key: 'l',
    ctrl: true,
    handler: handleClearChat,
    description: t('shortcut.clearChat')
  },
  {
    key: 'n',
    ctrl: true,
    handler: handleNewConversation,
    description: t('shortcut.newConversation')
  },
  {
    key: ',',
    ctrl: true,
    handler: handleOpenSettings,
    description: t('shortcut.openSettings')
  }
])

// ==================== 生命周期 ====================

onMounted(() => {
  // 初始化模型列表
  if (modelsStore.models.length === 0) {
    modelsStore.initialize()
  }
  
  // 监听快捷键事件
  window.addEventListener('shortcut:clear-chat', handleClearChat)
  window.addEventListener('shortcut:new-conversation', handleNewConversation)
  window.addEventListener('shortcut:open-settings', handleOpenSettings)
})

onUnmounted(() => {
  window.removeEventListener('shortcut:clear-chat', handleClearChat)
  window.removeEventListener('shortcut:new-conversation', handleNewConversation)
  window.removeEventListener('shortcut:open-settings', handleOpenSettings)
})
</script>

<template>
  <div class="flex h-screen bg-secondary-900 text-white overflow-hidden">
    <!-- 左侧面板 -->
    <aside
      class="flex flex-col bg-secondary-800 border-r border-secondary-700 transition-all duration-300 ease-in-out"
      :style="{ width: isSidebarCollapsed ? '64px' : `${sidebarWidth}px` }"
    >
      <!-- 顶部标题区域 -->
      <div class="flex items-center justify-between px-4 py-4 border-b border-secondary-700">
        <div v-if="!isSidebarCollapsed" class="flex items-center gap-2">
          <span class="text-xl font-bold text-gradient">{{ t('app.name') }}</span>
        </div>
        <button
          @click="toggleSidebar"
          class="p-2 rounded-lg hover:bg-secondary-700 transition-colors"
          :title="isSidebarCollapsed ? '展开' : '折叠'"
        >
          <svg
            class="w-5 h-5 transition-transform duration-300"
            :class="{ 'rotate-180': isSidebarCollapsed }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
            />
          </svg>
        </button>
      </div>

      <!-- 模型选择区域 -->
      <div v-if="!isSidebarCollapsed" class="px-3 py-3 border-b border-secondary-700">
        <ModelSelector @change="(model) => modelsStore.setCurrentModel(model.id)" />
      </div>

      <!-- 侧边栏导航 -->
      <nav class="flex-1 py-2 overflow-y-auto scrollbar-hide">
        <!-- 对话入口 -->
        <button
          @click="switchSidebarItem('chat')"
          class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-secondary-700 transition-colors"
          :class="{ 'bg-secondary-700': activeSidebarItem === 'chat' }"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed" class="flex-1">{{ t('nav.chat') }}</span>
          <span
            v-if="!isSidebarCollapsed && conversationCount > 0"
            class="px-2 py-0.5 text-xs bg-primary-600 rounded-full"
          >
            {{ conversationCount }}
          </span>
        </button>

        <!-- 文档管理入口 -->
        <button
          @click="switchSidebarItem('documents')"
          class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-secondary-700 transition-colors"
          :class="{ 'bg-secondary-700': activeSidebarItem === 'documents' }"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.documents') || '文档' }}</span>
        </button>

        <!-- 动作面板入口 -->
        <button
          @click="switchSidebarItem('actions')"
          class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-secondary-700 transition-colors"
          :class="{ 'bg-secondary-700': activeSidebarItem === 'actions' }"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.actions') || '动作' }}</span>
        </button>

        <!-- 记忆管理入口 -->
        <button
          @click="switchSidebarItem('memory')"
          class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-secondary-700 transition-colors"
          :class="{ 'bg-secondary-700': activeSidebarItem === 'memory' }"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.memory') || '记忆' }}</span>
        </button>
      </nav>

      <!-- 底部操作区域 -->
      <div class="border-t border-secondary-700 py-2">
        <!-- 新建对话按钮 -->
        <button
          v-if="!isSidebarCollapsed"
          @click="createNewConversation"
          class="w-full flex items-center gap-2 px-4 py-2 mx-2 rounded-lg bg-primary-600 hover:bg-primary-700 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          <span>{{ t('chat.new') }}</span>
        </button>

        <!-- 设置按钮 -->
        <button
          @click="openSettings"
          class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-secondary-700 transition-colors"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.settings') }}</span>
        </button>
      </div>
    </aside>

    <!-- 右侧主内容区域 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶部工具栏 -->
      <header class="flex items-center justify-between px-6 py-3 bg-secondary-800/50 border-b border-secondary-700">
        <div class="flex items-center gap-4">
          <h1 class="text-lg font-semibold">{{ t('chat.title') }}</h1>
          <span class="text-sm text-secondary-400">{{ currentModelName }}</span>
        </div>
        
        <div class="flex items-center gap-2">
          <!-- 主题切换按钮 -->
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg hover:bg-secondary-700 transition-colors"
            :title="t('settings.theme')"
          >
            <svg v-if="isDark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          </button>

          <!-- 语言切换按钮 -->
          <button
            @click="toggleLanguage"
            class="p-2 rounded-lg hover:bg-secondary-700 transition-colors"
            :title="t('settings.language')"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
              />
            </svg>
          </button>

          <!-- 清空对话按钮 -->
          <button
            @click="clearConversations"
            class="p-2 rounded-lg hover:bg-secondary-700 transition-colors text-secondary-400 hover:text-white"
            :title="t('chat.clear')"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </header>

      <!-- 路由视图区域 -->
      <div class="flex-1 overflow-hidden">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <!-- 底部状态栏 -->
    <footer class="fixed bottom-0 left-0 right-0 h-8 bg-secondary-800 border-t border-secondary-700 flex items-center justify-between px-4 text-xs text-secondary-400 z-50">
      <div class="flex items-center gap-4">
        <span>{{ statusMessage }}</span>
        <span v-if="chatStore.isLoading" class="flex items-center gap-1">
          <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ t('common.loading') }}
        </span>
      </div>
      
      <div class="flex items-center gap-4">
        <span>{{ t('settings.theme') }}: {{ t(`settings.theme.${themeMode}`) }}</span>
        <span>{{ t('settings.language') }}: {{ currentLanguage }}</span>
        <span>Ctrl+Enter: {{ t('shortcut.sendMessage') }}</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 侧边栏过渡 */
aside {
  will-change: width;
}

/* 状态栏偏移 */
main {
  padding-bottom: 32px;
}
</style>
