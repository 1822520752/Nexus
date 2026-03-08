<script setup lang="ts">
/**
 * 单条消息组件
 * 支持Markdown渲染、代码高亮、消息复制等功能
 */
import { ref, computed, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import type { Message } from '@/types'
import { useI18n } from '@/composables'

// ==================== Props 定义 ====================

interface Props {
  /** 消息对象 */
  message: Message
}

const props = defineProps<Props>()

// ==================== Emits 定义 ====================

const emit = defineEmits<{
  /** 复制消息事件 */
  (e: 'copy', message: Message): void
  /** 删除消息事件 */
  (e: 'delete', messageId: string): void
  /** 重试消息事件 */
  (e: 'retry', message: Message): void
}>()

// ==================== 组合式函数 ====================

const { t } = useI18n()

// ==================== 响应式状态 ====================

/**
 * 是否显示操作菜单
 */
const showMenu = ref(false)

/**
 * 复制状态
 */
const copyState = ref<'idle' | 'copied'>('idle')

/**
 * 代码块复制状态映射
 */
const codeCopyStates = ref<Record<number, 'idle' | 'copied'>>({})

// ==================== 计算属性 ====================

/**
 * 是否为用户消息
 */
const isUser = computed(() => props.message.role === 'user')

/**
 * 是否为助手消息
 */
const isAssistant = computed(() => props.message.role === 'assistant')

/**
 * 角色显示名称
 */
const roleName = computed(() => {
  switch (props.message.role) {
    case 'user':
      return t('message.user')
    case 'assistant':
      return t('message.assistant')
    case 'system':
      return t('message.system')
    default:
      return 'Unknown'
  }
})

/**
 * 角色头像背景色
 */
const avatarBg = computed(() => {
  switch (props.message.role) {
    case 'user':
      return 'bg-primary-600'
    case 'assistant':
      return 'bg-accent-600'
    case 'system':
      return 'bg-secondary-600'
    default:
      return 'bg-secondary-600'
  }
})

/**
 * 消息气泡样式
 */
const bubbleClass = computed(() => {
  if (isUser.value) {
    return 'bg-primary-600 text-white'
  }
  return 'bg-secondary-800 text-white border border-secondary-700'
})

/**
 * 格式化时间戳
 */
const formattedTime = computed(() => {
  const date = new Date(props.message.timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
})

/**
 * 渲染后的HTML内容
 */
const renderedContent = computed(() => {
  return renderMarkdown(props.message.content)
})

// ==================== 方法 ====================

/**
 * 配置 marked 选项
 */
const configureMarked = (): void => {
  marked.setOptions({
    highlight: (code: string, lang: string) => {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value
        } catch {
          // 忽略错误
        }
      }
      return hljs.highlightAuto(code).value
    },
    breaks: true,
    gfm: true
  })
}

/**
 * 渲染 Markdown 内容
 * @param content - 原始内容
 * @returns 渲染后的 HTML
 */
const renderMarkdown = (content: string): string => {
  try {
    return marked.parse(content) as string
  } catch {
    return content
  }
}

/**
 * 复制消息内容
 */
const copyMessage = async (): Promise<void> => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copyState.value = 'copied'
    emit('copy', props.message)
    
    setTimeout(() => {
      copyState.value = 'idle'
    }, 2000)
  } catch (error) {
    console.error('复制失败:', error)
  }
  
  showMenu.value = false
}

/**
 * 复制代码块
 * @param code - 代码内容
 * @param index - 代码块索引
 */
const copyCode = async (code: string, index: number): Promise<void> => {
  try {
    await navigator.clipboard.writeText(code)
    codeCopyStates.value[index] = 'copied'
    
    setTimeout(() => {
      codeCopyStates.value[index] = 'idle'
    }, 2000)
  } catch (error) {
    console.error('复制代码失败:', error)
  }
}

/**
 * 删除消息
 */
const deleteMessage = (): void => {
  emit('delete', props.message.id)
  showMenu.value = false
}

/**
 * 重试消息
 */
const retryMessage = (): void => {
  emit('retry', props.message)
  showMenu.value = false
}

/**
 * 切换菜单显示
 */
const toggleMenu = (): void => {
  showMenu.value = !showMenu.value
}

/**
 * 提取代码块
 * @param html - 渲染后的 HTML
 * @returns 带有复制按钮的代码块 HTML
 */
const processCodeBlocks = (html: string): string => {
  const codeBlockRegex = /<pre><code class="language-(\w+)?">([\s\S]*?)<\/code><\/pre>/g
  let index = 0
  
  return html.replace(codeBlockRegex, (match, lang, code) => {
    const currentIndex = index++
    // 解码 HTML 实体
    const decodedCode = decodeHtmlEntities(code)
    // 存储代码内容用于复制
    return `<div class="code-block-wrapper" data-code-index="${currentIndex}">
      <div class="code-header">
        <span class="code-lang">${lang || 'code'}</span>
        <button class="code-copy-btn" data-code="${encodeURIComponent(decodedCode)}" data-index="${currentIndex}">
          ${codeCopyStates.value[currentIndex] === 'copied' ? '已复制' : '复制代码'}
        </button>
      </div>
      <pre><code class="language-${lang || ''}">${code}</code></pre>
    </div>`
  })
}

/**
 * 解码 HTML 实体
 * @param html - HTML 字符串
 * @returns 解码后的字符串
 */
const decodeHtmlEntities = (html: string): string => {
  const textarea = document.createElement('textarea')
  textarea.innerHTML = html
  return textarea.value
}

/**
 * 处理代码块点击事件
 * @param event - 点击事件
 */
const handleCodeClick = (event: MouseEvent): void => {
  const target = event.target as HTMLElement
  if (target.classList.contains('code-copy-btn')) {
    const code = decodeURIComponent(target.getAttribute('data-code') || '')
    const index = parseInt(target.getAttribute('data-index') || '0')
    copyCode(code, index)
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  configureMarked()
  
  // 添加代码块点击事件委托
  nextTick(() => {
    document.addEventListener('click', handleCodeClick)
  })
})
</script>

<template>
  <div
    :class="[
      'flex gap-3 group',
      isUser ? 'flex-row-reverse' : 'flex-row'
    ]"
  >
    <!-- 头像 -->
    <div
      :class="[
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        avatarBg
      ]"
    >
      <span class="text-sm font-medium">{{ roleName.charAt(0) }}</span>
    </div>

    <!-- 消息内容 -->
    <div
      :class="[
        'relative max-w-[80%] rounded-2xl px-4 py-3',
        bubbleClass,
        isUser ? 'rounded-tr-sm' : 'rounded-tl-sm'
      ]"
    >
      <!-- 消息内容区域 -->
      <div
        v-if="isAssistant"
        class="message-content prose prose-invert prose-sm max-w-none"
        v-html="processCodeBlocks(renderedContent)"
      ></div>
      <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>

      <!-- 消息元信息 -->
      <div
        :class="[
          'flex items-center gap-2 mt-2 text-xs',
          isUser ? 'text-primary-200' : 'text-secondary-400'
        ]"
      >
        <span>{{ formattedTime }}</span>
        
        <!-- Token 数量 -->
        <span v-if="message.metadata?.tokens" class="opacity-60">
          {{ message.metadata.tokens }} tokens
        </span>
        
        <!-- 延迟时间 -->
        <span v-if="message.metadata?.latency" class="opacity-60">
          {{ message.metadata.latency }}ms
        </span>
      </div>

      <!-- 操作按钮 -->
      <div
        :class="[
          'absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity',
          isUser ? 'left-2' : 'right-2'
        ]"
      >
        <div class="relative">
          <!-- 更多操作按钮 -->
          <button
            @click="toggleMenu"
            class="p-1.5 rounded-lg hover:bg-secondary-700/50 transition-colors"
            :title="'更多操作'"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
              />
            </svg>
          </button>

          <!-- 操作菜单 -->
          <Transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div
              v-if="showMenu"
              :class="[
                'absolute top-full mt-1 w-36 bg-secondary-800 border border-secondary-700 rounded-lg shadow-lg py-1 z-20',
                isUser ? 'right-0' : 'left-0'
              ]"
            >
              <!-- 复制按钮 -->
              <button
                @click="copyMessage"
                class="w-full px-3 py-2 text-left text-sm hover:bg-secondary-700 flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                <span>{{ copyState === 'copied' ? t('common.copied') : t('common.copy') }}</span>
              </button>

              <!-- 重试按钮（仅助手消息） -->
              <button
                v-if="isAssistant"
                @click="retryMessage"
                class="w-full px-3 py-2 text-left text-sm hover:bg-secondary-700 flex items-center gap-2"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span>{{ t('common.retry') }}</span>
              </button>

              <!-- 删除按钮 -->
              <button
                @click="deleteMessage"
                class="w-full px-3 py-2 text-left text-sm hover:bg-secondary-700 flex items-center gap-2 text-red-400"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                <span>{{ t('common.delete') }}</span>
              </button>
            </div>
          </Transition>
        </div>
      </div>

      <!-- 错误提示 -->
      <div
        v-if="message.metadata?.error"
        class="mt-2 p-2 bg-red-900/20 border border-red-800 rounded text-red-400 text-sm"
      >
        {{ message.metadata.error }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Markdown 内容样式 */
.message-content {
  @apply text-sm leading-relaxed;
}

.message-content :deep(p) {
  @apply mb-3 last:mb-0;
}

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4) {
  @apply font-bold mb-2 mt-4 first:mt-0;
}

.message-content :deep(h1) {
  @apply text-lg;
}

.message-content :deep(h2) {
  @apply text-base;
}

.message-content :deep(h3) {
  @apply text-sm;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  @apply mb-3 pl-4;
}

.message-content :deep(li) {
  @apply mb-1;
}

.message-content :deep(code) {
  @apply px-1.5 py-0.5 bg-secondary-900 rounded text-accent-400 font-mono text-xs;
}

.message-content :deep(a) {
  @apply text-primary-400 hover:underline;
}

.message-content :deep(blockquote) {
  @apply pl-3 border-l-2 border-secondary-600 text-secondary-400 italic;
}

/* 代码块样式 */
.message-content :deep(.code-block-wrapper) {
  @apply relative my-3 rounded-lg overflow-hidden bg-secondary-900;
}

.message-content :deep(.code-header) {
  @apply flex items-center justify-between px-3 py-2 bg-secondary-800 border-b border-secondary-700;
}

.message-content :deep(.code-lang) {
  @apply text-xs text-secondary-400 font-mono;
}

.message-content :deep(.code-copy-btn) {
  @apply px-2 py-1 text-xs bg-secondary-700 hover:bg-secondary-600 rounded transition-colors;
}

.message-content :deep(pre) {
  @apply p-3 overflow-x-auto m-0;
}

.message-content :deep(pre code) {
  @apply bg-transparent p-0 text-xs leading-relaxed;
}
</style>
