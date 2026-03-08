/**
 * 文档上传组件
 * 支持拖拽上传、文件类型验证、上传进度显示和多文件上传
 */
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import type { DocumentType, UploadProgress } from '@/types'

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'uploaded'): void
}>()

// Store
const documentsStore = useDocumentsStore()

// ==================== 常量 ====================

/**
 * 允许上传的文件类型
 */
const ALLOWED_TYPES: Record<string, DocumentType> = {
  'application/pdf': 'pdf',
  'text/markdown': 'md',
  'text/plain': 'txt',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
  'text/html': 'html'
}

/**
 * 允许的文件扩展名
 */
const ALLOWED_EXTENSIONS: Record<string, DocumentType> = {
  '.pdf': 'pdf',
  '.md': 'md',
  '.markdown': 'md',
  '.txt': 'txt',
  '.docx': 'docx',
  '.html': 'html',
  '.htm': 'html'
}

/**
 * 最大文件大小 (50MB)
 */
const MAX_FILE_SIZE = 50 * 1024 * 1024

// ==================== 响应式状态 ====================

/**
 * 是否正在拖拽
 */
const isDragging = ref(false)

/**
 * 选中的文件列表
 */
const selectedFiles = ref<File[]>([])

/**
 * 是否正在上传
 */
const isUploading = ref(false)

/**
 * 文件输入框引用
 */
const fileInput = ref<HTMLInputElement | null>(null)

// ==================== 计算属性 ====================

/**
 * 允许的文件类型描述
 */
const allowedTypesDescription = computed(() => 
  'PDF, Markdown, TXT, Word (DOCX), HTML'
)

/**
 * 是否有选中的文件
 */
const hasFiles = computed(() => selectedFiles.value.length > 0)

// ==================== 方法 ====================

/**
 * 获取文件类型
 * @param file - 文件对象
 */
const getFileType = (file: File): DocumentType | null => {
  // 先检查 MIME 类型
  if (ALLOWED_TYPES[file.type]) {
    return ALLOWED_TYPES[file.type]
  }

  // 再检查扩展名
  const extension = '.' + file.name.split('.').pop()?.toLowerCase()
  if (ALLOWED_EXTENSIONS[extension]) {
    return ALLOWED_EXTENSIONS[extension]
  }

  return null
}

/**
 * 获取文件图标
 * @param file - 文件对象
 */
const getFileIcon = (file: File): string => {
  const fileType = getFileType(file)
  const icons: Record<DocumentType, string> = {
    pdf: '📄',
    md: '📝',
    txt: '📃',
    docx: '📘',
    html: '🌐'
  }
  return fileType ? icons[fileType] : '📄'
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
 * 验证文件
 * @param file - 文件对象
 */
const validateFile = (file: File): { valid: boolean; error?: string } => {
  // 检查文件类型
  const fileType = getFileType(file)
  if (!fileType) {
    return { valid: false, error: '不支持的文件类型' }
  }

  // 检查文件大小
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: `文件大小超过限制 (最大 ${MAX_FILE_SIZE / 1024 / 1024}MB)` }
  }

  return { valid: true }
}

/**
 * 处理文件选择
 * @param files - 文件列表
 */
const handleFiles = (files: FileList | File[]) => {
  const fileArray = Array.from(files)
  
  for (const file of fileArray) {
    const validation = validateFile(file)
    if (validation.valid) {
      // 检查是否已存在
      const exists = selectedFiles.value.some(f => f.name === file.name && f.size === file.size)
      if (!exists) {
        selectedFiles.value.push(file)
      }
    } else {
      // 显示错误提示
      alert(`${file.name}: ${validation.error}`)
    }
  }
}

/**
 * 处理拖拽进入
 * @param event - 拖拽事件
 */
const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = true
}

/**
 * 处理拖拽离开
 * @param event - 拖拽事件
 */
const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false
}

/**
 * 处理拖拽悬停
 * @param event - 拖拽事件
 */
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
}

/**
 * 处理拖拽放下
 * @param event - 拖拽事件
 */
const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false

  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    handleFiles(files)
  }
}

/**
 * 处理文件输入变化
 * @param event - 输入事件
 */
const handleFileInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    handleFiles(target.files)
  }
  // 重置 input 以允许选择相同文件
  target.value = ''
}

/**
 * 触发文件选择
 */
const triggerFileSelect = () => {
  fileInput.value?.click()
}

/**
 * 移除文件
 * @param index - 文件索引
 */
const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

/**
 * 清空所有文件
 */
const clearFiles = () => {
  selectedFiles.value = []
}

/**
 * 上传所有文件
 */
const uploadFiles = async () => {
  if (selectedFiles.value.length === 0 || isUploading.value) return

  isUploading.value = true

  try {
    // 逐个上传文件
    for (const file of selectedFiles.value) {
      await documentsStore.uploadDocument(file)
    }

    // 清空选中文件
    selectedFiles.value = []

    // 触发上传完成事件
    emit('uploaded')
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    isUploading.value = false
  }
}

/**
 * 关闭对话框
 */
const close = () => {
  if (!isUploading.value) {
    emit('close')
  }
}

/**
 * 获取上传进度
 * @param fileName - 文件名
 */
const getUploadProgress = (fileName: string): UploadProgress | undefined => {
  return documentsStore.uploadProgress.find(p => p.fileName === fileName)
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">上传文档</h2>
        <button
          @click="close"
          :disabled="isUploading"
          class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-auto p-4">
        <!-- 拖拽上传区域 -->
        <div
          class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
          :class="isDragging 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'"
          @dragenter="handleDragEnter"
          @dragleave="handleDragLeave"
          @dragover="handleDragOver"
          @drop="handleDrop"
          @click="triggerFileSelect"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.md,.markdown,.txt,.docx,.html,.htm"
            class="hidden"
            @change="handleFileInput"
          />

          <div class="flex flex-col items-center">
            <!-- 上传图标 -->
            <div class="w-16 h-16 mb-4 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <svg class="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>

            <!-- 提示文字 -->
            <p class="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {{ isDragging ? '松开鼠标上传文件' : '拖拽文件到此处上传' }}
            </p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
              或点击选择文件
            </p>
            <p class="text-xs text-gray-400 dark:text-gray-500">
              支持的文件类型: {{ allowedTypesDescription }}，最大 50MB
            </p>
          </div>
        </div>

        <!-- 已选文件列表 -->
        <div v-if="hasFiles" class="mt-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">
              已选择 {{ selectedFiles.length }} 个文件
            </h3>
            <button
              @click="clearFiles"
              :disabled="isUploading"
              class="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
            >
              清空
            </button>
          </div>

          <ul class="space-y-2">
            <li
              v-for="(file, index) in selectedFiles"
              :key="index"
              class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <!-- 文件图标 -->
              <span class="text-2xl">{{ getFileIcon(file) }}</span>

              <!-- 文件信息 -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ file.name }}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ formatFileSize(file.size) }}
                </p>
              </div>

              <!-- 上传进度 -->
              <div v-if="getUploadProgress(file.name)" class="flex items-center gap-2">
                <div class="w-24 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-blue-600 transition-all duration-300"
                    :style="{ width: `${getUploadProgress(file.name)?.progress || 0}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400 w-10 text-right">
                  {{ getUploadProgress(file.name)?.progress || 0 }}%
                </span>
              </div>

              <!-- 移除按钮 -->
              <button
                v-if="!isUploading"
                @click.stop="removeFile(index)"
                class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </li>
          </ul>
        </div>

        <!-- 上传进度列表 -->
        <div v-if="documentsStore.uploadProgress.length > 0" class="mt-4">
          <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            上传进度
          </h3>
          <ul class="space-y-2">
            <li
              v-for="progress in documentsStore.uploadProgress"
              :key="progress.fileId"
              class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <!-- 状态图标 -->
              <div class="w-6 h-6 flex items-center justify-center">
                <svg
                  v-if="progress.status === 'uploading' || progress.status === 'processing'"
                  class="w-5 h-5 text-blue-600 animate-spin"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <svg
                  v-else-if="progress.status === 'completed'"
                  class="w-5 h-5 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <svg
                  v-else-if="progress.status === 'failed'"
                  class="w-5 h-5 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>

              <!-- 文件名 -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ progress.fileName }}
                </p>
                <p v-if="progress.error" class="text-xs text-red-600 dark:text-red-400">
                  {{ progress.error }}
                </p>
              </div>

              <!-- 进度条 -->
              <div class="flex items-center gap-2">
                <div class="w-24 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                  <div
                    class="h-full transition-all duration-300"
                    :class="{
                      'bg-blue-600': progress.status === 'uploading',
                      'bg-yellow-600': progress.status === 'processing',
                      'bg-green-600': progress.status === 'completed',
                      'bg-red-600': progress.status === 'failed'
                    }"
                    :style="{ width: `${progress.progress}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400 w-10 text-right">
                  {{ progress.progress }}%
                </span>
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="flex items-center justify-end gap-3 p-4 border-t dark:border-gray-700">
        <button
          @click="close"
          :disabled="isUploading"
          class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 disabled:opacity-50"
        >
          取消
        </button>
        <button
          @click="uploadFiles"
          :disabled="!hasFiles || isUploading"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg
            v-if="isUploading"
            class="w-4 h-4 animate-spin"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ isUploading ? '上传中...' : '开始上传' }}
        </button>
      </div>
    </div>
  </div>
</template>
