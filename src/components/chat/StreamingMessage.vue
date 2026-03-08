<script setup lang="ts">
/**
 * 流式响应消息组件
 * 显示 AI 流式输出的内容，支持实时渲染
 */
import { ref, computed, watch, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

// ==================== Props 定义 ====================

interface Props {
  /** 流式内容 */
  content: string
  /** 是否显示光标 */
  showCursor?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showCursor: true
})

// ==================== 响应式状态 ====================

/**
 * 是否正在打字
 */
const isTyping = ref(true)

// ==================== 计算属性 ====================

/**
 * 渲染后的 HTML 内容
 */
const renderedContent = computed(() => {
  return renderMarkdown(props.content)
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
    // 对于不完整的 Markdown，尝试补全
    let processedContent = content
    
    // 补全未闭合的代码块
    const codeBlockCount = (content.match(/```/g) || []).length
    if (codeBlockCount % 2 !== 0) {
      processedContent += '\n```'
    }
    
    return marked.parse(processedContent) as string
  } catch {
    return content
  }
}

// ==================== 监听器 ====================

/**
 * 监听内容变化
 */
watch(() => props.content, () => {
  isTyping.value = true
})

// ==================== 生命周期 ====================

onMounted(() => {
  configureMarked()
})
</script>

<template>
  <div class="flex gap-3">
    <!-- AI 头像 -->
    <div class="w-8 h-8 rounded-full bg-accent-600 flex items-center justify-center flex-shrink-0">
      <span class="text-sm font-medium">AI</span>
    </div>

    <!-- 内容区域 -->
    <div class="flex-1 bg-secondary-800 border border-secondary-700 rounded-2xl rounded-tl-sm px-4 py-3">
      <!-- 渲染的内容 -->
      <div
        class="message-content prose prose-invert prose-sm max-w-none"
        v-html="renderedContent"
      ></div>

      <!-- 打字光标 -->
      <span
        v-if="showCursor && isTyping"
        class="inline-block w-2 h-4 bg-primary-500 ml-1 animate-pulse"
      ></span>
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

.message-content :deep(code) {
  @apply px-1.5 py-0.5 bg-secondary-900 rounded text-accent-400 font-mono text-xs;
}

.message-content :deep(pre) {
  @apply my-3 p-3 rounded-lg bg-secondary-900 overflow-x-auto;
}

.message-content :deep(pre code) {
  @apply bg-transparent p-0;
}

/* 光标动画 */
@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

.animate-pulse {
  animation: blink 1s infinite;
}
</style>
