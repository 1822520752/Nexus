/**
 * 记忆编辑组件
 * 支持创建和编辑记忆，包括内容编辑、类型切换、重要性调整和删除功能
 */
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMemoryStore } from '@/stores/memory'
import type { Memory, MemoryType, CreateMemoryRequest, UpdateMemoryRequest } from '@/types'
import { memoryTypeConfig } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 要编辑的记忆，为空则创建新记忆
   */
  memory?: Memory | null
  /**
   * 是否显示对话框
   */
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  memory: null,
  visible: false
})

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'save', memory: Memory): void
  (e: 'delete', memoryId: string): void
  (e: 'cancel'): void
}>()

// Store
const memoryStore = useMemoryStore()

// ==================== 响应式状态 ====================

/**
 * 表单数据
 */
const formData = ref({
  memoryType: 'instant' as MemoryType,
  content: '',
  importance: 5
})

/**
 * 是否正在提交
 */
const isSubmitting = ref(false)

/**
 * 表单验证错误
 */
const formErrors = ref<Record<string, string>>({})

/**
 * 显示删除确认对话框
 */
const showDeleteConfirm = ref(false)

// ==================== 计算属性 ====================

/**
 * 是否为编辑模式
 */
const isEditMode = computed(() => !!props.memory)

/**
 * 对话框标题
 */
const dialogTitle = computed(() =>
  isEditMode.value ? '编辑记忆' : '新建记忆'
)

/**
 * 记忆类型选项
 */
const memoryTypeOptions = computed(() => {
  return Object.entries(memoryTypeConfig).map(([key, config]) => ({
    value: key as MemoryType,
    label: config.label,
    description: config.description,
    color: config.color
  }))
})

/**
 * 重要性等级描述
 */
const importanceLevel = computed(() => {
  const value = formData.value.importance
  if (value >= 9) return { label: '极高', color: 'text-red-500' }
  if (value >= 7) return { label: '高', color: 'text-orange-500' }
  if (value >= 5) return { label: '中', color: 'text-yellow-500' }
  if (value >= 3) return { label: '低', color: 'text-blue-500' }
  return { label: '极低', color: 'text-gray-500' }
})

// ==================== 方法 ====================

/**
 * 验证表单
 */
const validateForm = (): boolean => {
  formErrors.value = {}

  if (!formData.value.content.trim()) {
    formErrors.value.content = '请输入记忆内容'
  } else if (formData.value.content.length > 10000) {
    formErrors.value.content = '记忆内容不能超过 10000 个字符'
  }

  if (formData.value.importance < 1 || formData.value.importance > 10) {
    formErrors.value.importance = '重要性必须在 1-10 之间'
  }

  return Object.keys(formErrors.value).length === 0
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!validateForm()) return

  isSubmitting.value = true

  try {
    if (isEditMode.value && props.memory) {
      // 更新记忆
      const updates: UpdateMemoryRequest = {
        memoryType: formData.value.memoryType,
        content: formData.value.content,
        importance: formData.value.importance
      }
      const updatedMemory = await memoryStore.updateMemory(props.memory.id, updates)
      if (updatedMemory) {
        emit('save', updatedMemory)
        handleClose()
      }
    } else {
      // 创建记忆
      const createData: CreateMemoryRequest = {
        memoryType: formData.value.memoryType,
        content: formData.value.content,
        importance: formData.value.importance
      }
      const newMemory = await memoryStore.createMemory(createData)
      if (newMemory) {
        emit('save', newMemory)
        handleClose()
      }
    }
  } catch (error) {
    console.error('保存记忆失败:', error)
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 处理删除
 */
const handleDelete = () => {
  showDeleteConfirm.value = true
}

/**
 * 确认删除
 */
const confirmDelete = async () => {
  if (!props.memory) return

  try {
    const success = await memoryStore.deleteMemory(props.memory.id)
    if (success) {
      emit('delete', props.memory.id)
      handleClose()
    }
  } catch (error) {
    console.error('删除记忆失败:', error)
  } finally {
    showDeleteConfirm.value = false
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  emit('update:visible', false)
  emit('cancel')
  resetForm()
}

/**
 * 重置表单
 */
const resetForm = () => {
  formData.value = {
    memoryType: 'instant',
    content: '',
    importance: 5
  }
  formErrors.value = {}
}

/**
 * 初始化表单数据
 */
const initFormData = () => {
  if (props.memory) {
    formData.value = {
      memoryType: props.memory.memoryType,
      content: props.memory.content,
      importance: props.memory.importance
    }
  } else {
    resetForm()
  }
}

// ==================== 监听器 ====================

// 监听 memory 变化，初始化表单
watch(() => props.memory, () => {
  initFormData()
}, { immediate: true })

// 监听 visible 变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    initFormData()
  }
})
</script>

<template>
  <!-- 编辑对话框 -->
  <div
    v-if="visible"
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    @click.self="handleClose"
  >
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- 对话框头部 -->
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ dialogTitle }}
        </h3>
        <button
          @click="handleClose"
          class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- 对话框内容 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- 记忆类型选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            记忆类型
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="option in memoryTypeOptions"
              :key="option.value"
              @click="formData.memoryType = option.value"
              class="p-3 rounded-lg border-2 transition-all text-left"
              :class="formData.memoryType === option.value
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'"
            >
              <div class="font-medium text-gray-900 dark:text-white">
                {{ option.label }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {{ option.description }}
              </div>
            </button>
          </div>
        </div>

        <!-- 记忆内容 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            记忆内容 <span class="text-red-500">*</span>
          </label>
          <textarea
            v-model="formData.content"
            rows="6"
            class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            :class="formErrors.content ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'"
            placeholder="请输入记忆内容..."
          ></textarea>
          <div class="flex justify-between mt-1">
            <span v-if="formErrors.content" class="text-sm text-red-500">
              {{ formErrors.content }}
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-400 ml-auto">
              {{ formData.content.length }} / 10000
            </span>
          </div>
        </div>

        <!-- 重要性调整 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            重要性
            <span :class="importanceLevel.color" class="ml-2">
              ({{ importanceLevel.label }})
            </span>
          </label>
          <div class="flex items-center gap-4">
            <input
              v-model.number="formData.importance"
              type="range"
              min="1"
              max="10"
              step="1"
              class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <input
              v-model.number="formData.importance"
              type="number"
              min="1"
              max="10"
              class="w-16 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center"
            />
          </div>
          <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
            <span>1 (极低)</span>
            <span>5 (中等)</span>
            <span>10 (极高)</span>
          </div>
        </div>

        <!-- 元数据预览（编辑模式） -->
        <div v-if="isEditMode && memory?.metadata" class="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
          <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            元数据
          </div>
          <pre class="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{{ JSON.stringify(memory.metadata, null, 2) }}</pre>
        </div>
      </div>

      <!-- 对话框底部 -->
      <div class="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
        <!-- 删除按钮（仅编辑模式） -->
        <button
          v-if="isEditMode"
          @click="handleDelete"
          class="px-4 py-2 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 border border-red-600 dark:border-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          删除记忆
        </button>
        <div v-else></div>

        <!-- 操作按钮 -->
        <div class="flex items-center gap-3">
          <button
            @click="handleClose"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            取消
          </button>
          <button
            @click="handleSubmit"
            :disabled="isSubmitting || !formData.content.trim()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg
              v-if="isSubmitting"
              class="animate-spin w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isEditMode ? '保存更改' : '创建记忆' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 删除确认对话框 -->
  <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
      <div class="flex items-center gap-3 mb-4">
        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
          <svg class="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">确认删除</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">此操作无法撤销</p>
        </div>
      </div>
      <p class="text-gray-600 dark:text-gray-400 mb-4">
        确定要删除这条记忆吗？删除后将无法恢复。
      </p>
      <div class="flex justify-end gap-3">
        <button
          @click="showDeleteConfirm = false"
          class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          取消
        </button>
        <button
          @click="confirmDelete"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
        >
          确认删除
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义滑块样式 */
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input[type="range"]::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
