/**
 * 记忆列表展示组件
 * 支持表格和卡片两种视图模式，显示记忆类型、重要性、内容预览和创建时间
 */
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMemoryStore } from '@/stores/memory'
import type { Memory, MemoryType } from '@/types'
import { memoryTypeConfig } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 视图模式: table 或 card
   */
  viewMode?: 'table' | 'card'
}

const props = withDefaults(defineProps<Props>(), {
  viewMode: 'table'
})

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'select', memory: Memory): void
  (e: 'edit', memory: Memory): void
  (e: 'create'): void
}>()

// Store
const memoryStore = useMemoryStore()

// ==================== 响应式状态 ====================

/**
 * 当前视图模式
 */
const currentViewMode = ref<'table' | 'card'>(props.viewMode)

/**
 * 类型筛选
 */
const typeFilter = ref<MemoryType | ''>('')

/**
 * 删除确认对话框
 */
const showDeleteConfirm = ref(false)

/**
 * 待删除的记忆 ID
 */
const memoryToDelete = ref<string | null>(null)

// ==================== 计算属性 ====================

/**
 * 记忆类型选项
 */
const typeOptions = computed(() => [
  { label: '全部类型', value: '' },
  { label: memoryTypeConfig.instant.label, value: 'instant' },
  { label: memoryTypeConfig.working.label, value: 'working' },
  { label: memoryTypeConfig.long_term.label, value: 'long_term' }
])

/**
 * 总页数
 */
const totalPages = computed(() =>
  Math.ceil(memoryStore.pagination.total / memoryStore.pagination.pageSize)
)

/**
 * 页码数组
 */
const pageNumbers = computed(() => {
  const pages: number[] = []
  const current = memoryStore.pagination.page
  const total = totalPages.value

  // 显示当前页附近的页码
  const start = Math.max(1, current - 2)
  const end = Math.min(total, current + 2)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

// ==================== 方法 ====================

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
 * 获取重要性星星显示
 * @param importance - 重要性值
 */
const getImportanceStars = (importance: number): string => {
  const fullStars = Math.floor(importance / 2)
  return '★'.repeat(fullStars) + '☆'.repeat(5 - fullStars)
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
const truncateContent = (content: string, maxLength: number = 100): string => {
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

/**
 * 刷新记忆列表
 */
const refreshList = async () => {
  await memoryStore.fetchMemories({
    memoryType: typeFilter.value || undefined,
    page: memoryStore.pagination.page,
    pageSize: memoryStore.pagination.pageSize
  })
}

/**
 * 处理筛选变化
 */
const handleFilterChange = () => {
  memoryStore.setPage(1)
  refreshList()
}

/**
 * 处理页码变化
 * @param page - 页码
 */
const handlePageChange = (page: number) => {
  memoryStore.setPage(page)
  refreshList()
}

/**
 * 处理每页数量变化
 * @param event - 选择事件
 */
const handlePageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  memoryStore.setPageSize(Number(target.value))
  refreshList()
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

/**
 * 处理删除
 * @param memoryId - 记忆 ID
 */
const handleDelete = (memoryId: string) => {
  memoryToDelete.value = memoryId
  showDeleteConfirm.value = true
}

/**
 * 确认删除
 */
const confirmDelete = async () => {
  if (memoryToDelete.value === null) return

  await memoryStore.deleteMemory(memoryToDelete.value)
  showDeleteConfirm.value = false
  memoryToDelete.value = null
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async () => {
  if (!memoryStore.hasSelection) return

  if (confirm(`确定要删除选中的 ${memoryStore.selectedIds.length} 条记忆吗？`)) {
    await memoryStore.deleteMemories(memoryStore.selectedIds)
  }
}

/**
 * 切换视图模式
 */
const toggleViewMode = () => {
  currentViewMode.value = currentViewMode.value === 'table' ? 'card' : 'table'
}

// ==================== 生命周期 ====================

onMounted(() => {
  refreshList()
})

// 监听筛选条件变化
watch(typeFilter, () => {
  handleFilterChange()
})
</script>

<template>
  <div class="memory-list flex flex-col h-full">
    <!-- 工具栏 -->
    <div class="toolbar p-4 border-b dark:border-gray-700 bg-white dark:bg-gray-800">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 类型筛选 -->
        <select
          v-model="typeFilter"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="option in typeOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

        <!-- 视图切换 -->
        <button
          @click="toggleViewMode"
          class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          :title="currentViewMode === 'table' ? '卡片视图' : '表格视图'"
        >
          <svg v-if="currentViewMode === 'table'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
        </button>

        <!-- 刷新按钮 -->
        <button
          @click="refreshList"
          :disabled="memoryStore.isLoading"
          class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
          title="刷新"
        >
          <svg
            class="w-5 h-5"
            :class="{ 'animate-spin': memoryStore.isLoading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- 创建按钮 -->
        <button
          @click="emit('create')"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          新建记忆
        </button>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="memoryStore.hasSelection" class="mt-3 flex items-center gap-4">
        <span class="text-sm text-gray-600 dark:text-gray-400">
          已选择 {{ memoryStore.selectedIds.length }} 条记忆
        </span>
        <button
          @click="handleBatchDelete"
          class="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 border border-red-600 dark:border-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          批量删除
        </button>
        <button
          @click="memoryStore.clearSelection"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          取消选择
        </button>
      </div>
    </div>

    <!-- 记忆列表 -->
    <div class="flex-1 overflow-auto p-4">
      <!-- 加载状态 -->
      <div v-if="memoryStore.isLoading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="memoryStore.memories.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <p class="text-lg">暂无记忆</p>
        <p class="text-sm mt-2">点击"新建记忆"按钮添加记忆</p>
      </div>

      <!-- 表格视图 -->
      <div v-else-if="currentViewMode === 'table'" class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700/50">
            <tr>
              <th class="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  :checked="memoryStore.isAllSelected"
                  @change="memoryStore.toggleSelectAll"
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">类型</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">内容预览</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">重要性</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">创建时间</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="memory in memoryStore.memories"
              :key="memory.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
              :class="{ 'bg-blue-50 dark:bg-blue-900/20': memoryStore.selectedIds.includes(memory.id) }"
            >
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  :checked="memoryStore.selectedIds.includes(memory.id)"
                  @change="memoryStore.toggleSelection(memory.id)"
                  @click.stop
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
              </td>
              <td class="px-4 py-3" @click="handleSelect(memory)">
                <div class="flex items-center gap-2">
                  <span class="text-xl">{{ getMemoryTypeIcon(memory.memoryType) }}</span>
                  <span :class="getMemoryTypeColorClass(memory.memoryType)" class="px-2 py-1 rounded-full text-xs font-medium">
                    {{ memoryTypeConfig[memory.memoryType].label }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 max-w-md" @click="handleSelect(memory)">
                <p class="text-gray-900 dark:text-white line-clamp-2">
                  {{ truncateContent(memory.content, 80) }}
                </p>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-1">
                  <span :class="getImportanceColorClass(memory.importance)" class="text-sm">
                    {{ getImportanceStars(memory.importance) }}
                  </span>
                  <span class="text-xs text-gray-500 dark:text-gray-400 ml-1">
                    ({{ memory.importance }})
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400 text-sm">
                {{ formatDate(memory.createdAt) }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <button
                    @click.stop="handleEdit(memory)"
                    class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    title="编辑"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    @click.stop="handleDelete(memory.id)"
                    class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    title="删除"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="memory in memoryStore.memories"
          :key="memory.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-700 cursor-pointer overflow-hidden"
          :class="{ 'ring-2 ring-blue-500': memoryStore.selectedIds.includes(memory.id) }"
          @click="handleSelect(memory)"
        >
          <!-- 卡片头部 -->
          <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ getMemoryTypeIcon(memory.memoryType) }}</span>
              <span :class="getMemoryTypeColorClass(memory.memoryType)" class="px-2 py-1 rounded-full text-xs font-medium">
                {{ memoryTypeConfig[memory.memoryType].label }}
              </span>
            </div>
            <input
              type="checkbox"
              :checked="memoryStore.selectedIds.includes(memory.id)"
              @change="memoryStore.toggleSelection(memory.id)"
              @click.stop
              class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <!-- 卡片内容 -->
          <div class="p-4 space-y-3">
            <!-- 内容预览 -->
            <p class="text-gray-700 dark:text-gray-300 text-sm line-clamp-3">
              {{ truncateContent(memory.content, 120) }}
            </p>

            <!-- 重要性 -->
            <div class="flex items-center gap-1">
              <span :class="getImportanceColorClass(memory.importance)" class="text-sm">
                {{ getImportanceStars(memory.importance) }}
              </span>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                重要性: {{ memory.importance }}/10
              </span>
            </div>

            <!-- 时间 -->
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {{ formatDate(memory.createdAt) }}
            </div>
          </div>

          <!-- 卡片底部操作 -->
          <div class="flex items-center justify-end gap-1 p-3 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            <button
              @click.stop="handleEdit(memory)"
              class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              title="编辑"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              @click.stop="handleDelete(memory.id)"
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
    </div>

    <!-- 分页 -->
    <div v-if="memoryStore.memories.length > 0" class="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-white dark:bg-gray-800">
      <div class="flex items-center gap-2">
        <span class="text-sm text-gray-600 dark:text-gray-400">每页显示</span>
        <select
          :value="memoryStore.pagination.pageSize"
          @change="handlePageSizeChange"
          class="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
        >
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
        <span class="text-sm text-gray-600 dark:text-gray-400">条</span>
      </div>

      <div class="flex items-center gap-1">
        <!-- 首页 -->
        <button
          @click="handlePageChange(1)"
          :disabled="memoryStore.pagination.page === 1"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          首页
        </button>

        <!-- 上一页 -->
        <button
          @click="handlePageChange(memoryStore.pagination.page - 1)"
          :disabled="memoryStore.pagination.page === 1"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          上一页
        </button>

        <!-- 页码 -->
        <button
          v-for="page in pageNumbers"
          :key="page"
          @click="handlePageChange(page)"
          class="px-3 py-1 text-sm rounded"
          :class="page === memoryStore.pagination.page
            ? 'bg-blue-600 text-white'
            : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'"
        >
          {{ page }}
        </button>

        <!-- 下一页 -->
        <button
          @click="handlePageChange(memoryStore.pagination.page + 1)"
          :disabled="memoryStore.pagination.page >= totalPages"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          下一页
        </button>

        <!-- 末页 -->
        <button
          @click="handlePageChange(totalPages)"
          :disabled="memoryStore.pagination.page >= totalPages"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          末页
        </button>
      </div>

      <div class="text-sm text-gray-600 dark:text-gray-400">
        共 {{ memoryStore.pagination.total }} 条记录
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">确认删除</h3>
        <p class="text-gray-600 dark:text-gray-400 mb-4">确定要删除这条记忆吗？此操作无法撤销。</p>
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
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
