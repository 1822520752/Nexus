<script setup lang="ts">
/**
 * 聊天输入组件
 * 提供消息输入、发送功能和快捷键支持
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from '@/composables'
import { useSettingsStore } from '@/stores/settings'

// ==================== Props 定义 ====================

interface Props {
  /** 是否禁用输入 */
  disabled?: boolean
  /** 是否正在发送 */
  isSending?: boolean
  /** 占位符文本 */
  placeholder?: string
  /** 最大输入长度 */
  maxLength?: number
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  isSending: false,
  placeholder: '',
  maxLength: 4000
})

// ==================== Emits 定义 ====================

const emit = defineEmits<{
  /** 发送消息事件 */
  (e: 'send', content: string): void
  /** 输入内容变化事件 */
  (e: 'input', content: string): void
  /** 停止生成事件 */
  (e: 'stop'): void
}>()

// ==================== 组合式函数 ====================

const { t } = useI18n()
const settingsStore = useSettingsStore()

// ==================== 响应式状态 ====================

/**
 * 输入内容
 */
const inputContent = ref('')

/**
 * 文本框引用
 */
const textareaRef = ref<HTMLTextAreaElement | null>(null)

/**
 * 是否聚焦
 */
const isFocused = ref(false)

/**
 * 是否显示建议面板
 */
const showSuggestions = ref(false)

/**
 * 光标位置
 */
const cursorPosition = ref(0)

// ==================== 计算属性 ====================

/**
 * 占位符文本
 */
const placeholderText = computed(() => {
  return props.placeholder || t('chat.placeholder')
})

/**
 * 是否可以发送
 */
const canSend = computed(() => {
  return inputContent.value.trim().length > 0 && !props.disabled && !props.isSending
})

/**
 * 当前输入长度
 */
const inputLength = computed(() => inputContent.value.length)

/**
 * 是否超过最大长度
 */
const isOverLength = computed(() => inputLength.value > props.maxLength)

/**
 * 是否按回车发送
 */
const sendOnEnter = computed(() => settingsStore.settings.sendOnEnter)

// ==================== 方法 ====================

/**
 * 自动调整文本框高度
 */
const adjustTextareaHeight = (): void => {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
      const newHeight = Math.min(textareaRef.value.scrollHeight, 200)
      textareaRef.value.style.height = `${newHeight}px`
    }
  })
}

/**
 * 发送消息
 */
const sendMessage = (): void => {
  const content = inputContent.value.trim()
  if (!content || !canSend.value) return

  emit('send', content)
  inputContent.value = ''
  adjustTextareaHeight()
}

/**
 * 停止生成
 */
const stopGeneration = (): void => {
  emit('stop')
}

/**
 * 聚焦文本框
 */
const focusInput = (): void => {
  textareaRef.value?.focus()
}

/**
 * 处理输入事件
 */
const handleInput = (): void => {
  adjustTextareaHeight()
  emit('input', inputContent.value)
}

/**
 * 处理键盘事件
 * @param event - 键盘事件
 */
const handleKeydown = (event: KeyboardEvent): void => {
  // Ctrl+Enter 发送消息
  if (event.ctrlKey && event.key === 'Enter') {
    event.preventDefault()
    sendMessage()
    return
  }

  // Enter 发送消息（如果启用）
  if (sendOnEnter.value && event.key === 'Enter' && !event.shiftKey && !event.ctrlKey) {
    event.preventDefault()
    sendMessage()
    return
  }

  // Shift+Enter 换行
  if (event.key === 'Enter' && event.shiftKey) {
    // 默认行为，允许换行
    return
  }
}

/**
 * 处理粘贴事件
 * @param event - 粘贴事件
 */
const handlePaste = async (event: ClipboardEvent): Promise<void> => {
  const items = event.clipboardData?.items
  if (!items) return

  // 检查是否有图片
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      // TODO: 处理图片粘贴
      console.log('粘贴图片:', item)
    }
  }
}

/**
 * 插入文本
 * @param text - 要插入的文本
 */
const insertText = (text: string): void => {
  if (!textareaRef.value) return

  const start = textareaRef.value.selectionStart
  const end = textareaRef.value.selectionEnd
  const content = inputContent.value

  inputContent.value = content.substring(0, start) + text + content.substring(end)
  
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.selectionStart = textareaRef.value.selectionEnd = start + text.length
      focusInput()
    }
  })
}

/**
 * 清空输入
 */
const clearInput = (): void => {
  inputContent.value = ''
  adjustTextareaHeight()
}

// ==================== 监听器 ====================

/**
 * 监听输入内容变化
 */
watch(inputContent, () => {
  adjustTextareaHeight()
})

// ==================== 生命周期 ====================

onMounted(() => {
  // 监听快捷键事件
  window.addEventListener('shortcut:send-message', sendMessage)
  
  // 自动聚焦
  focusInput()
})

onUnmounted(() => {
  window.removeEventListener('shortcut:send-message', sendMessage)
})

// 暴露方法给父组件
defineExpose({
  focusInput,
  clearInput,
  insertText
})
</script>

<template>
  <div class="border-t border-secondary-700 bg-secondary-800/50 p-4">
    <div class="max-w-4xl mx-auto">
      <!-- 输入区域 -->
      <div
        :class="[
          'relative flex items-end gap-3 p-3 rounded-xl border transition-all duration-200',
          isFocused
            ? 'border-primary-500 bg-secondary-800'
            : 'border-secondary-700 bg-secondary-800/50',
          isOverLength ? 'border-red-500' : ''
        ]"
      >
        <!-- 文本输入框 -->
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="inputContent"
            :placeholder="placeholderText"
            :disabled="disabled"
            :maxlength="maxLength"
            class="w-full bg-transparent text-white placeholder-secondary-500 resize-none outline-none text-sm leading-relaxed"
            rows="1"
            @input="handleInput"
            @keydown="handleKeydown"
            @paste="handlePaste"
            @focus="isFocused = true"
            @blur="isFocused = false"
          ></textarea>
        </div>

        <!-- 操作按钮区域 -->
        <div class="flex items-center gap-2 flex-shrink-0">
          <!-- 字数统计 -->
          <span
            v-if="inputLength > 0"
            :class="[
              'text-xs',
              isOverLength ? 'text-red-400' : 'text-secondary-500'
            ]"
          >
            {{ inputLength }}/{{ maxLength }}
          </span>

          <!-- 停止生成按钮 -->
          <button
            v-if="isSending"
            @click="stopGeneration"
            class="p-2 rounded-lg bg-red-600 hover:bg-red-700 transition-colors"
            :title="'停止生成'"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
              />
            </svg>
          </button>

          <!-- 发送按钮 -->
          <button
            v-else
            @click="sendMessage"
            :disabled="!canSend || isOverLength"
            :class="[
              'p-2 rounded-lg transition-all duration-200',
              canSend && !isOverLength
                ? 'bg-primary-600 hover:bg-primary-700 text-white'
                : 'bg-secondary-700 text-secondary-500 cursor-not-allowed'
            ]"
            :title="t('chat.send')"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- 快捷键提示 -->
      <div class="flex items-center justify-between mt-2 text-xs text-secondary-500">
        <div class="flex items-center gap-4">
          <span v-if="sendOnEnter">
            <kbd class="px-1.5 py-0.5 bg-secondary-700 rounded">Enter</kbd>
            发送，
            <kbd class="px-1.5 py-0.5 bg-secondary-700 rounded">Shift+Enter</kbd>
            换行
          </span>
          <span v-else>
            <kbd class="px-1.5 py-0.5 bg-secondary-700 rounded">Ctrl+Enter</kbd>
            发送
          </span>
        </div>
        
        <span v-if="isSending" class="flex items-center gap-1 text-primary-400">
          <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ t('chat.sending') }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 键盘按键样式 */
kbd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
