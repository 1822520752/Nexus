/**
 * API 请求组合式函数
 * 封装 HTTP 请求逻辑
 */
import { ref, type Ref } from 'vue'
import type { ApiResponse } from '@/types'

/**
 * API 请求配置接口
 */
interface UseApiOptions {
  baseUrl?: string
  headers?: Record<string, string>
}

/**
 * API 请求状态接口
 */
interface UseApiReturn<T> {
  data: Ref<T | null>
  error: Ref<string | null>
  isLoading: Ref<boolean>
  execute: (url: string, options?: RequestInit) => Promise<T | null>
  get: (url: string) => Promise<T | null>
  post: (url: string, body?: unknown) => Promise<T | null>
  put: (url: string, body?: unknown) => Promise<T | null>
  del: (url: string) => Promise<T | null>
}

/**
 * 使用 API 请求的组合式函数
 * @param options - 配置选项
 */
export function useApi<T = unknown>(options: UseApiOptions = {}): UseApiReturn<T> {
  const baseUrl = options.baseUrl || 'http://localhost:8000/api/v1'
  
  const data = ref<T | null>(null) as Ref<T | null>
  const error = ref<string | null>(null)
  const isLoading = ref(false)

  /**
   * 执行请求
   * @param url - 请求 URL
   * @param options - 请求选项
   */
  const execute = async (url: string, init?: RequestInit): Promise<T | null> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await fetch(`${baseUrl}${url}`, {
        ...init,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
          ...init?.headers,
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result: ApiResponse<T> = await response.json()
      
      if (!result.success && result.error) {
        throw new Error(result.error.message)
      }

      data.value = result.data ?? null
      return data.value
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      console.error('API 请求失败:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * GET 请求
   * @param url - 请求 URL
   */
  const get = (url: string): Promise<T | null> => {
    return execute(url, { method: 'GET' })
  }

  /**
   * POST 请求
   * @param url - 请求 URL
   * @param body - 请求体
   */
  const post = (url: string, body?: unknown): Promise<T | null> => {
    return execute(url, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  /**
   * PUT 请求
   * @param url - 请求 URL
   * @param body - 请求体
   */
  const put = (url: string, body?: unknown): Promise<T | null> => {
    return execute(url, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  /**
   * DELETE 请求
   * @param url - 请求 URL
   */
  const del = (url: string): Promise<T | null> => {
    return execute(url, { method: 'DELETE' })
  }

  return {
    data,
    error,
    isLoading,
    execute,
    get,
    post,
    put,
    del,
  }
}
