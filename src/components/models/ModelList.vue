/**
 * 模型列表组件
 * 显示所有模型配置的列表视图
 */
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useModelsStore } from '@/stores/models'
import ModelCard from './ModelCard.vue'
import ModelConfigDialog from './ModelConfigDialog.vue'
import type { ModelConfig } from '@/types'

// Store
const modelsStore = useModelsStore()

// ==================== 响应式状态 ====================

/**
 * 是否显示配置对话框
 */
const showConfigDialog = ref(false)

/**
 * 当前编辑的模型
 */
const editingModel = ref<ModelConfig | null>(null)

/**
 * 筛选条件
 */
const filterProvider = ref<string>('')

// ==================== 计算属性 ====================

/**
 * 筛选后的模型列表
 */
const filteredModels = computed(() => {
  if (!filterProvider.value) {
    return modelsStore.models
  }
  return modelsStore.models.filter(m => m.provider === filterProvider.value)
})

/**
 * 提供商选项
 */
const providerOptions = computed(() => {
  const options = [{ value: '', label: '全部' }]
  for (const [key, config] of Object.entries(modelsStore.providers)) {
    options.push({ value: key, label: config.name })
  }
  return options
})

// ==================== 方法 ====================

/**
 * 打开添加模型对话框
 */
const handleAddModel = () => {
  editingModel.value = null
  showConfigDialog.value = true
}

/**
 * 打开编辑模型对话框
 * @param model - 要编辑的模型
 */
const handleEditModel = (model: ModelConfig) => {
  editingModel.value = model
  showConfigDialog.value = true
}

/**
 * 删除模型
 * @param modelId - 模型 ID
 */
const handleDeleteModel = async (modelId: number) => {
  await modelsStore.deleteModel(modelId)
}

/**
 * 切换模型启用状态
 * @param modelId - 模型 ID
 */
const handleToggleModel = async (modelId: number) => {
  await modelsStore.toggleModel(modelId)
}

/**
 * 设置默认模型
 * @param modelId - 模型 ID
 */
const handleSetDefault = async (modelId: number) => {
  await modelsStore.setDefaultModel(modelId)
}

/**
 * 对话框保存成功
 * @param model - 保存的模型
 */
const handleDialogSuccess = (model: ModelConfig) => {
  console.log('模型保存成功:', model)
}

/**
 * 刷新模型列表
 */
const refreshModels = async () => {
  await modelsStore.fetchModels()
}

// ==================== 生命周期 ====================

onMounted(() => {
  modelsStore.initialize()
})
</script>

<template>
  <div class="space-y-4">
    <!-- 头部工具栏 -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
          模型管理
        </h2>
        <span class="text-sm text-gray-500 dark:text-gray-400">
          共 {{ modelsStore.totalModels }} 个模型，{{ modelsStore.enabledCount }} 个已启用
        </span>
      </div>
      
      <div class="flex items-center gap-3">
        <!-- 筛选 -->
        <select
          v-model="filterProvider"
          class="px-3 py-1.5 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          <option v-for="option in providerOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

        <!-- 刷新 -->
        <button
          @click="refreshModels"
          :disabled="modelsStore.isLoading"
          class="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
          title="刷新"
        >
          <svg
            class="w-5 h-5"
            :class="{ 'animate-spin': modelsStore.isLoading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- 添加模型 -->
        <button
          @click="handleAddModel"
          class="flex items-center gap-1 px-3 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          添加模型
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div
      v-if="modelsStore.error"
      class="p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-md"
    >
      {{ modelsStore.error }}
    </div>

    <!-- 加载状态 -->
    <div v-if="modelsStore.isLoading && modelsStore.models.length === 0" class="flex items-center justify-center py-12">
      <svg class="w-8 h-8 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="ml-2 text-gray-600 dark:text-gray-400">加载中...</span>
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="!modelsStore.isLoading && modelsStore.models.length === 0"
      class="flex flex-col items-center justify-center py-12 text-center"
    >
      <svg class="w-16 h-16 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
      <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">暂无模型配置</h3>
      <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
        点击"添加模型"按钮配置您的第一个 AI 模型
      </p>
      <button
        @click="handleAddModel"
        class="mt-4 px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md"
      >
        添加模型
      </button>
    </div>

    <!-- 模型卡片网格 -->
    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <ModelCard
        v-for="model in filteredModels"
        :key="model.id"
        :model="model"
        @edit="handleEditModel"
        @delete="handleDeleteModel"
        @toggle="handleToggleModel"
        @set-default="handleSetDefault"
      />
    </div>

    <!-- 配置对话框 -->
    <ModelConfigDialog
      v-model:visible="showConfigDialog"
      :model="editingModel"
      @success="handleDialogSuccess"
    />
  </div>
</template>
