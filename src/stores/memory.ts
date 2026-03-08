/**
 * 记忆管理状态管理 Store
 * 管理记忆列表、当前记忆、搜索结果等
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Memory,
  MemoryType,
  MemorySearchParams,
  MemoryListResponse,
  CreateMemoryRequest,
  UpdateMemoryRequest
} from '@/types'

/**
 * API 基础 URL
 */
const API_BASE_URL = 'http://localhost:8000/api/v1'

/**
 * 记忆管理 Store
 */
export const useMemoryStore = defineStore('memory', () => {
  // ==================== 状态 ====================

  /**
   * 记忆列表
   */
  const memories = ref<Memory[]>([])

  /**
   * 当前选中的记忆
   */
  const currentMemory = ref<Memory | null>(null)

  /**
   * 搜索结果列表
   */
  const searchResults = ref<Memory[]>([])

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
   * 当前筛选类型
   */
  const filterType = ref<MemoryType | ''>('')

  /**
   * 选中的记忆 ID 列表（用于批量操作）
   */
  const selectedIds = ref<string[]>([])

  // ==================== 计算属性 ====================

  /**
   * 记忆总数
   */
  const totalMemories = computed(() => memories.value.length)

  /**
   * 是否有选中的记忆
   */
  const hasSelection = computed(() => selectedIds.value.length > 0)

  /**
   * 是否全选
   */
  const isAllSelected = computed(() =>
    memories.value.length > 0 && selectedIds.value.length === memories.value.length
  )

  /**
   * 按类型分组的记忆
   */
  const memoriesByType = computed(() => {
    const grouped: Record<MemoryType, Memory[]> = {
      instant: [],
      working: [],
      long_term: []
    }
    memories.value.forEach(memory => {
      grouped[memory.memoryType].push(memory)
    })
    return grouped
  })

  /**
   * 高重要性记忆（重要性 >= 7）
   */
  const highImportanceMemories = computed(() =>
    memories.value.filter(m => m.importance >= 7)
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
        'Content-Type': 'application/json',
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

  // ==================== 记忆 CRUD 方法 ====================

  /**
   * 获取记忆列表
   * @param params - 查询参数
   */
  const fetchMemories = async (params?: {
    memoryType?: MemoryType
    page?: number
    pageSize?: number
  }): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params?.memoryType) queryParams.append('memory_type', params.memoryType)
      if (params?.page) queryParams.append('page', String(params.page))
      if (params?.pageSize) queryParams.append('page_size', String(params.pageSize))

      const queryString = queryParams.toString()
      const url = `/memories/${queryString ? `?${queryString}` : ''}`

      const response: MemoryListResponse = await fetchApi(url)
      memories.value = response.items
      pagination.value.total = response.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取记忆列表失败'
      console.error('获取记忆列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取单个记忆详情
   * @param memoryId - 记忆 ID
   */
  const fetchMemoryById = async (memoryId: string): Promise<Memory | null> => {
    isLoading.value = true
    error.value = null

    try {
      const memory = await fetchApi<Memory>(`/memories/${memoryId}`)
      currentMemory.value = memory
      return memory
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取记忆详情失败'
      console.error('获取记忆详情失败:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 创建记忆
   * @param data - 创建请求数据
   */
  const createMemory = async (data: CreateMemoryRequest): Promise<Memory | null> => {
    isLoading.value = true
    error.value = null

    try {
      const memory = await fetchApi<Memory>('/memories/', {
        method: 'POST',
        body: JSON.stringify(data),
      })

      // 添加到记忆列表
      memories.value.unshift(memory)
      pagination.value.total += 1

      return memory
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建记忆失败'
      console.error('创建记忆失败:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新记忆
   * @param memoryId - 记忆 ID
   * @param updates - 更新的字段
   */
  const updateMemory = async (
    memoryId: string,
    updates: UpdateMemoryRequest
  ): Promise<Memory | null> => {
    isLoading.value = true
    error.value = null

    try {
      const memory = await fetchApi<Memory>(`/memories/${memoryId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      })

      // 更新本地列表
      const index = memories.value.findIndex(m => m.id === memoryId)
      if (index !== -1) {
        memories.value[index] = memory
      }

      // 更新当前记忆
      if (currentMemory.value?.id === memoryId) {
        currentMemory.value = memory
      }

      // 更新搜索结果
      const searchIndex = searchResults.value.findIndex(m => m.id === memoryId)
      if (searchIndex !== -1) {
        searchResults.value[searchIndex] = memory
      }

      return memory
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新记忆失败'
      console.error('更新记忆失败:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除记忆
   * @param memoryId - 记忆 ID
   */
  const deleteMemory = async (memoryId: string): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await fetchApi<void>(`/memories/${memoryId}`, {
        method: 'DELETE',
      })

      // 从本地列表移除
      const index = memories.value.findIndex(m => m.id === memoryId)
      if (index !== -1) {
        memories.value.splice(index, 1)
        pagination.value.total -= 1
      }

      // 从搜索结果移除
      const searchIndex = searchResults.value.findIndex(m => m.id === memoryId)
      if (searchIndex !== -1) {
        searchResults.value.splice(searchIndex, 1)
      }

      // 从选中列表移除
      const selectedIndex = selectedIds.value.indexOf(memoryId)
      if (selectedIndex !== -1) {
        selectedIds.value.splice(selectedIndex, 1)
      }

      // 清除当前记忆
      if (currentMemory.value?.id === memoryId) {
        currentMemory.value = null
      }

      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除记忆失败'
      console.error('删除记忆失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 批量删除记忆
   * @param memoryIds - 记忆 ID 列表
   */
  const deleteMemories = async (memoryIds: string[]): Promise<{ success: number; failed: number }> => {
    let success = 0
    let failed = 0

    for (const id of memoryIds) {
      const result = await deleteMemory(id)
      if (result) {
        success++
      } else {
        failed++
      }
    }

    return { success, failed }
  }

  // ==================== 搜索方法 ====================

  /**
   * 搜索记忆
   * @param params - 搜索参数
   */
  const searchMemories = async (params: MemorySearchParams): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params.query) queryParams.append('query', params.query)
      if (params.memoryType) queryParams.append('memory_type', params.memoryType)
      if (params.minImportance !== undefined) queryParams.append('min_importance', String(params.minImportance))
      if (params.maxImportance !== undefined) queryParams.append('max_importance', String(params.maxImportance))
      if (params.startDate) queryParams.append('start_date', params.startDate)
      if (params.endDate) queryParams.append('end_date', params.endDate)
      if (params.page) queryParams.append('page', String(params.page))
      if (params.pageSize) queryParams.append('page_size', String(params.pageSize))

      const queryString = queryParams.toString()
      const url = `/memories/search/${queryString ? `?${queryString}` : ''}`

      const response: MemoryListResponse = await fetchApi(url)
      searchResults.value = response.items
      pagination.value.total = response.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : '搜索记忆失败'
      console.error('搜索记忆失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 清除搜索结果
   */
  const clearSearchResults = (): void => {
    searchResults.value = []
  }

  // ==================== 选择操作方法 ====================

  /**
   * 切换记忆选择状态
   * @param memoryId - 记忆 ID
   */
  const toggleSelection = (memoryId: string): void => {
    const index = selectedIds.value.indexOf(memoryId)
    if (index === -1) {
      selectedIds.value.push(memoryId)
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
      selectedIds.value = memories.value.map(m => m.id)
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
   * 设置筛选类型
   * @param type - 记忆类型
   */
  const setFilterType = (type: MemoryType | ''): void => {
    filterType.value = type
    pagination.value.page = 1
  }

  /**
   * 清除当前记忆
   */
  const clearCurrentMemory = (): void => {
    currentMemory.value = null
  }

  /**
   * 清除所有数据
   */
  const clearAll = (): void => {
    memories.value = []
    currentMemory.value = null
    searchResults.value = []
    selectedIds.value = []
    error.value = null
    filterType.value = ''
    pagination.value = { page: 1, pageSize: 10, total: 0 }
  }

  /**
   * 初始化 Store
   */
  const initialize = async (): Promise<void> => {
    await fetchMemories()
  }

  return {
    // 状态
    memories,
    currentMemory,
    searchResults,
    isLoading,
    error,
    pagination,
    filterType,
    selectedIds,

    // 计算属性
    totalMemories,
    hasSelection,
    isAllSelected,
    memoriesByType,
    highImportanceMemories,

    // 记忆 CRUD 方法
    fetchMemories,
    fetchMemoryById,
    createMemory,
    updateMemory,
    deleteMemory,
    deleteMemories,

    // 搜索方法
    searchMemories,
    clearSearchResults,

    // 选择操作方法
    toggleSelection,
    toggleSelectAll,
    clearSelection,

    // 分页方法
    setPage,
    setPageSize,

    // 辅助方法
    setFilterType,
    clearCurrentMemory,
    clearAll,
    initialize,
  }
})
