/**
 * 模型卡片组件
 * 显示单个模型配置的卡片视图
 */
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useModelsStore } from '@/stores/models'
import type { ModelConfig, ModelStatus } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 模型配置数据
   */
  model: ModelConfig
}

const props = defineProps<Props>()

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'edit', model: ModelConfig): void
  (e: 'delete', modelId: number): void
  (e: 'toggle', modelId: number): void
  (e: 'setDefault', modelId: number): void
}>()

// Store
const modelsStore = useModelsStore()

// ==================== 响应式状态 ====================

/**
 * 模型状态
 */
const modelStatus = ref<ModelStatus | null>(null)

/**
 * 是否正在检查状态
 */
const isCheckingStatus = ref(false)

/**
 * 是否正在测试连接
 */
const isTesting = ref(false)

/**
 * 测试结果
 */
const testResult = ref<{ success: boolean; message: string } | null>(null)

// ==================== 计算属性 ====================

/**
 * 提供商显示名称
 */
const providerName = computed(() => {
  const config = modelsStore.providers[props.model.provider]
  return config?.name || props.model.provider
})

/**
 * 状态颜色类
 */
const statusColorClass = computed(() => {
  if (!modelStatus.value) return 'bg-gray-400'
  switch (modelStatus.value.status) {
    case 'available':
      return 'bg-green-500'
    case 'unavailable':
      return 'bg-yellow-500'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
})

/**
 * 状态文本
 */
const statusText = computed(() => {
  if (!modelStatus.value) return '未检测'
  switch (modelStatus.value.status) {
    case 'available':
      return '可用'
    case 'unavailable':
      return '不可用'
    case 'error':
      return '错误'
    case 'not_found':
      return '未找到'
    default:
      return '未知'
  }
})

/**
 * 提供商图标
 */
const providerIcon = computed(() => {
  switch (props.model.provider) {
    case 'ollama':
      return '🦙'
    case 'openai':
      return '🤖'
    case 'deepseek':
      return '🔮'
    case 'anthropic':
      return '🧠'
    default:
      return '⚙️'
  }
})

// ==================== 方法 ====================

/**
 * 检查模型状态
 */
const checkStatus = async () => {
  isCheckingStatus.value = true
  try {
    modelStatus.value = await modelsStore.fetchModelStatus(props.model.id)
  } finally {
    isCheckingStatus.value = false
  }
}

/**
 * 测试连接
 */
const testConnection = async () => {
  isTesting.value = true
  testResult.value = null
  try {
    const result = await modelsStore.testModelConnection(props.model.id)
    testResult.value = {
      success: result?.success ?? false,
      message: result?.message ?? '测试完成',
    }
    // 3秒后清除结果
    setTimeout(() => {
      testResult.value = null
    }, 3000)
  } finally {
    isTesting.value = false
  }
}

/**
 * 编辑模型
 */
const handleEdit = () => {
  emit('edit', props.model)
}

/**
 * 删除模型
 */
const handleDelete = () => {
  if (confirm(`确定要删除模型 "${props.model.name}" 吗？`)) {
    emit('delete', props.model.id)
  }
}

/**
 * 切换启用状态
 */
const handleToggle = () => {
  emit('toggle', props.model.id)
}

/**
 * 设为默认
 */
const handleSetDefault = () => {
  emit('setDefault', props.model.id)
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 自动检查状态
  checkStatus()
})
</script>

<template>
  <div
    class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-700"
    :class="{ 'ring-2 ring-blue-500': model.is_default }"
  >
    <!-- 卡片头部 -->
    <div class="flex items-start justify-between p-4 border-b dark:border-gray-700">
      <div class="flex items-center gap-3">
        <span class="text-2xl">{{ providerIcon }}</span>
        <div>
          <h3 class="font-semibold text-gray-900 dark:text-white">
            {{ model.name }}
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ providerName }}
          </p>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <!-- 默认标记 -->
        <span
          v-if="model.is_default"
          class="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 dark:bg-blue-900 dark:text-blue-300 rounded"
        >
          默认
        </span>
        
        <!-- 状态指示器 -->
        <div class="flex items-center gap-1">
          <span
            class="w-2 h-2 rounded-full"
            :class="statusColorClass"
            :title="statusText"
          ></span>
          <span class="text-xs text-gray-500 dark:text-gray-400">
            {{ statusText }}
          </span>
        </div>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="p-4 space-y-3">
      <!-- 基本信息 -->
      <div class="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span class="text-gray-500 dark:text-gray-400">最大 Token:</span>
          <span class="ml-1 text-gray-900 dark:text-white">{{ model.max_tokens }}</span>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">温度:</span>
          <span class="ml-1 text-gray-900 dark:text-white">{{ model.temperature }}</span>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">上下文窗口:</span>
          <span class="ml-1 text-gray-900 dark:text-white">{{ model.context_window }}</span>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">类型:</span>
          <span class="ml-1 text-gray-900 dark:text-white">{{ model.model_type }}</span>
        </div>
      </div>

      <!-- Base URL -->
      <div v-if="model.base_url" class="text-sm">
        <span class="text-gray-500 dark:text-gray-400">URL:</span>
        <span class="ml-1 text-gray-900 dark:text-white truncate block">{{ model.base_url }}</span>
      </div>

      <!-- 测试结果 -->
      <div
        v-if="testResult"
        class="p-2 rounded text-sm"
        :class="testResult.success ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'"
      >
        {{ testResult.message }}
      </div>
    </div>

    <!-- 卡片底部操作 -->
    <div class="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 rounded-b-lg">
      <div class="flex items-center gap-2">
        <!-- 启用/禁用开关 -->
        <button
          @click="handleToggle"
          class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
          :class="model.is_active ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="model.is_active ? 'translate-x-4' : 'translate-x-1'"
          />
        </button>
        <span class="text-sm text-gray-600 dark:text-gray-400">
          {{ model.is_active ? '已启用' : '已禁用' }}
        </span>
      </div>

      <div class="flex items-center gap-1">
        <!-- 刷新状态 -->
        <button
          @click="checkStatus"
          :disabled="isCheckingStatus"
          class="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          title="刷新状态"
        >
          <svg
            class="w-4 h-4"
            :class="{ 'animate-spin': isCheckingStatus }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- 测试连接 -->
        <button
          @click="testConnection"
          :disabled="isTesting"
          class="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          title="测试连接"
        >
          <svg
            class="w-4 h-4"
            :class="{ 'animate-pulse': isTesting }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </button>

        <!-- 设为默认 -->
        <button
          v-if="!model.is_default"
          @click="handleSetDefault"
          class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          title="设为默认"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </button>

        <!-- 编辑 -->
        <button
          @click="handleEdit"
          class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          title="编辑"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>

        <!-- 删除 -->
        <button
          @click="handleDelete"
          class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          title="删除"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
