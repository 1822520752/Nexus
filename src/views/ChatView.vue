<script setup lang="ts">
/**
 * 对话视图组件
 * 提供 AI 对话交互界面
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useModelsStore } from '@/stores/models'
import { useI18n } from '@/composables'
import { MessageList, ChatInput } from '@/components/chat'
import type { Message } from '@/types'

// ==================== 组合式函数 ====================

const chatStore = useChatStore()
const modelsStore = useModelsStore()
const { t } = useI18n()

// ==================== 响应式状态 ====================

/**
 * 输入框引用
 */
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null)

/**
 * 流式响应内容
 */
const streamingContent = ref('')

/**
 * 是否正在流式输出
 */
const isStreaming = ref(false)

// ==================== 计算属性 ====================

/**
 * 消息列表
 */
const messages = computed(() => chatStore.currentConversation?.messages || [])

/**
 * 是否正在加载
 */
const isLoading = computed(() => chatStore.isLoading)

/**
 * 当前模型
 */
const currentModel = computed(() => modelsStore.currentModel)

/**
 * 是否有选中的模型
 */
const hasModel = computed(() => !!currentModel.value)

// ==================== 方法 ====================

/**
 * 发送消息
 * @param content - 消息内容
 */
const sendMessage = async (content: string): Promise<void> => {
  if (!hasModel.value) {
    alert(t('tip.selectModel'))
    return
  }

  // 如果没有当前对话，创建新对话
  if (!chatStore.currentConversation) {
    chatStore.createConversation(currentModel.value!)
  }

  // 开始流式输出模拟
  isStreaming.value = true
  streamingContent.value = ''

  try {
    await chatStore.sendMessage(content)
    
    // 模拟流式输出效果
    const lastMessage = messages.value[messages.value.length - 1]
    if (lastMessage?.role === 'assistant') {
      // 实际应用中，这里应该连接到后端的流式 API
      streamingContent.value = lastMessage.content
    }
  } catch (error) {
    console.error('发送消息失败:', error)
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
  }
}

/**
 * 停止生成
 */
const stopGeneration = (): void => {
  isStreaming.value = false
  streamingContent.value = ''
  // TODO: 调用后端 API 停止生成
}

/**
 * 处理复制消息
 * @param message - 消息对象
 */
const handleCopy = (message: Message): void => {
  console.log('复制消息:', message.id)
}

/**
 * 处理删除消息
 * @param messageId - 消息ID
 */
const handleDelete = (messageId: string): void => {
  // TODO: 实现删除消息功能
  console.log('删除消息:', messageId)
}

/**
 * 处理重试消息
 * @param message - 消息对象
 */
const handleRetry = (message: Message): void => {
  // TODO: 实现重试消息功能
  console.log('重试消息:', message.id)
}

/**
 * 处理输入变化
 * @param content - 输入内容
 */
const handleInput = (content: string): void => {
  // 可以在这里实现输入提示等功能
}

// ==================== 快捷键处理 ====================

/**
 * 处理发送消息快捷键
 */
const handleSendMessageShortcut = (): void => {
  chatInputRef.value?.focusInput()
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 监听快捷键事件
  window.addEventListener('shortcut:send-message', handleSendMessageShortcut)
})

onUnmounted(() => {
  window.removeEventListener('shortcut:send-message', handleSendMessageShortcut)
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 消息列表 -->
    <MessageList
      :messages="messages"
      :is-loading="isLoading"
      :streaming-content="streamingContent"
      :is-streaming="isStreaming"
      @copy="handleCopy"
      @delete="handleDelete"
      @retry="handleRetry"
    />

    <!-- 输入区域 -->
    <ChatInput
      ref="chatInputRef"
      :disabled="!hasModel"
      :is-sending="isLoading || isStreaming"
      @send="sendMessage"
      @input="handleInput"
      @stop="stopGeneration"
    />
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>
