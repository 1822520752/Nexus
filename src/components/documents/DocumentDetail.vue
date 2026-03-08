/**
 * 文档详情组件
 * 显示文档详情、分块列表和文档预览
 */
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import type { Document, DocumentChunk, DocumentStatus, DocumentType } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 文档 ID
   */
  documentId?: number
}

const props = defineProps<Props>()

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'close'): void
}>()

// Store
const documentsStore = useDocumentsStore()

// ==================== 响应式状态 ====================

/**
 * 当前选中的分块索引
 */
const selectedChunkIndex = ref<number | null>(null)

/**
 * 搜索关键词
 */
const searchKeyword = ref('')

/**
 * 是否显示分块列表
 */
const showChunks = ref(true)

// ==================== 计算属性 ====================

/**
 * 当前文档
 */
const document = computed(() => documentsStore.currentDocument)

/**
 * 分块列表
 */
const chunks = computed(() => documentsStore.currentChunks)

/**
 * 筛选后的分块列表
 */
const filteredChunks = computed(() => {
  if (!searchKeyword.value) return chunks.value
  
  const keyword = searchKeyword.value.toLowerCase()
  return chunks.value.filter(chunk => 
    chunk.content.toLowerCase().includes(keyword)
  )
})

/**
 * 选中的分块
 */
const selectedChunk = computed(() => {
  if (selectedChunkIndex.value === null) return null
  return filteredChunks.value[selectedChunkIndex.value] || null
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
 * 选择分块
 * @param index - 分块索引
 */
const selectChunk = (index: number) => {
  selectedChunkIndex.value = index
}

/**
 * 关闭详情面板
 */
const close = () => {
  emit('close')
}

/**
 * 加载文档详情
 */
const loadDocument = async () => {
  if (props.documentId) {
    await documentsStore.fetchDocumentById(props.documentId)
  }
}

// ==================== 监听器 ====================

watch(() => props.documentId, () => {
  loadDocument()
})

// ==================== 生命周期 ====================

onMounted(() => {
  loadDocument()
})
</script>

<template>
  <div class="document-detail h-full flex flex-col bg-white dark:bg-gray-800">
    <!-- 头部 -->
    <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">文档详情</h2>
      <button
        @click="close"
        class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="documentsStore.isLoading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!document" class="flex-1 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
      <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p>未选择文档</p>
    </div>

    <!-- 文档详情内容 -->
    <div v-else class="flex-1 overflow-hidden flex flex-col">
      <!-- 文档基本信息 -->
      <div class="p-4 border-b dark:border-gray-700">
        <div class="flex items-start gap-4">
          <!-- 文件图标 -->
          <div class="w-16 h-16 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
            <span class="text-4xl">{{ getFileIcon(document.file_type) }}</span>
          </div>

          <!-- 文件信息 -->
          <div class="flex-1 min-w-0">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate" :title="document.original_name">
              {{ document.original_name }}
            </h3>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ document.file_type.toUpperCase() }}
              </span>
              <span class="text-gray-300 dark:text-gray-600">|</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ formatFileSize(document.file_size) }}
              </span>
              <span class="text-gray-300 dark:text-gray-600">|</span>
              <span :class="getStatusColor(document.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                {{ getStatusText(document.status) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 详细信息 -->
        <div class="grid grid-cols-2 gap-4 mt-4 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400">分块数量:</span>
            <span class="ml-2 text-gray-900 dark:text-white">{{ document.chunk_count }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">上传时间:</span>
            <span class="ml-2 text-gray-900 dark:text-white">{{ formatDate(document.created_at) }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">更新时间:</span>
            <span class="ml-2 text-gray-900 dark:text-white">{{ formatDate(document.updated_at) }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">文件路径:</span>
            <span class="ml-2 text-gray-900 dark:text-white truncate" :title="document.file_path">
              {{ document.file_path }}
            </span>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="document.status === 'failed' && document.error_message" class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <p class="text-sm text-red-600 dark:text-red-400">
            <span class="font-medium">错误信息:</span> {{ document.error_message }}
          </p>
        </div>
      </div>

      <!-- 分块列表切换 -->
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <button
          @click="showChunks = !showChunks"
          class="flex items-center gap-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        >
          <svg
            class="w-5 h-5 transition-transform"
            :class="{ 'rotate-90': showChunks }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          <span class="font-medium">分块列表</span>
          <span class="text-sm text-gray-500 dark:text-gray-400">({{ chunks.length }} 个)</span>
        </button>

        <!-- 搜索框 -->
        <div class="relative">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索分块内容..."
            class="w-48 pl-8 pr-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            class="absolute left-2.5 top-2 w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <!-- 分块列表 -->
      <div v-show="showChunks" class="flex-1 overflow-hidden flex">
        <!-- 分块列表侧边栏 -->
        <div class="w-1/3 border-r dark:border-gray-700 overflow-y-auto">
          <div v-if="filteredChunks.length === 0" class="p-4 text-center text-gray-500 dark:text-gray-400 text-sm">
            {{ searchKeyword ? '未找到匹配的分块' : '暂无分块数据' }}
          </div>
          <div v-else class="divide-y dark:divide-gray-700">
            <div
              v-for="(chunk, index) in filteredChunks"
              :key="chunk.id"
              @click="selectChunk(index)"
              class="p-3 cursor-pointer transition-colors"
              :class="selectedChunkIndex === index 
                ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-600' 
                : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  分块 #{{ chunk.chunk_index + 1 }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  {{ chunk.token_count }} tokens
                </span>
              </div>
              <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                {{ chunk.content.substring(0, 100) }}...
              </p>
            </div>
          </div>
        </div>

        <!-- 分块内容预览 -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="!selectedChunk" class="h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
            <p>选择一个分块查看内容</p>
          </div>
          <div v-else>
            <div class="flex items-center justify-between mb-4">
              <h4 class="font-medium text-gray-900 dark:text-white">
                分块 #{{ selectedChunk.chunk_index + 1 }}
              </h4>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ selectedChunk.token_count }} tokens
              </span>
            </div>
            <div class="prose dark:prose-invert max-w-none">
              <p class="whitespace-pre-wrap text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                {{ selectedChunk.content }}
              </p>
            </div>
          </div>
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
</style>
