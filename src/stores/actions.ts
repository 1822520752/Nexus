/**
 * 动作管理状态管理 Store
 * 管理动作定义、执行历史、权限设置和待确认队列
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ActionDefinition,
  ActionHistoryItem,
  PendingAction,
  PermissionSettings,
  ActionCategory,
  PermissionLevel,
  ActionStatus,
  defaultPermissionSettings
} from '@/types'
import { defaultPermissionSettings as defaultSettings } from '@/types'

/**
 * 本地存储键名
 */
const HISTORY_STORAGE_KEY = 'nexus-action-history'
const PERMISSION_STORAGE_KEY = 'nexus-permission-settings'

/**
 * 模拟动作定义数据
 * 实际项目中应从后端获取
 */
const mockActionDefinitions: ActionDefinition[] = [
  // 文件操作类
  {
    id: 'file-read',
    name: '读取文件',
    description: '读取指定路径的文件内容',
    category: 'file',
    permissionLevel: 'low',
    icon: '📄',
    params: [
      {
        name: 'path',
        type: 'path',
        required: true,
        description: '文件路径'
      }
    ],
    examples: ['读取 C:\\Users\\Documents\\note.txt'],
    requiresConfirmation: false
  },
  {
    id: 'file-write',
    name: '写入文件',
    description: '将内容写入指定文件',
    category: 'file',
    permissionLevel: 'medium',
    icon: '✏️',
    params: [
      {
        name: 'path',
        type: 'path',
        required: true,
        description: '文件路径'
      },
      {
        name: 'content',
        type: 'string',
        required: true,
        description: '写入内容'
      },
      {
        name: 'append',
        type: 'boolean',
        required: false,
        default: false,
        description: '是否追加模式'
      }
    ],
    examples: ['将 "Hello World" 写入 C:\\test.txt'],
    risks: ['可能覆盖现有文件内容'],
    requiresConfirmation: true
  },
  {
    id: 'file-delete',
    name: '删除文件',
    description: '删除指定路径的文件',
    category: 'file',
    permissionLevel: 'high',
    icon: '🗑️',
    params: [
      {
        name: 'path',
        type: 'path',
        required: true,
        description: '文件路径'
      }
    ],
    risks: ['删除操作不可恢复', '可能导致数据丢失'],
    requiresConfirmation: true
  },
  {
    id: 'file-list',
    name: '列出目录',
    description: '列出指定目录下的文件和子目录',
    category: 'file',
    permissionLevel: 'low',
    icon: '📁',
    params: [
      {
        name: 'path',
        type: 'path',
        required: true,
        description: '目录路径'
      },
      {
        name: 'recursive',
        type: 'boolean',
        required: false,
        default: false,
        description: '是否递归列出'
      }
    ],
    requiresConfirmation: false
  },
  // 笔记操作类
  {
    id: 'note-create',
    name: '创建笔记',
    description: '创建新的笔记条目',
    category: 'note',
    permissionLevel: 'low',
    icon: '📝',
    params: [
      {
        name: 'title',
        type: 'string',
        required: true,
        description: '笔记标题'
      },
      {
        name: 'content',
        type: 'string',
        required: true,
        description: '笔记内容'
      },
      {
        name: 'tags',
        type: 'string',
        required: false,
        description: '标签（逗号分隔）'
      }
    ],
    requiresConfirmation: false
  },
  {
    id: 'note-search',
    name: '搜索笔记',
    description: '根据关键词搜索笔记',
    category: 'note',
    permissionLevel: 'low',
    icon: '🔍',
    params: [
      {
        name: 'keyword',
        type: 'string',
        required: true,
        description: '搜索关键词'
      },
      {
        name: 'tags',
        type: 'string',
        required: false,
        description: '按标签过滤'
      }
    ],
    requiresConfirmation: false
  },
  // 系统操作类
  {
    id: 'system-info',
    name: '系统信息',
    description: '获取系统基本信息',
    category: 'system',
    permissionLevel: 'low',
    icon: '💻',
    params: [],
    requiresConfirmation: false
  },
  {
    id: 'system-process',
    name: '进程管理',
    description: '查看或管理系统进程',
    category: 'system',
    permissionLevel: 'high',
    icon: '⚙️',
    params: [
      {
        name: 'action',
        type: 'select',
        required: true,
        description: '操作类型',
        options: [
          { label: '列出进程', value: 'list' },
          { label: '结束进程', value: 'kill' }
        ]
      },
      {
        name: 'pid',
        type: 'number',
        required: false,
        description: '进程ID（结束进程时需要）'
      }
    ],
    risks: ['结束进程可能导致数据丢失', '可能影响系统稳定性'],
    requiresConfirmation: true
  },
  {
    id: 'system-clipboard',
    name: '剪贴板操作',
    description: '读取或写入系统剪贴板',
    category: 'system',
    permissionLevel: 'medium',
    icon: '📋',
    params: [
      {
        name: 'action',
        type: 'select',
        required: true,
        options: [
          { label: '读取', value: 'read' },
          { label: '写入', value: 'write' }
        ]
      },
      {
        name: 'content',
        type: 'string',
        required: false,
        description: '写入内容'
      }
    ],
    requiresConfirmation: false
  },
  // 脚本执行类
  {
    id: 'script-run',
    name: '执行脚本',
    description: '执行指定的脚本文件',
    category: 'script',
    permissionLevel: 'critical',
    icon: '⚡',
    params: [
      {
        name: 'path',
        type: 'path',
        required: true,
        description: '脚本路径'
      },
      {
        name: 'args',
        type: 'string',
        required: false,
        description: '脚本参数'
      }
    ],
    risks: ['脚本可能执行任意代码', '可能造成系统损坏', '可能泄露敏感信息'],
    requiresConfirmation: true
  },
  {
    id: 'script-command',
    name: '执行命令',
    description: '执行系统命令',
    category: 'script',
    permissionLevel: 'critical',
    icon: '🔧',
    params: [
      {
        name: 'command',
        type: 'string',
        required: true,
        description: '命令内容'
      }
    ],
    risks: ['命令可能执行任意操作', '高风险安全威胁'],
    requiresConfirmation: true
  }
]

export const useActionsStore = defineStore('actions', () => {
  // ==================== 状态 ====================

  /**
   * 可用动作列表
   */
  const actions = ref<ActionDefinition[]>([...mockActionDefinitions])

  /**
   * 动作执行历史
   */
  const history = ref<ActionHistoryItem[]>(loadHistory())

  /**
   * 待确认动作队列
   */
  const pendingActions = ref<PendingAction[]>([])

  /**
   * 权限设置
   */
  const permissionSettings = ref<PermissionSettings>(loadPermissionSettings())

  /**
   * 是否正在加载
   */
  const isLoading = ref(false)

  /**
   * 当前选中的动作
   */
  const selectedAction = ref<ActionDefinition | null>(null)

  // ==================== 计算属性 ====================

  /**
   * 按分类分组的动作
   */
  const actionsByCategory = computed(() => {
    const grouped: Record<ActionCategory, ActionDefinition[]> = {
      file: [],
      note: [],
      system: [],
      script: []
    }
    actions.value.forEach(action => {
      grouped[action.category].push(action)
    })
    return grouped
  })

  /**
   * 分类显示名称
   */
  const categoryNames: Record<ActionCategory, string> = {
    file: '文件操作',
    note: '笔记管理',
    system: '系统操作',
    script: '脚本执行'
  }

  /**
   * 权限级别显示名称
   */
  const permissionLevelNames: Record<PermissionLevel, string> = {
    low: '低风险',
    medium: '中等风险',
    high: '高风险',
    critical: '极高风险'
  }

  /**
   * 状态显示名称
   */
  const statusNames: Record<ActionStatus, string> = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }

  /**
   * 是否有待确认动作
   */
  const hasPendingActions = computed(() => pendingActions.value.length > 0)

  /**
   * 当前待确认动作
   */
  const currentPendingAction = computed(() => pendingActions.value[0] || null)

  // ==================== 方法 ====================

  /**
   * 根据ID获取动作定义
   * @param actionId - 动作ID
   */
  const getActionById = (actionId: string): ActionDefinition | undefined => {
    return actions.value.find(a => a.id === actionId)
  }

  /**
   * 搜索动作
   * @param keyword - 搜索关键词
   * @param category - 分类过滤（可选）
   */
  const searchActions = (keyword: string, category?: ActionCategory): ActionDefinition[] => {
    let results = actions.value
    
    if (category) {
      results = results.filter(a => a.category === category)
    }
    
    if (keyword.trim()) {
      const lowerKeyword = keyword.toLowerCase()
      results = results.filter(a => 
        a.name.toLowerCase().includes(lowerKeyword) ||
        a.description.toLowerCase().includes(lowerKeyword)
      )
    }
    
    return results
  }

  /**
   * 执行动作
   * @param actionId - 动作ID
   * @param params - 执行参数
   */
  const executeAction = async (
    actionId: string,
    params: Record<string, unknown>
  ): Promise<ActionHistoryItem> {
    const action = getActionById(actionId)
    if (!action) {
      throw new Error(`动作不存在: ${actionId}`)
    }

    // 检查是否需要确认
    if (needsConfirmation(action, params)) {
      return new Promise((resolve, reject) => {
        const pending: PendingAction = {
          id: `pending-${Date.now()}`,
          action,
          params,
          resolve: (confirmed: boolean) => {
            if (confirmed) {
              // 用户确认后执行
              doExecuteAction(action, params).then(resolve).catch(reject)
            } else {
              // 用户取消
              const cancelledItem: ActionHistoryItem = {
                id: `history-${Date.now()}`,
                actionId: action.id,
                actionName: action.name,
                category: action.category,
                status: 'cancelled',
                params,
                executedAt: new Date()
              }
              addToHistory(cancelledItem)
              reject(new Error('用户取消操作'))
            }
          },
          timestamp: new Date()
        }
        pendingActions.value.push(pending)
      })
    }

    return doExecuteAction(action, params)
  }

  /**
   * 实际执行动作
   * @param action - 动作定义
   * @param params - 执行参数
   */
  const doExecuteAction = async (
    action: ActionDefinition,
    params: Record<string, unknown>
  ): Promise<ActionHistoryItem> => {
    const startTime = new Date()
    const historyItem: ActionHistoryItem = {
      id: `history-${Date.now()}`,
      actionId: action.id,
      actionName: action.name,
      category: action.category,
      status: 'running',
      params,
      executedAt: startTime
    }

    // 添加到历史（运行中状态）
    addToHistory(historyItem)

    try {
      // 模拟执行动作
      // 实际项目中应调用后端API
      await simulateExecution(action, params)
      
      // 更新为成功状态
      historyItem.status = 'success'
      historyItem.result = { message: '执行成功' }
    } catch (error) {
      historyItem.status = 'failed'
      historyItem.error = error instanceof Error ? error.message : String(error)
    } finally {
      historyItem.duration = Date.now() - startTime.getTime()
      updateHistoryItem(historyItem)
    }

    return historyItem
  }

  /**
   * 模拟动作执行
   * @param action - 动作定义
   * @param params - 执行参数
   */
  const simulateExecution = async (
    action: ActionDefinition,
    params: Record<string, unknown>
  ): Promise<void> => {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000))
    
    // 模拟随机失败（10%概率）
    if (Math.random() < 0.1) {
      throw new Error('模拟执行失败')
    }
  }

  /**
   * 检查动作是否需要确认
   * @param action - 动作定义
   * @param params - 执行参数
   */
  const needsConfirmation = (
    action: ActionDefinition,
    params: Record<string, unknown>
  ): boolean => {
    // 安全模式下所有需要确认的动作都要确认
    if (permissionSettings.value.safeMode && action.requiresConfirmation) {
      return true
    }

    // 检查权限级别设置
    if (permissionSettings.value.confirmLevels[action.permissionLevel]) {
      return true
    }

    // 检查是否涉及敏感目录
    if (action.category === 'file' && params.path) {
      const path = String(params.path)
      for (const sensitivePath of permissionSettings.value.sensitiveDirectories) {
        if (path.startsWith(sensitivePath.replace('*', ''))) {
          return true
        }
      }
    }

    return false
  }

  /**
   * 确认待执行动作
   * @param pendingId - 待确认动作ID
   * @param confirmed - 是否确认
   */
  const confirmPendingAction = (pendingId: string, confirmed: boolean): void => {
    const index = pendingActions.value.findIndex(p => p.id === pendingId)
    if (index !== -1) {
      const pending = pendingActions.value[index]
      pendingActions.value.splice(index, 1)
      pending.resolve(confirmed)
    }
  }

  /**
   * 添加历史记录
   * @param item - 历史记录项
   */
  const addToHistory = (item: ActionHistoryItem): void => {
    history.value.unshift(item)
    // 限制历史记录数量
    if (history.value.length > 100) {
      history.value = history.value.slice(0, 100)
    }
    saveHistory()
  }

  /**
   * 更新历史记录项
   * @param item - 历史记录项
   */
  const updateHistoryItem = (item: ActionHistoryItem): void => {
    const index = history.value.findIndex(h => h.id === item.id)
    if (index !== -1) {
      history.value[index] = { ...item }
      saveHistory()
    }
  }

  /**
   * 清空历史记录
   */
  const clearHistory = (): void => {
    history.value = []
    saveHistory()
  }

  /**
   * 删除单条历史记录
   * @param itemId - 历史记录ID
   */
  const deleteHistoryItem = (itemId: string): void => {
    const index = history.value.findIndex(h => h.id === itemId)
    if (index !== -1) {
      history.value.splice(index, 1)
      saveHistory()
    }
  }

  /**
   * 重新执行历史动作
   * @param historyItem - 历史记录项
   */
  const reexecuteAction = async (historyItem: ActionHistoryItem): Promise<ActionHistoryItem> => {
    return executeAction(historyItem.actionId, historyItem.params)
  }

  /**
   * 更新权限设置
   * @param settings - 新设置
   */
  const updatePermissionSettings = (settings: Partial<PermissionSettings>): void => {
    Object.assign(permissionSettings.value, settings)
    savePermissionSettings()
  }

  /**
   * 重置权限设置
   */
  const resetPermissionSettings = (): void => {
    permissionSettings.value = { ...defaultSettings }
    savePermissionSettings()
  }

  /**
   * 添加敏感目录
   * @param path - 目录路径
   */
  const addSensitiveDirectory = (path: string): void => {
    if (!permissionSettings.value.sensitiveDirectories.includes(path)) {
      permissionSettings.value.sensitiveDirectories.push(path)
      savePermissionSettings()
    }
  }

  /**
   * 移除敏感目录
   * @param path - 目录路径
   */
  const removeSensitiveDirectory = (path: string): void => {
    const index = permissionSettings.value.sensitiveDirectories.indexOf(path)
    if (index !== -1) {
      permissionSettings.value.sensitiveDirectories.splice(index, 1)
      savePermissionSettings()
    }
  }

  /**
   * 设置选中的动作
   * @param action - 动作定义
   */
  const setSelectedAction = (action: ActionDefinition | null): void => {
    selectedAction.value = action
  }

  // ==================== 辅助函数 ====================

  /**
   * 从本地存储加载历史记录
   */
  function loadHistory(): ActionHistoryItem[] {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as ActionHistoryItem[]
        // 转换日期格式
        return parsed.map(item => ({
          ...item,
          executedAt: new Date(item.executedAt)
        }))
      }
    } catch (e) {
      console.error('加载历史记录失败: - actions.ts:684', e)
    }
    return []
  }

  /**
   * 保存历史记录到本地存储
   */
  function saveHistory(): void {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history.value))
    } catch (e) {
      console.error('保存历史记录失败: - actions.ts:696', e)
    }
  }

  /**
   * 从本地存储加载权限设置
   */
  function loadPermissionSettings(): PermissionSettings {
    try {
      const stored = localStorage.getItem(PERMISSION_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<PermissionSettings>
        return { ...defaultSettings, ...parsed }
      }
    } catch (e) {
      console.error('加载权限设置失败: - actions.ts:711', e)
    }
    return { ...defaultSettings }
  }

  /**
   * 保存权限设置到本地存储
   */
  function savePermissionSettings(): void {
    try {
      localStorage.setItem(PERMISSION_STORAGE_KEY, JSON.stringify(permissionSettings.value))
    } catch (e) {
      console.error('保存权限设置失败: - actions.ts:723', e)
    }
  }

  return {
    // 状态
    actions,
    history,
    pendingActions,
    permissionSettings,
    isLoading,
    selectedAction,

    // 计算属性
    actionsByCategory,
    categoryNames,
    permissionLevelNames,
    statusNames,
    hasPendingActions,
    currentPendingAction,

    // 方法
    getActionById,
    searchActions,
    executeAction,
    confirmPendingAction,
    addToHistory,
    updateHistoryItem,
    clearHistory,
    deleteHistoryItem,
    reexecuteAction,
    updatePermissionSettings,
    resetPermissionSettings,
    addSensitiveDirectory,
    removeSensitiveDirectory,
    setSelectedAction
  }
})
