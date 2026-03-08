/**
 * 模型配置对话框组件
 * 用于添加和编辑 AI 模型配置
 */
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useModelsStore } from '@/stores/models'
import type { ModelConfig, CreateModelConfigRequest, ModelProvider, ProviderConfig, AvailableModel } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 是否显示对话框
   */
  visible: boolean
  /**
   * 要编辑的模型（编辑模式）
   */
  model?: ModelConfig | null
}

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'success', model: ModelConfig): void
  (e: 'cancel'): void
}>()

const props = defineProps<Props>()

// Store
const modelsStore = useModelsStore()

// ==================== 响应式状态 ====================

/**
 * 表单数据
 */
const formData = ref<CreateModelConfigRequest>({
  name: '',
  provider: 'ollama',
  api_key: '',
  base_url: '',
  model_type: 'chat',
  is_default: false,
  max_tokens: 4096,
  temperature: 0.7,
  context_window: 8192,
})

/**
 * 是否显示 API Key
 */
const showApiKey = ref(false)

/**
 * 是否正在加载
 */
const isLoading = ref(false)

/**
 * 错误信息
 */
const errorMessage = ref('')

/**
 * 可用模型列表
 */
const availableModels = ref<AvailableModel[]>([])

/**
 * 是否正在加载可用模型
 */
const isLoadingModels = ref(false)

// ==================== 计算属性 ====================

/**
 * 是否为编辑模式
 */
const isEditMode = computed(() => !!props.model)

/**
 * 对话框标题
 */
const dialogTitle = computed(() => isEditMode.value ? '编辑模型配置' : '添加模型配置')

/**
 * 当前选中的提供商配置
 */
const currentProviderConfig = computed((): ProviderConfig | undefined => {
  return modelsStore.providers[formData.value.provider]
})

/**
 * 是否需要 API Key
 */
const requiresApiKey = computed(() => {
  return currentProviderConfig.value?.requires_api_key ?? false
})

/**
 * 默认 Base URL
 */
const defaultBaseUrl = computed(() => {
  return currentProviderConfig.value?.default_base_url ?? ''
})

// ==================== 监听器 ====================

/**
 * 监听对话框显示状态
 */
watch(() => props.visible, (newVal) => {
  if (newVal) {
    resetForm()
    if (props.model) {
      // 编辑模式：填充表单
      formData.value = {
        name: props.model.name,
        provider: props.model.provider,
        api_key: '', // API Key 不回显
        base_url: props.model.base_url || '',
        model_type: props.model.model_type,
        is_default: props.model.is_default,
        max_tokens: props.model.max_tokens,
        temperature: props.model.temperature,
        context_window: props.model.context_window,
        config: props.model.config,
      }
    }
    loadAvailableModels()
  }
})

/**
 * 监听提供商变化
 */
watch(() => formData.value.provider, () => {
  // 自动填充默认 Base URL
  if (!formData.value.base_url && defaultBaseUrl.value) {
    formData.value.base_url = defaultBaseUrl.value
  }
  loadAvailableModels()
})

// ==================== 方法 ====================

/**
 * 重置表单
 */
const resetForm = () => {
  formData.value = {
    name: '',
    provider: 'ollama',
    api_key: '',
    base_url: '',
    model_type: 'chat',
    is_default: false,
    max_tokens: 4096,
    temperature: 0.7,
    context_window: 8192,
  }
  showApiKey.value = false
  errorMessage.value = ''
  availableModels.value = []
}

/**
 * 加载可用模型列表
 */
const loadAvailableModels = async () => {
  isLoadingModels.value = true
  try {
    availableModels.value = await modelsStore.fetchProviderModels(formData.value.provider)
  } finally {
    isLoadingModels.value = false
  }
}

/**
 * 选择可用模型
 * @param model - 可用模型
 */
const selectAvailableModel = (model: AvailableModel) => {
  formData.value.name = model.name
}

/**
 * 验证表单
 */
const validateForm = (): boolean => {
  if (!formData.value.name.trim()) {
    errorMessage.value = '请输入模型名称'
    return false
  }

  if (requiresApiKey.value && !formData.value.api_key?.trim()) {
    errorMessage.value = '请输入 API Key'
    return false
  }

  return true
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    let result: ModelConfig | null

    if (isEditMode.value && props.model) {
      // 编辑模式
      result = await modelsStore.updateModel(props.model.id, {
        name: formData.value.name,
        api_key: formData.value.api_key || undefined,
        base_url: formData.value.base_url || undefined,
        is_default: formData.value.is_default,
        max_tokens: formData.value.max_tokens,
        temperature: formData.value.temperature,
        context_window: formData.value.context_window,
        config: formData.value.config,
      })
    } else {
      // 创建模式
      result = await modelsStore.createModel(formData.value)
    }

    if (result) {
      emit('success', result)
      handleClose()
    }
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    isLoading.value = false
  }
}

/**
 * 关闭对话框
 */
const handleClose = () => {
  emit('update:visible', false)
  emit('cancel')
}

/**
 * 测试连接
 */
const handleTestConnection = async () => {
  if (!props.model) return

  isLoading.value = true
  try {
    const result = await modelsStore.testModelConnection(props.model.id)
    if (result?.success) {
      alert('连接测试成功！')
    } else {
      alert(`连接测试失败：${result?.message || '未知错误'}`)
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
      <!-- 头部 -->
      <div class="flex items-center justify-between px-6 py-4 border-b dark:border-gray-700">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
          {{ dialogTitle }}
        </h2>
        <button
          @click="handleClose"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- 表单内容 -->
      <div class="px-6 py-4 space-y-4">
        <!-- 错误提示 -->
        <div v-if="errorMessage" class="p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-md">
          {{ errorMessage }}
        </div>

        <!-- 提供商选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            提供商
          </label>
          <select
            v-model="formData.provider"
            :disabled="isEditMode"
            class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option v-for="(config, key) in modelsStore.providers" :key="key" :value="key">
              {{ config.name }}
            </option>
          </select>
          <p v-if="currentProviderConfig" class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ currentProviderConfig.description }}
          </p>
        </div>

        <!-- 模型名称 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            模型名称 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="例如: gpt-4, llama2, deepseek-chat"
            class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
          
          <!-- 可用模型列表（Ollama） -->
          <div v-if="availableModels.length > 0 && !isEditMode" class="mt-2">
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">可用模型：</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="model in availableModels"
                :key="model.name"
                @click="selectAvailableModel(model)"
                class="px-2 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
              >
                {{ model.name }}
              </button>
            </div>
          </div>
        </div>

        <!-- API Key -->
        <div v-if="requiresApiKey">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            API Key <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              v-model="formData.api_key"
              :type="showApiKey ? 'text' : 'password'"
              placeholder="请输入 API Key"
              class="w-full px-3 py-2 pr-10 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <button
              @click="showApiKey = !showApiKey"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <svg v-if="showApiKey" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            API Key 将加密存储
          </p>
        </div>

        <!-- Base URL -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            API 基础 URL
          </label>
          <input
            v-model="formData.base_url"
            type="text"
            :placeholder="defaultBaseUrl || '可选'"
            class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        </div>

        <!-- 高级设置 -->
        <details class="border rounded-md dark:border-gray-700">
          <summary class="px-4 py-2 cursor-pointer text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
            高级设置
          </summary>
          <div class="px-4 py-3 space-y-4">
            <!-- 最大 Token 数 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                最大 Token 数
              </label>
              <input
                v-model.number="formData.max_tokens"
                type="number"
                min="1"
                class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>

            <!-- 温度参数 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                温度参数 (0-2)
              </label>
              <input
                v-model.number="formData.temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>

            <!-- 上下文窗口 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                上下文窗口大小
              </label>
              <input
                v-model.number="formData.context_window"
                type="number"
                min="1"
                class="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>

            <!-- 设为默认 -->
            <div class="flex items-center">
              <input
                v-model="formData.is_default"
                type="checkbox"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                设为默认模型
              </label>
            </div>
          </div>
        </details>
      </div>

      <!-- 底部按钮 -->
      <div class="flex items-center justify-between px-6 py-4 border-t dark:border-gray-700">
        <button
          v-if="isEditMode"
          @click="handleTestConnection"
          :disabled="isLoading"
          class="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          测试连接
        </button>
        <div v-else></div>
        
        <div class="flex gap-3">
          <button
            @click="handleClose"
            class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
          >
            取消
          </button>
          <button
            @click="handleSubmit"
            :disabled="isLoading"
            class="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
          >
            {{ isLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
