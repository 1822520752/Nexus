/**
 * 记忆搜索组件
 * 提供搜索输入框、高级搜索选项（时间范围、类型、重要性）和搜索结果展示
 */
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMemoryStore } from '@/stores/memory'
import type { Memory, MemoryType, MemorySearchParams } from '@/types'
import { memoryTypeConfig } from '@/types'

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'select', memory: Memory): void
  (e: 'edit', memory: Memory): void
}>()

// Store
const memoryStore = useMemoryStore()

// ==================== 响应式状态 ====================

/**
 * 搜索关键词
 */
const searchQuery = ref('')

/**
 * 是否显示高级搜索
 */
const showAdvancedSearch = ref(false)

/**
 * 高级搜索参数
 */
const advancedParams = ref({
  memoryType: '' as MemoryType | '',
  minImportance: 1,
  maxImportance: 10,
  startDate: '',
  endDate: ''
})

/**
 * 是否正在搜索
 */
const isSearching = ref(false)

// ==================== 计算属性 ====================

/**
 * 记忆类型选项
 */
const memoryTypeOptions = computed(() => [
  { label: '全部类型', value: '' },
  { label: memoryTypeConfig.instant.label, value: 'instant' },
  { label: memoryTypeConfig.working.label, value: 'working' },
  { label: memoryTypeConfig.long_term.label, value: 'long_term' }
])

/**
 * 是否有搜索结果
 */
const hasResults = computed(() => memoryStore.searchResults.length > 0)

/**
 * 是否有搜索条件
 */
const hasSearchConditions = computed(() => {
  return searchQuery.value.trim() !== '' ||
    advancedParams.value.memoryType !== '' ||
    advancedParams.value.minImportance > 1 ||
    advancedParams.value.maxImportance < 10 ||
    advancedParams.value.startDate !== '' ||
    advancedParams.value.endDate !== ''
})

// ==================== 方法 ====================

/**
 * 执行搜索
 */
const handleSearch = async () => {
  if (!hasSearchConditions.value) return

  isSearching.value = true

  const params: MemorySearchParams = {
    query: searchQuery.value.trim() || undefined,
    memoryType: advancedParams.value.memoryType || undefined,
    minImportance: advancedParams.value.minImportance > 1 ? advancedParams.value.minImportance : undefined,
    maxImportance: advancedParams.value.maxImportance < 10 ? advancedParams.value.maxImportance : undefined,
    startDate: advancedParams.value.startDate || undefined,
    endDate: advancedParams.value.endDate || undefined
  }

  await memoryStore.searchMemories(params)
  isSearching.value = false
}

/**
 * 清除搜索
 */
const handleClear = () => {
  searchQuery.value = ''
  advancedParams.value = {
    memoryType: '',
    minImportance: 1,
    maxImportance: 10,
    startDate: '',
    endDate: ''
  }
  memoryStore.clearSearchResults()
}

/**
 * 切换高级搜索
 */
const toggleAdvancedSearch = () => {
  showAdvancedSearch.value = !showAdvancedSearch.value
}

/**
 * 获取记忆类型图标
 * @param memoryType - 记忆类型
 */
const getMemoryTypeIcon = (memoryType: MemoryType): string => {
  const icons: Record<MemoryType, string> = {
    instant: '⚡',
    working: '🔧',
    long_term: '📚'
  }
  return icons[memoryType] || '📝'
}

/**
 * 获取记忆类型颜色类
 * @param memoryType - 记忆类型
 */
const getMemoryTypeColorClass = (memoryType: MemoryType): string => {
  const color = memoryTypeConfig[memoryType].color
  const colors: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    green: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
  }
  return colors[color] || 'bg-gray-100 text-gray-800'
}

/**
 * 获取重要性颜色类
 * @param importance - 重要性值
 */
const getImportanceColorClass = (importance: number): string => {
  if (importance >= 8) return 'text-red-500'
  if (importance >= 6) return 'text-orange-500'
  if (importance >= 4) return 'text-yellow-500'
  return 'text-gray-400'
}

/**
 * 格式化日期
 * @param dateString - 日期字符串
 */
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 截断内容预览
 * @param content - 内容
 * @param maxLength - 最大长度
 */
const truncateContent = (content: string, maxLength: number = 150): string => {
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

/**
 * 高亮搜索关键词
 * @param text - 原文本
 */
const highlightSearchTerm = (text: string): string => {
  if (!searchQuery.value.trim()) return text

  const regex = new RegExp(`(${searchQuery.value.trim()})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">$1</mark>')
}

/**
 * 处理记忆选择
 * @param memory - 记忆对象
 */
const handleSelect = (memory: Memory) => {
  emit('select', memory)
}

/**
 * 处理编辑
 * @param memory - 记忆对象
 */
const handleEdit = (memory: Memory) => {
  emit('edit', memory)
}

// ==================== 监听器 ====================

// 监听搜索关键词变化，自动搜索（防抖）
let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    if (searchQuery.value.trim()) {
      handleSearch()
    }
  }, 500)
})
</script>

<template>
  <div class="memory-search flex flex-col h-full">
    <!-- 搜索区域 -->
    <div class="search-area p-4 border-b dark:border-gray-700 bg-white dark:bg-gray-800">
      <!-- 搜索输入框 -->
      <div class="flex gap-2">
        <div class="flex-1 relative">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索记忆内容..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            @keyup.enter="handleSearch"
          />
          <svg
            class="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <!-- 清除按钮 -->
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 高级搜索按钮 -->
        <button
          @click="toggleAdvancedSearch"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
          :class="{ 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-600 dark:text-blue-400': showAdvancedSearch }"
          title="高级搜索"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
        </button>

        <!-- 搜索按钮 -->
        <button
          @click="handleSearch"
          :disabled="isSearching || !hasSearchConditions"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg
            v-if="isSearching"
            class="animate-spin w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          搜索
        </button>
      </div>

      <!-- 高级搜索选项 -->
      <div v-if="showAdvancedSearch" class="mt-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <!-- 记忆类型 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              记忆类型
            </label>
            <select
              v-model="advancedParams.memoryType"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="option in memoryTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <!-- 重要性范围 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              重要性范围
            </label>
            <div class="flex items-center gap-2">
              <input
                v-model.number="advancedParams.minImportance"
                type="number"
                min="1"
                max="10"
                class="w-20 px-2 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center"
              />
              <span class="text-gray-500">-</span>
              <input
                v-model.number="advancedParams.maxImportance"
                type="number"
                min="1"
                max="10"
                class="w-20 px-2 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center"
              />
            </div>
          </div>

          <!-- 开始日期 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              开始日期
            </label>
            <input
              v-model="advancedParams.startDate"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <!-- 结束日期 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              结束日期
            </label>
            <input
              v-model="advancedParams.endDate"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <!-- 清除按钮 -->
        <div class="flex justify-end">
          <button
            @click="handleClear"
            class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            清除所有条件
          </button>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div class="flex-1 overflow-auto p-4">
      <!-- 加载状态 -->
      <div v-if="isSearching" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!hasResults" class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="text-lg">输入关键词搜索记忆</p>
        <p class="text-sm mt-2">支持内容搜索和高级筛选</p>
      </div>

      <!-- 搜索结果列表 -->
      <div v-else class="space-y-3">
        <!-- 结果统计 -->
        <div class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          找到 {{ memoryStore.searchResults.length }} 条相关记忆
        </div>

        <!-- 结果卡片 -->
        <div
          v-for="memory in memoryStore.searchResults"
          :key="memory.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700 p-4 cursor-pointer"
          @click="handleSelect(memory)"
        >
          <div class="flex items-start justify-between gap-4">
            <!-- 左侧内容 -->
            <div class="flex-1 min-w-0">
              <!-- 类型标签 -->
              <div class="flex items-center gap-2 mb-2">
                <span class="text-lg">{{ getMemoryTypeIcon(memory.memoryType) }}</span>
                <span :class="getMemoryTypeColorClass(memory.memoryType)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                  {{ memoryTypeConfig[memory.memoryType].label }}
                </span>
                <span :class="getImportanceColorClass(memory.importance)" class="text-sm">
                  重要性: {{ memory.importance }}
                </span>
              </div>

              <!-- 内容预览（带高亮） -->
              <p
                class="text-gray-700 dark:text-gray-300 text-sm line-clamp-3"
                v-html="highlightSearchTerm(truncateContent(memory.content))"
              ></p>

              <!-- 时间 -->
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {{ formatDate(memory.createdAt) }}
              </div>
            </div>

            <!-- 右侧操作 -->
            <button
              @click.stop="handleEdit(memory)"
              class="flex-shrink-0 p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              title="编辑"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 高亮样式 */
:deep(mark) {
  background-color: transparent;
}
</style>
