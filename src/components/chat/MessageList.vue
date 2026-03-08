<script setup lang="ts">
/**
 * 消息列表组件
 * 显示对话中的所有消息，支持自动滚动和虚拟滚动
 */
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import type { Message } from '@/types'
import MessageItem from './MessageItem.vue'
import StreamingMessage from './StreamingMessage.vue'

// ==================== Props 定义 ====================

interface Props {
  /** 消息列表 */
  messages: Message[]
  /** 是否正在加载 */
  isLoading?: boolean
  /** 流式响应内容 */
  streamingContent?: string
  /** 是否正在流式输出 */
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  streamingContent: '',
  isStreaming: false
})

// ==================== Emits 定义 ====================

const emit = defineEmits<{
  /** 复制消息事件 */
  (e: 'copy', message: Message): void
  /** 删除消息事件 */
  (e: 'delete', messageId: string): void
  /** 重试消息事件 */
  (e: 'retry', message: Message): void
}>()

// ==================== 响应式状态 ====================

/**
 * 消息列表容器引用
 */
const containerRef = ref<HTMLElement | null>(null)

/**
 * 是否自动滚动到底部
 */
const autoScroll = ref(true)

/**
 * 是否显示滚动到底部按钮
 */
const showScrollButton = ref(false)

/**
 * 滚动阈值（距离底部多少像素时认为接近底部）
 */
const SCROLL_THRESHOLD = 100

// ==================== 计算属性 ====================

/**
 * 是否有消息
 */
const hasMessages = computed(() => props.messages.length > 0)

/**
 * 是否显示空状态
 */
const showEmptyState = computed(() => !hasMessages.value && !props.isLoading)

// ==================== 方法 ====================

/**
 * 滚动到底部
 * @param behavior - 滚动行为
 */
const scrollToBottom = (behavior: ScrollBehavior = 'smooth'): void => {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: containerRef.value.scrollHeight,
        behavior
      })
    }
  })
}

/**
 * 处理滚动事件
 */
const handleScroll = (): void => {
  if (!containerRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const isNearBottom = scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD

  showScrollButton.value = !isNearBottom
  autoScroll.value = isNearBottom
}

/**
 * 处理复制消息
 * @param message - 消息对象
 */
const handleCopy = (message: Message): void => {
  emit('copy', message)
}

/**
 * 处理删除消息
 * @param messageId - 消息ID
 */
const handleDelete = (messageId: string): void => {
  emit('delete', messageId)
}

/**
 * 处理重试消息
 * @param message - 消息对象
 */
const handleRetry = (message: Message): void => {
  emit('retry', message)
}

// ==================== 监听器 ====================

/**
 * 监听消息变化，自动滚动到底部
 */
watch(
  () => props.messages.length,
  () => {
    if (autoScroll.value) {
      scrollToBottom()
    }
  }
)

/**
 * 监听流式内容变化，自动滚动
 */
watch(
  () => props.streamingContent,
  () => {
    if (autoScroll.value && props.isStreaming) {
      scrollToBottom('auto')
    }
  }
)

// ==================== 生命周期 ====================

onMounted(() => {
  // 初始滚动到底部
  scrollToBottom('auto')
})
</script>

<template>
  <div
    ref="containerRef"
    class="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin"
    @scroll="handleScroll"
  >
    <!-- 消息列表 -->
    <div class="max-w-4xl mx-auto space-y-6">
      <!-- 遍历消息 -->
      <MessageItem
        v-for="message in messages"
        :key="message.id"
        :message="message"
        @copy="handleCopy"
        @delete="handleDelete"
        @retry="handleRetry"
      />

      <!-- 流式响应消息 -->
      <StreamingMessage
        v-if="isStreaming && streamingContent"
        :content="streamingContent"
      />

      <!-- 加载状态 -->
      <div
        v-if="isLoading && !isStreaming"
        class="flex items-center gap-3 text-secondary-400"
      >
        <div class="w-8 h-8 rounded-full bg-accent-600 flex items-center justify-center">
          <span class="text-sm">AI</span>
        </div>
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span class="text-sm">正在思考...</span>
        </div>
      </div>

      <!-- 空状态 -->
      <div
        v-if="showEmptyState"
        class="flex flex-col items-center justify-center py-20 text-center"
      >
        <div class="w-16 h-16 mb-4 rounded-full bg-secondary-800 flex items-center justify-center">
          <svg class="w-8 h-8 text-secondary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h3 class="text-lg font-medium text-secondary-300 mb-2">开始与 AI 对话吧</h3>
        <p class="text-sm text-secondary-500 max-w-md">
          选择一个模型，输入您的问题，AI 将为您提供智能回答
        </p>
      </div>
    </div>

    <!-- 滚动到底部按钮 -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="transform opacity-0 translate-y-2"
      enter-to-class="transform opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="transform opacity-100 translate-y-0"
      leave-to-class="transform opacity-0 translate-y-2"
    >
      <button
        v-if="showScrollButton"
        @click="scrollToBottom()"
        class="fixed bottom-24 right-8 p-3 bg-secondary-700 hover:bg-secondary-600 rounded-full shadow-lg transition-colors z-10"
        title="滚动到底部"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      </button>
    </Transition>
  </div>
</template>

<style scoped>
/* 细滚动条样式 */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: theme('colors.secondary.600');
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: theme('colors.secondary.500');
}
</style>
