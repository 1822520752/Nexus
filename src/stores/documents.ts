/**
 * 文档管理状态管理 Store
 * 管理文档列表、上传进度和文档详情
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Document,
  DocumentChunk,
  UploadProgress,
  DocumentListResponse,
  DocumentDetailResponse,
  DocumentStatus,
  DocumentType
} from '@/types'

/**
 * API 基础 URL
 */
const API_BASE_URL = 'http://localhost:8000/api/v1'

/**
 * 允许上传的文件类型
 */
const ALLOWED_FILE_TYPES: DocumentType[] = ['pdf', 'md', 'txt', 'docx', 'html']

/**
 * 最大文件大小 (50MB)
 */
const MAX_FILE_SIZE = 50 * 1024 * 1024

/**
 * 文档管理 Store
 */
export const useDocumentsStore = defineStore('documents', () => {
  // ==================== 状态 ====================

  /**
   * 文档列表
   */
  const documents = ref<Document[]>([])

  /**
   * 当前选中的文档
   */
  const currentDocument = ref<Document | null>(null)

  /**
   * 当前文档的分块列表
   */
  const currentChunks = ref<DocumentChunk[]>([])

  /**
   * 上传进度列表
   */
  const uploadProgress = ref<UploadProgress[]>([])

  /**
   * 是否正在加载
   */
  const isLoading = ref(false)

  /**
   * 错误信息
   */
  const error = ref<string | null>(null)

  /**
   * 分页信息
   */
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0
  })

  /**
   * 选中的文档 ID 列表（用于批量操作）
   */
  const selectedIds = ref<number[]>([])

  // ==================== 计算属性 ====================

  /**
   * 文档总数
   */
  const totalDocuments = computed(() => documents.value.length)

  /**
   * 正在上传的文件数量
   */
  const uploadingCount = computed(() => 
    uploadProgress.value.filter(p => p.status === 'uploading' || p.status === 'processing').length
  )

  /**
   * 是否有选中的文档
   */
  const hasSelection = computed(() => selectedIds.value.length > 0)

  /**
   * 是否全选
   */
  const isAllSelected = computed(() => 
    documents.value.length > 0 && selectedIds.value.length === documents.value.length
  )

  // ==================== API 请求方法 ====================

  /**
   * 发送 API 请求
   * @param url - 请求 URL
   * @param options - 请求选项
   */
  const fetchApi = async <T>(url: string, options?: RequestInit): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    // 处理 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  // ==================== 文档 CRUD 方法 ====================

  /**
   * 获取文档列表
   * @param params - 查询参数
   */
  const fetchDocuments = async (params?: {
    status?: DocumentStatus
    file_type?: DocumentType
    search?: string
    page?: number
    pageSize?: number
  }): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params?.status) queryParams.append('status', params.status)
      if (params?.file_type) queryParams.append('file_type', params.file_type)
      if (params?.search) queryParams.append('search', params.search)
      if (params?.page) queryParams.append('page', String(params.page))
      if (params?.pageSize) queryParams.append('pageSize', String(params.pageSize))

      const queryString = queryParams.toString()
      const url = `/documents/${queryString ? `?${queryString}` : ''}`

      const response: DocumentListResponse = await fetchApi(url)
      documents.value = response.items
      pagination.value.total = response.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取文档列表失败'
      console.error('获取文档列表失败: - documents.ts:168', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取单个文档详情
   * @param documentId - 文档 ID
   */
  const fetchDocumentById = async (documentId: number): Promise<Document | null> => {
    isLoading.value = true
    error.value = null

    try {
      const response: DocumentDetailResponse = await fetchApi(`/documents/${documentId}`)
      currentDocument.value = response.document
      currentChunks.value = response.chunks
      return response.document
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取文档详情失败'
      console.error('获取文档详情失败: - documents.ts:189', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 上传文档
   * @param file - 要上传的文件
   */
  const uploadDocument = async (file: File): Promise<Document | null> => {
    // 验证文件类型
    const fileExtension = file.name.split('.').pop()?.toLowerCase() as DocumentType
    if (!ALLOWED_FILE_TYPES.includes(fileExtension)) {
      error.value = `不支持的文件类型: ${fileExtension}`
      return null
    }

    // 验证文件大小
    if (file.size > MAX_FILE_SIZE) {
      error.value = `文件大小超过限制 (最大 ${MAX_FILE_SIZE / 1024 / 1024}MB)`
      return null
    }

    // 创建上传进度记录
    const progressId = `upload-${Date.now()}`
    const progress: UploadProgress = {
      fileId: progressId,
      fileName: file.name,
      progress: 0,
      status: 'uploading'
    }
    uploadProgress.value.push(progress)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const xhr = new XMLHttpRequest()

      // 监听上传进度
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100)
          const progressItem = uploadProgress.value.find(p => p.fileId === progressId)
          if (progressItem) {
            progressItem.progress = percentComplete
          }
        }
      })

      // 创建 Promise 处理响应
      const result = await new Promise<Document>((resolve, reject) => {
        xhr.onload = () => {
          const progressItem = uploadProgress.value.find(p => p.fileId === progressId)
          
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText)
              if (progressItem) {
                progressItem.status = 'processing'
                progressItem.progress = 100
              }
              resolve(response)
            } catch {
              reject(new Error('解析响应失败'))
            }
          } else {
            if (progressItem) {
              progressItem.status = 'failed'
              progressItem.error = '上传失败'
            }
            reject(new Error(`上传失败: ${xhr.statusText}`))
          }
        }

        xhr.onerror = () => {
          const progressItem = uploadProgress.value.find(p => p.fileId === progressId)
          if (progressItem) {
            progressItem.status = 'failed'
            progressItem.error = '网络错误'
          }
          reject(new Error('网络错误'))
        }

        xhr.open('POST', `${API_BASE_URL}/documents/`)
        xhr.send(formData)
      })

      // 添加到文档列表
      documents.value.unshift(result)
      pagination.value.total += 1

      // 更新进度状态为完成
      const progressItem = uploadProgress.value.find(p => p.fileId === progressId)
      if (progressItem) {
        progressItem.status = 'completed'
      }

      // 5秒后移除进度记录
      setTimeout(() => {
        const index = uploadProgress.value.findIndex(p => p.fileId === progressId)
        if (index !== -1) {
          uploadProgress.value.splice(index, 1)
        }
      }, 5000)

      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : '上传文档失败'
      console.error('上传文档失败: - documents.ts:300', e)
      return null
    }
  }

  /**
   * 更新文档信息
   * @param documentId - 文档 ID
   * @param updates - 更新的字段
   */
  const updateDocument = async (
    documentId: number,
    updates: { filename?: string }
  ): Promise<Document | null> => {
    isLoading.value = true
    error.value = null

    try {
      const document = await fetchApi<Document>(`/documents/${documentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      })

      // 更新本地列表
      const index = documents.value.findIndex(d => d.id === documentId)
      if (index !== -1) {
        documents.value[index] = document
      }

      // 更新当前文档
      if (currentDocument.value?.id === documentId) {
        currentDocument.value = document
      }

      return document
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新文档失败'
      console.error('更新文档失败: - documents.ts:340', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除文档
   * @param documentId - 文档 ID
   */
  const deleteDocument = async (documentId: number): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await fetchApi<void>(`/documents/${documentId}`, {
        method: 'DELETE',
      })

      // 从本地列表移除
      const index = documents.value.findIndex(d => d.id === documentId)
      if (index !== -1) {
        documents.value.splice(index, 1)
        pagination.value.total -= 1
      }

      // 从选中列表移除
      const selectedIndex = selectedIds.value.indexOf(documentId)
      if (selectedIndex !== -1) {
        selectedIds.value.splice(selectedIndex, 1)
      }

      // 清除当前文档
      if (currentDocument.value?.id === documentId) {
        currentDocument.value = null
        currentChunks.value = []
      }

      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除文档失败'
      console.error('删除文档失败: - documents.ts:382', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 批量删除文档
   * @param documentIds - 文档 ID 列表
   */
  const deleteDocuments = async (documentIds: number[]): Promise<{ success: number; failed: number }> => {
    let success = 0
    let failed = 0

    for (const id of documentIds) {
      const result = await deleteDocument(id)
      if (result) {
        success++
      } else {
        failed++
      }
    }

    return { success, failed }
  }

  // ==================== 选择操作方法 ====================

  /**
   * 切换文档选择状态
   * @param documentId - 文档 ID
   */
  const toggleSelection = (documentId: number): void => {
    const index = selectedIds.value.indexOf(documentId)
    if (index === -1) {
      selectedIds.value.push(documentId)
    } else {
      selectedIds.value.splice(index, 1)
    }
  }

  /**
   * 全选/取消全选
   */
  const toggleSelectAll = (): void => {
    if (isAllSelected.value) {
      selectedIds.value = []
    } else {
      selectedIds.value = documents.value.map(d => d.id)
    }
  }

  /**
   * 清除选择
   */
  const clearSelection = (): void => {
    selectedIds.value = []
  }

  // ==================== 分页方法 ====================

  /**
   * 设置页码
   * @param page - 页码
   */
  const setPage = (page: number): void => {
    pagination.value.page = page
  }

  /**
   * 设置每页数量
   * @param pageSize - 每页数量
   */
  const setPageSize = (pageSize: number): void => {
    pagination.value.pageSize = pageSize
    pagination.value.page = 1
  }

  // ==================== 辅助方法 ====================

  /**
   * 清除当前文档
   */
  const clearCurrentDocument = (): void => {
    currentDocument.value = null
    currentChunks.value = []
  }

  /**
   * 清除所有数据
   */
  const clearAll = (): void => {
    documents.value = []
    currentDocument.value = null
    currentChunks.value = []
    uploadProgress.value = []
    selectedIds.value = []
    error.value = null
    pagination.value = { page: 1, pageSize: 10, total: 0 }
  }

  /**
   * 初始化 Store
   */
  const initialize = async (): Promise<void> => {
    await fetchDocuments()
  }

  return {
    // 状态
    documents,
    currentDocument,
    currentChunks,
    uploadProgress,
    isLoading,
    error,
    pagination,
    selectedIds,

    // 计算属性
    totalDocuments,
    uploadingCount,
    hasSelection,
    isAllSelected,

    // 文档 CRUD 方法
    fetchDocuments,
    fetchDocumentById,
    uploadDocument,
    updateDocument,
    deleteDocument,
    deleteDocuments,

    // 选择操作方法
    toggleSelection,
    toggleSelectAll,
    clearSelection,

    // 分页方法
    setPage,
    setPageSize,

    // 辅助方法
    clearCurrentDocument,
    clearAll,
    initialize,
  }
})
