/**
 * 模型管理状态管理 Store
 * 管理 AI 模型配置和状态，连接后端 API
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ModelConfig,
  CreateModelConfigRequest,
  UpdateModelConfigRequest,
  ModelStatus,
  ModelTestResult,
  ProviderConfig,
  AvailableModel,
  ModelConfigListResponse,
  ProvidersResponse
} from '@/types'

/**
 * API 基础 URL
 */
const API_BASE_URL = 'http://localhost:8000/api/v1'

/**
 * 模型管理 Store
 */
export const useModelsStore = defineStore('models', () => {
  // ==================== 状态 ====================

  /**
   * 模型列表
   */
  const models = ref<ModelConfig[]>([])

  /**
   * 提供商配置
   */
  const providers = ref<Record<string, ProviderConfig>>({})

  /**
   * 是否正在加载
   */
  const isLoading = ref(false)

  /**
   * 错误信息
   */
  const error = ref<string | null>(null)

  /**
   * 模型状态缓存
   */
  const modelStatusCache = ref<Record<number, ModelStatus>>({})

  /**
   * 当前选中的模型 ID
   */
  const currentModelId = ref<number | null>(null)

  // ==================== 计算属性 ====================

  /**
   * 已启用的模型列表
   */
  const enabledModels = computed(() => {
    return models.value.filter(m => m.is_active)
  })

  /**
   * 默认模型
   */
  const defaultModel = computed(() => {
    return models.value.find(m => m.is_default && m.is_active) || enabledModels.value[0] || null
  })

  /**
   * 模型总数
   */
  const totalModels = computed(() => models.value.length)

  /**
   * 已启用模型数量
   */
  const enabledCount = computed(() => enabledModels.value.length)

  /**
   * 当前选中的模型
   */
  const currentModel = computed(() => {
    if (currentModelId.value) {
      return models.value.find(m => m.id === currentModelId.value) || defaultModel.value
    }
    return defaultModel.value
  })

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

  // ==================== 模型 CRUD 方法 ====================

  /**
   * 获取模型列表
   * @param params - 查询参数
   */
  const fetchModels = async (params?: {
    provider?: string
    model_type?: string
    is_active?: boolean
    include_inactive?: boolean
  }): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams()
      if (params?.provider) queryParams.append('provider', params.provider)
      if (params?.model_type) queryParams.append('model_type', params.model_type)
      if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active))
      if (params?.include_inactive) queryParams.append('include_inactive', 'true')

      const queryString = queryParams.toString()
      const url = `/models/${queryString ? `?${queryString}` : ''}`

      const response: ModelConfigListResponse = await fetchApi(url)
      models.value = response.items
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取模型列表失败'
      console.error('获取模型列表失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 获取单个模型详情
   * @param modelId - 模型 ID
   */
  const fetchModelById = async (modelId: number): Promise<ModelConfig | null> => {
    try {
      const model = await fetchApi<ModelConfig>(`/models/${modelId}`)
      return model
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取模型详情失败'
      console.error('获取模型详情失败:', e)
      return null
    }
  }

  /**
   * 创建新模型
   * @param modelData - 模型创建数据
   */
  const createModel = async (modelData: CreateModelConfigRequest): Promise<ModelConfig | null> => {
    isLoading.value = true
    error.value = null

    try {
      const model = await fetchApi<ModelConfig>('/models/', {
        method: 'POST',
        body: JSON.stringify(modelData),
      })

      models.value.push(model)

      // 如果是默认模型，更新其他模型
      if (model.is_default) {
        models.value = models.value.map(m => ({
          ...m,
          is_default: m.id === model.id
        }))
      }

      return model
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建模型失败'
      console.error('创建模型失败:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新模型配置
   * @param modelId - 模型 ID
   * @param updates - 更新的字段
   */
  const updateModel = async (
    modelId: number,
    updates: UpdateModelConfigRequest
  ): Promise<ModelConfig | null> => {
    isLoading.value = true
    error.value = null

    try {
      const model = await fetchApi<ModelConfig>(`/models/${modelId}`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      })

      // 更新本地列表
      const index = models.value.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models.value[index] = model
      }

      // 如果设为默认，更新其他模型
      if (model.is_default) {
        models.value = models.value.map(m => ({
          ...m,
          is_default: m.id === model.id
        }))
      }

      return model
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新模型失败'
      console.error('更新模型失败:', e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除模型
   * @param modelId - 模型 ID
   */
  const deleteModel = async (modelId: number): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      await fetchApi<void>(`/models/${modelId}`, {
        method: 'DELETE',
      })

      // 从本地列表移除
      const index = models.value.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models.value.splice(index, 1)
      }

      // 清除状态缓存
      delete modelStatusCache.value[modelId]

      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除模型失败'
      console.error('删除模型失败:', e)
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 设置默认模型
   * @param modelId - 模型 ID
   */
  const setDefaultModel = async (modelId: number): Promise<ModelConfig | null> => {
    try {
      const model = await fetchApi<ModelConfig>(`/models/${modelId}/set-default`, {
        method: 'POST',
      })

      // 更新本地列表
      models.value = models.value.map(m => ({
        ...m,
        is_default: m.id === modelId
      }))

      return model
    } catch (e) {
      error.value = e instanceof Error ? e.message : '设置默认模型失败'
      console.error('设置默认模型失败:', e)
      return null
    }
  }

  /**
   * 切换模型启用状态
   * @param modelId - 模型 ID
   */
  const toggleModel = async (modelId: number): Promise<ModelConfig | null> => {
    try {
      const model = await fetchApi<ModelConfig>(`/models/${modelId}/toggle`, {
        method: 'POST',
      })

      // 更新本地列表
      const index = models.value.findIndex(m => m.id === modelId)
      if (index !== -1) {
        models.value[index] = model
      }

      return model
    } catch (e) {
      error.value = e instanceof Error ? e.message : '切换模型状态失败'
      console.error('切换模型状态失败:', e)
      return null
    }
  }

  // ==================== 模型状态方法 ====================

  /**
   * 获取模型状态
   * @param modelId - 模型 ID
   */
  const fetchModelStatus = async (modelId: number): Promise<ModelStatus | null> => {
    try {
      const status = await fetchApi<ModelStatus>(`/models/${modelId}/status`)
      modelStatusCache.value[modelId] = status
      return status
    } catch (e) {
      console.error('获取模型状态失败:', e)
      return null
    }
  }

  /**
   * 测试模型连接
   * @param modelId - 模型 ID
   */
  const testModelConnection = async (modelId: number): Promise<ModelTestResult | null> => {
    try {
      const result = await fetchApi<ModelTestResult>(`/models/${modelId}/test`, {
        method: 'POST',
      })
      return result
    } catch (e) {
      console.error('测试模型连接失败:', e)
      return {
        success: false,
        message: e instanceof Error ? e.message : '测试失败',
        tested_at: new Date().toISOString(),
      }
    }
  }

  // ==================== 提供商方法 ====================

  /**
   * 获取支持的提供商列表
   */
  const fetchProviders = async (): Promise<void> => {
    try {
      const response: ProvidersResponse = await fetchApi('/models/providers')
      providers.value = response.providers
    } catch (e) {
      console.error('获取提供商列表失败:', e)
    }
  }

  /**
   * 获取提供商可用模型列表
   * @param provider - 提供商名称
   */
  const fetchProviderModels = async (provider: string): Promise<AvailableModel[]> => {
    try {
      const models = await fetchApi<AvailableModel[]>(`/models/providers/${provider}/models`)
      return models
    } catch (e) {
      console.error('获取提供商模型列表失败:', e)
      return []
    }
  }

  // ==================== 辅助方法 ====================

  /**
   * 根据 ID 获取模型
   * @param modelId - 模型 ID
   */
  const getModelById = (modelId: number): ModelConfig | undefined => {
    return models.value.find(m => m.id === modelId)
  }

  /**
   * 根据提供商筛选模型
   * @param provider - 提供商类型
   */
  const getModelsByProvider = (provider: string): ModelConfig[] => {
    return models.value.filter(m => m.provider === provider)
  }

  /**
   * 设置当前模型
   * @param modelId - 模型 ID
   */
  const setCurrentModel = (modelId: number | null): void => {
    currentModelId.value = modelId
  }

  /**
   * 清空所有数据
   */
  const clearAll = (): void => {
    models.value = []
    providers.value = {}
    modelStatusCache.value = {}
    currentModelId.value = null
    error.value = null
  }

  /**
   * 初始化 Store
   */
  const initialize = async (): Promise<void> => {
    await Promise.all([
      fetchModels(),
      fetchProviders(),
    ])
  }

  return {
    // 状态
    models,
    providers,
    isLoading,
    error,
    modelStatusCache,
    currentModelId,

    // 计算属性
    enabledModels,
    defaultModel,
    totalModels,
    enabledCount,
    currentModel,

    // 模型 CRUD 方法
    fetchModels,
    fetchModelById,
    createModel,
    updateModel,
    deleteModel,
    setDefaultModel,
    toggleModel,

    // 模型状态方法
    fetchModelStatus,
    testModelConnection,

    // 提供商方法
    fetchProviders,
    fetchProviderModels,

    // 辅助方法
    getModelById,
    getModelsByProvider,
    setCurrentModel,
    clearAll,
    initialize,
  }
})
