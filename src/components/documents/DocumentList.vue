/**
 * 文档列表展示组件
 * 支持表格和卡片两种视图模式，显示文档状态、类型图标、大小和上传时间
 */
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import type { Document, DocumentStatus, DocumentType } from '@/types'
import DocumentActions from './DocumentActions.vue'

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
  (e: 'select', document: Document): void
  (e: 'upload'): void
}>()

// Store
const documentsStore = useDocumentsStore()

// ==================== 响应式状态 ====================

/**
 * 当前视图模式
 */
const currentViewMode = ref<'table' | 'card'>(props.viewMode)

/**
 * 搜索关键词
 */
const searchQuery = ref('')

/**
 * 状态筛选
 */
const statusFilter = ref<DocumentStatus | ''>('')

/**
 * 类型筛选
 */
const typeFilter = ref<DocumentType | ''>('')

/**
 * 重命名对话框显示状态
 */
const showRenameDialog = ref(false)

/**
 * 正在重命名的文档
 */
const renamingDocument = ref<Document | null>(null)

/**
 * 新文件名
 */
const newFilename = ref('')

/**
 * 删除确认对话框
 */
const showDeleteConfirm = ref(false)

/**
 * 待删除的文档 ID
 */
const documentToDelete = ref<number | null>(null)

// ==================== 计算属性 ====================

/**
 * 文档状态选项
 */
const statusOptions = computed(() => [
  { label: '全部状态', value: '' },
  { label: '等待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
])

/**
 * 文件类型选项
 */
const typeOptions = computed(() => [
  { label: '全部类型', value: '' },
  { label: 'PDF', value: 'pdf' },
  { label: 'Markdown', value: 'md' },
  { label: '文本', value: 'txt' },
  { label: 'Word', value: 'docx' },
  { label: 'HTML', value: 'html' }
])

/**
 * 总页数
 */
const totalPages = computed(() => 
  Math.ceil(documentsStore.pagination.total / documentsStore.pagination.pageSize)
)

/**
 * 页码数组
 */
const pageNumbers = computed(() => {
  const pages: number[] = []
  const current = documentsStore.pagination.page
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
 * 获取文件类型图标
 * @param fileType - 文件类型
 */
const getFileIcon = (fileType: DocumentType): string => {
  const icons: Record<DocumentType, string> = {
    pdf: '📄',
    md: '📝',
    txt: '📃',
    docx: '📘',
    html: '🌐'
  }
  return icons[fileType] || '📄'
}

/**
 * 获取文件类型颜色
 * @param fileType - 文件类型
 */
const getFileTypeColor = (fileType: DocumentType): string => {
  const colors: Record<DocumentType, string> = {
    pdf: 'text-red-500',
    md: 'text-blue-500',
    txt: 'text-gray-500',
    docx: 'text-blue-600',
    html: 'text-orange-500'
  }
  return colors[fileType] || 'text-gray-500'
}

/**
 * 获取状态颜色
 * @param status - 文档状态
 */
const getStatusColor = (status: DocumentStatus): string => {
  const colors: Record<DocumentStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

/**
 * 获取状态文本
 * @param status - 文档状态
 */
const getStatusText = (status: DocumentStatus): string => {
  const texts: Record<DocumentStatus, string> = {
    pending: '等待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

/**
 * 格式化文件大小
 * @param bytes - 字节数
 */
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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
 * 刷新文档列表
 */
const refreshList = async () => {
  await documentsStore.fetchDocuments({
    status: statusFilter.value || undefined,
    file_type: typeFilter.value || undefined,
    search: searchQuery.value || undefined,
    page: documentsStore.pagination.page,
    pageSize: documentsStore.pagination.pageSize
  })
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  documentsStore.setPage(1)
  refreshList()
}

/**
 * 处理筛选变化
 */
const handleFilterChange = () => {
  documentsStore.setPage(1)
  refreshList()
}

/**
 * 处理页码变化
 * @param page - 页码
 */
const handlePageChange = (page: number) => {
  documentsStore.setPage(page)
  refreshList()
}

/**
 * 处理每页数量变化
 * @param event - 选择事件
 */
const handlePageSizeChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  documentsStore.setPageSize(Number(target.value))
  refreshList()
}

/**
 * 处理文档选择
 * @param document - 文档对象
 */
const handleSelect = (document: Document) => {
  emit('select', document)
}

/**
 * 处理重命名
 * @param document - 文档对象
 */
const handleRename = (document: Document) => {
  renamingDocument.value = document
  newFilename.value = document.original_name
  showRenameDialog.value = true
}

/**
 * 确认重命名
 */
const confirmRename = async () => {
  if (!renamingDocument.value || !newFilename.value.trim()) return
  
  try {
    await documentsStore.updateDocument(renamingDocument.value.id, {
      filename: newFilename.value.trim()
    })
    showRenameDialog.value = false
    renamingDocument.value = null
    newFilename.value = ''
  } catch (error) {
    console.error('重命名失败:', error)
  }
}

/**
 * 处理删除
 * @param documentId - 文档 ID
 */
const handleDelete = (documentId: number) => {
  documentToDelete.value = documentId
  showDeleteConfirm.value = true
}

/**
 * 确认删除
 */
const confirmDelete = async () => {
  if (documentToDelete.value === null) return
  
  await documentsStore.deleteDocument(documentToDelete.value)
  showDeleteConfirm.value = false
  documentToDelete.value = null
}

/**
 * 处理批量删除
 */
const handleBatchDelete = async () => {
  if (!documentsStore.hasSelection) return
  
  if (confirm(`确定要删除选中的 ${documentsStore.selectedIds.length} 个文档吗？`)) {
    await documentsStore.deleteDocuments(documentsStore.selectedIds)
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
watch([statusFilter, typeFilter], () => {
  handleFilterChange()
})
</script>

<template>
  <div class="document-list flex flex-col h-full">
    <!-- 工具栏 -->
    <div class="toolbar p-4 border-b dark:border-gray-700 bg-white dark:bg-gray-800">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 搜索框 -->
        <div class="flex-1 min-w-[200px]">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索文档..."
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
          </div>
        </div>

        <!-- 状态筛选 -->
        <select
          v-model="statusFilter"
          class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>

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
          :disabled="documentsStore.isLoading"
          class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
          title="刷新"
        >
          <svg
            class="w-5 h-5"
            :class="{ 'animate-spin': documentsStore.isLoading }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <!-- 上传按钮 -->
        <button
          @click="emit('upload')"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          上传文档
        </button>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="documentsStore.hasSelection" class="mt-3 flex items-center gap-4">
        <span class="text-sm text-gray-600 dark:text-gray-400">
          已选择 {{ documentsStore.selectedIds.length }} 个文档
        </span>
        <button
          @click="handleBatchDelete"
          class="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 border border-red-600 dark:border-red-400 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
        >
          批量删除
        </button>
        <button
          @click="documentsStore.clearSelection"
          class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          取消选择
        </button>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="flex-1 overflow-auto p-4">
      <!-- 加载状态 -->
      <div v-if="documentsStore.isLoading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="documentsStore.documents.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-lg">暂无文档</p>
        <p class="text-sm mt-2">点击"上传文档"按钮添加文档</p>
      </div>

      <!-- 表格视图 -->
      <div v-else-if="currentViewMode === 'table'" class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700/50">
            <tr>
              <th class="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  :checked="documentsStore.isAllSelected"
                  @change="documentsStore.toggleSelectAll"
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">文件名</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">类型</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">大小</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">状态</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">分块数</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">上传时间</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-600 dark:text-gray-300">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr
              v-for="document in documentsStore.documents"
              :key="document.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
              :class="{ 'bg-blue-50 dark:bg-blue-900/20': documentsStore.selectedIds.includes(document.id) }"
            >
              <td class="px-4 py-3">
                <input
                  type="checkbox"
                  :checked="documentsStore.selectedIds.includes(document.id)"
                  @change="documentsStore.toggleSelection(document.id)"
                  @click.stop
                  class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                />
              </td>
              <td class="px-4 py-3" @click="handleSelect(document)">
                <div class="flex items-center gap-2">
                  <span class="text-xl">{{ getFileIcon(document.file_type) }}</span>
                  <span class="text-gray-900 dark:text-white font-medium">{{ document.original_name }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span :class="getFileTypeColor(document.file_type)" class="font-medium uppercase">
                  {{ document.file_type }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">
                {{ formatFileSize(document.file_size) }}
              </td>
              <td class="px-4 py-3">
                <span :class="getStatusColor(document.status)" class="px-2 py-1 rounded-full text-xs font-medium">
                  {{ getStatusText(document.status) }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400">
                {{ document.chunk_count }}
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-400 text-sm">
                {{ formatDate(document.created_at) }}
              </td>
              <td class="px-4 py-3">
                <DocumentActions
                  :document="document"
                  @rename="handleRename"
                  @delete="handleDelete"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div
          v-for="document in documentsStore.documents"
          :key="document.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 dark:border-gray-700 cursor-pointer overflow-hidden"
          :class="{ 'ring-2 ring-blue-500': documentsStore.selectedIds.includes(document.id) }"
          @click="handleSelect(document)"
        >
          <!-- 卡片头部 -->
          <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
            <div class="flex items-center gap-3">
              <span class="text-3xl">{{ getFileIcon(document.file_type) }}</span>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-900 dark:text-white truncate" :title="document.original_name">
                  {{ document.original_name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ document.file_type.toUpperCase() }} · {{ formatFileSize(document.file_size) }}
                </p>
              </div>
            </div>
            <input
              type="checkbox"
              :checked="documentsStore.selectedIds.includes(document.id)"
              @change="documentsStore.toggleSelection(document.id)"
              @click.stop
              class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
            />
          </div>

          <!-- 卡片内容 -->
          <div class="p-4 space-y-3">
            <!-- 状态 -->
            <div class="flex items-center justify-between">
              <span :class="getStatusColor(document.status)" class="px-2 py-1 rounded-full text-xs font-medium">
                {{ getStatusText(document.status) }}
              </span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ document.chunk_count }} 个分块
              </span>
            </div>

            <!-- 错误信息 -->
            <div v-if="document.status === 'failed' && document.error_message" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
              {{ document.error_message }}
            </div>

            <!-- 时间 -->
            <div class="text-sm text-gray-500 dark:text-gray-400">
              {{ formatDate(document.created_at) }}
            </div>
          </div>

          <!-- 卡片底部操作 -->
          <div class="flex items-center justify-end gap-1 p-3 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
            <DocumentActions
              :document="document"
              @rename="handleRename"
              @delete="handleDelete"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="documentsStore.documents.length > 0" class="flex items-center justify-between p-4 border-t dark:border-gray-700 bg-white dark:bg-gray-800">
      <div class="flex items-center gap-2">
        <span class="text-sm text-gray-600 dark:text-gray-400">每页显示</span>
        <select
          :value="documentsStore.pagination.pageSize"
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
          :disabled="documentsStore.pagination.page === 1"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          首页
        </button>

        <!-- 上一页 -->
        <button
          @click="handlePageChange(documentsStore.pagination.page - 1)"
          :disabled="documentsStore.pagination.page === 1"
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
          :class="page === documentsStore.pagination.page 
            ? 'bg-blue-600 text-white' 
            : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'"
        >
          {{ page }}
        </button>

        <!-- 下一页 -->
        <button
          @click="handlePageChange(documentsStore.pagination.page + 1)"
          :disabled="documentsStore.pagination.page >= totalPages"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          下一页
        </button>

        <!-- 末页 -->
        <button
          @click="handlePageChange(totalPages)"
          :disabled="documentsStore.pagination.page >= totalPages"
          class="px-3 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600 dark:text-gray-400"
        >
          末页
        </button>
      </div>

      <div class="text-sm text-gray-600 dark:text-gray-400">
        共 {{ documentsStore.pagination.total }} 条记录
      </div>
    </div>

    <!-- 重命名对话框 -->
    <div v-if="showRenameDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">重命名文档</h3>
        <input
          v-model="newFilename"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
          placeholder="输入新文件名"
          @keyup.enter="confirmRename"
        />
        <div class="flex justify-end gap-3 mt-4">
          <button
            @click="showRenameDialog = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
          >
            取消
          </button>
          <button
            @click="confirmRename"
            :disabled="!newFilename.trim()"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            确认
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">确认删除</h3>
        <p class="text-gray-600 dark:text-gray-400 mb-4">确定要删除这个文档吗？此操作无法撤销。</p>
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
