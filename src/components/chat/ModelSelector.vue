/**
 * 模型选择下拉组件
 * 用于在聊天界面快速切换当前使用的模型
 */
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useModelsStore } from '@/stores/models'
import type { ModelConfig, ModelStatus } from '@/types'

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'change', model: ModelConfig): void
}>()

// Store
const modelsStore = useModelsStore()

// ==================== 响应式状态 ====================

/**
 * 是否展开下拉菜单
 */
const isOpen = ref(false)

/**
 * 下拉菜单引用
 */
const dropdownRef = ref<HTMLElement | null>(null)

// ==================== 计算属性 ====================

/**
 * 当前选中的模型
 */
const selectedModel = computed(() => modelsStore.currentModel)

/**
 * 已启用的模型列表
 */
const enabledModels = computed(() => modelsStore.enabledModels)

/**
 * 提供商图标
 */
const getProviderIcon = (provider: string): string => {
  switch (provider) {
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
}

/**
 * 获取模型状态颜色
 */
const getStatusColor = (modelId: number): string => {
  const status = modelsStore.modelStatusCache[modelId]
  if (!status) return 'bg-gray-400'
  switch (status.status) {
    case 'available':
      return 'bg-green-500'
    case 'unavailable':
      return 'bg-yellow-500'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
}

// ==================== 方法 ====================

/**
 * 选择模型
 * @param model - 选中的模型
 */
const selectModel = (model: ModelConfig) => {
  modelsStore.setCurrentModel(model.id)
  emit('change', model)
  isOpen.value = false
}

/**
 * 切换下拉菜单
 */
const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

/**
 * 点击外部关闭下拉菜单
 * @param event - 点击事件
 */
const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

/**
 * 检查模型状态
 * @param modelId - 模型 ID
 */
const checkModelStatus = async (modelId: number) => {
  await modelsStore.fetchModelStatus(modelId)
}

// ==================== 生命周期 ====================

onMounted(() => {
  // 添加点击外部事件监听
  document.addEventListener('click', handleClickOutside)
  
  // 初始化模型列表
  if (modelsStore.models.length === 0) {
    modelsStore.initialize()
  }
})

// 清理事件监听
watch(isOpen, (newVal) => {
  if (newVal) {
    // 展开时检查所有模型状态
    enabledModels.value.forEach(model => {
      if (!modelsStore.modelStatusCache[model.id]) {
        checkModelStatus(model.id)
      }
    })
  }
})
</script>

<template>
  <div ref="dropdownRef" class="relative inline-block text-left">
    <!-- 触发按钮 -->
    <button
      @click="toggleDropdown"
      class="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <span v-if="selectedModel" class="flex items-center gap-2">
        <span class="text-lg">{{ getProviderIcon(selectedModel.provider) }}</span>
        <span class="font-medium text-gray-900 dark:text-white">{{ selectedModel.name }}</span>
        <span
          class="w-2 h-2 rounded-full"
          :class="getStatusColor(selectedModel.id)"
          :title="modelsStore.modelStatusCache[selectedModel.id]?.message || '未检测'"
        ></span>
      </span>
      <span v-else class="text-gray-500 dark:text-gray-400">选择模型</span>
      
      <svg
        class="w-4 h-4 text-gray-400 ml-1"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- 下拉菜单 -->
    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute left-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
      >
        <!-- 空状态 -->
        <div
          v-if="enabledModels.length === 0"
          class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center"
        >
          暂无可用模型
        </div>

        <!-- 模型列表 -->
        <div v-else class="py-1 max-h-64 overflow-y-auto">
          <button
            v-for="model in enabledModels"
            :key="model.id"
            @click="selectModel(model)"
            class="w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between"
            :class="{ 'bg-blue-50 dark:bg-blue-900/30': selectedModel?.id === model.id }"
          >
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ getProviderIcon(model.provider) }}</span>
              <div>
                <div class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ model.name }}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  {{ modelsStore.providers[model.provider]?.name || model.provider }}
                </div>
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <!-- 状态指示器 -->
              <span
                class="w-2 h-2 rounded-full"
                :class="getStatusColor(model.id)"
                :title="modelsStore.modelStatusCache[model.id]?.message || '未检测'"
              ></span>
              
              <!-- 默认标记 -->
              <span
                v-if="model.is_default"
                class="px-1.5 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded"
              >
                默认
              </span>
              
              <!-- 选中标记 -->
              <svg
                v-if="selectedModel?.id === model.id"
                class="w-4 h-4 text-blue-600 dark:text-blue-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
          </button>
        </div>

        <!-- 底部操作 -->
        <div class="border-t dark:border-gray-700 px-2 py-2">
          <button
            @click="isOpen = false"
            class="w-full px-3 py-1.5 text-sm text-center text-blue-600 dark:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            管理模型
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>
