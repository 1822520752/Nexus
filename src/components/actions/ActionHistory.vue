/**
 * 动作历史记录组件
 * 展示动作执行历史，支持过滤、查看详情和重新执行
 */
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useActionsStore } from '@/stores/actions'
import type { ActionHistoryItem, ActionStatus, ActionCategory } from '@/types'

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'reexecute', item: ActionHistoryItem): void
  (e: 'viewDetail', item: ActionHistoryItem): void
}>()

// Store
const actionsStore = useActionsStore()

// ==================== 响应式状态 ====================

/**
 * 状态过滤
 */
const statusFilter = ref<ActionStatus | 'all'>('all')

/**
 * 分类过滤
 */
const categoryFilter = ref<ActionCategory | 'all'>('all')

/**
 * 时间范围过滤
 */
const timeRangeFilter = ref<'today' | 'week' | 'month' | 'all'>('all')

/**
 * 选中的历史项
 */
const selectedItem = ref<ActionHistoryItem | null>(null)

/**
 * 是否显示详情面板
 */
const showDetailPanel = ref(false)

// ==================== 计算属性 ====================

/**
 * 过滤后的历史记录
 */
const filteredHistory = computed(() => {
  let items = [...actionsStore.history]

  // 状态过滤
  if (statusFilter.value !== 'all') {
    items = items.filter(item => item.status === statusFilter.value)
  }

  // 分类过滤
  if (categoryFilter.value !== 'all') {
    items = items.filter(item => item.category === categoryFilter.value)
  }

  // 时间范围过滤
  const now = new Date()
  if (timeRangeFilter.value === 'today') {
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    items = items.filter(item => new Date(item.executedAt) >= today)
  } else if (timeRangeFilter.value === 'week') {
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    items = items.filter(item => new Date(item.executedAt) >= weekAgo)
  } else if (timeRangeFilter.value === 'month') {
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    items = items.filter(item => new Date(item.executedAt) >= monthAgo)
  }

  return items
})

/**
 * 统计信息
 */
const statistics = computed(() => {
  const total = actionsStore.history.length
  const success = actionsStore.history.filter(h => h.status === 'success').length
  const failed = actionsStore.history.filter(h => h.status === 'failed').length
  const cancelled = actionsStore.history.filter(h => h.status === 'cancelled').length
  return { total, success, failed, cancelled }
})

// ==================== 方法 ====================

/**
 * 格式化时间
 * @param date - 日期对象
 */
const formatTime = (date: Date | string): string => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  // 1分钟内
  if (diff < 60 * 1000) {
    return '刚刚'
  }
  
  // 1小时内
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes}分钟前`
  }
  
  // 今天
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  if (d >= today) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours}小时前`
  }
  
  // 昨天
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  if (d >= yesterday) {
    return `昨天 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  
  // 其他
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

/**
 * 格式化持续时间
 * @param duration - 持续时间（毫秒）
 */
const formatDuration = (duration?: number): string => {
  if (!duration) return '-'
  if (duration < 1000) {
    return `${duration}ms`
  }
  return `${(duration / 1000).toFixed(2)}s`
}

/**
 * 获取状态样式类
 * @param status - 状态
 */
const getStatusClass = (status: ActionStatus): string => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    case 'failed':
      return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    case 'cancelled':
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    case 'running':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
    default:
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
  }
}

/**
 * 获取状态图标
 * @param status - 状态
 */
const getStatusIcon = (status: ActionStatus): string => {
  switch (status) {
    case 'success':
      return '✓'
    case 'failed':
      return '✗'
    case 'cancelled':
      return '○'
    case 'running':
      return '◐'
    default:
      return '◔'
  }
}

/**
 * 获取分类图标
 * @param category - 分类
 */
const getCategoryIcon = (category: ActionCategory): string => {
  switch (category) {
    case 'file':
      return '📁'
    case 'note':
      return '📝'
    case 'system':
      return '⚙️'
    case 'script':
      return '⚡'
    default:
      return '📋'
  }
}

/**
 * 查看详情
 * @param item - 历史记录项
 */
const viewDetail = (item: ActionHistoryItem): void => {
  selectedItem.value = item
  showDetailPanel.value = true
  emit('viewDetail', item)
}

/**
 * 关闭详情面板
 */
const closeDetail = (): void => {
  showDetailPanel.value = false
  selectedItem.value = null
}

/**
 * 重新执行
 * @param item - 历史记录项
 */
const reexecute = async (item: ActionHistoryItem): Promise<void> => {
  try {
    await actionsStore.reexecuteAction(item)
    emit('reexecute', item)
  } catch (error) {
    console.error('重新执行失败:', error)
  }
}

/**
 * 删除历史项
 * @param itemId - 历史记录ID
 */
const deleteItem = (itemId: string): void => {
  if (confirm('确定要删除这条历史记录吗？')) {
    actionsStore.deleteHistoryItem(itemId)
    if (selectedItem.value?.id === itemId) {
      closeDetail()
    }
  }
}

/**
 * 清空所有历史
 */
const clearAllHistory = (): void => {
  if (confirm('确定要清空所有历史记录吗？此操作不可恢复。')) {
    actionsStore.clearHistory()
    closeDetail()
  }
}

/**
 * 格式化JSON显示
 * @param obj - 对象
 */
const formatJson = (obj: unknown): string => {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow">
    <!-- 头部工具栏 -->
    <div class="p-4 border-b dark:border-gray-700 space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">执行历史</h3>
        <button
          v-if="actionsStore.history.length > 0"
          @click="clearAllHistory"
          class="text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
        >
          清空历史
        </button>
      </div>

      <!-- 统计信息 -->
      <div class="flex gap-4 text-sm">
        <span class="text-gray-600 dark:text-gray-400">
          总计: <span class="font-medium text-gray-900 dark:text-white">{{ statistics.total }}</span>
        </span>
        <span class="text-green-600 dark:text-green-400">
          成功: <span class="font-medium">{{ statistics.success }}</span>
        </span>
        <span class="text-red-600 dark:text-red-400">
          失败: <span class="font-medium">{{ statistics.failed }}</span>
        </span>
        <span class="text-gray-500 dark:text-gray-500">
          取消: <span class="font-medium">{{ statistics.cancelled }}</span>
        </span>
      </div>

      <!-- 过滤器 -->
      <div class="flex flex-wrap gap-2">
        <!-- 状态过滤 -->
        <select
          v-model="statusFilter"
          class="px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          <option value="all">全部状态</option>
          <option value="success">成功</option>
          <option value="failed">失败</option>
          <option value="cancelled">已取消</option>
          <option value="running">执行中</option>
        </select>

        <!-- 分类过滤 -->
        <select
          v-model="categoryFilter"
          class="px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          <option value="all">全部分类</option>
          <option value="file">文件操作</option>
          <option value="note">笔记管理</option>
          <option value="system">系统操作</option>
          <option value="script">脚本执行</option>
        </select>

        <!-- 时间范围过滤 -->
        <select
          v-model="timeRangeFilter"
          class="px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        >
          <option value="all">全部时间</option>
          <option value="today">今天</option>
          <option value="week">最近一周</option>
          <option value="month">最近一月</option>
        </select>
      </div>
    </div>

    <!-- 历史列表 -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="filteredHistory.length === 0" class="text-center py-12 text-gray-500 dark:text-gray-400">
        <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-lg">暂无历史记录</p>
        <p class="text-sm mt-1">执行动作后，历史记录将显示在这里</p>
      </div>

      <div v-else class="divide-y dark:divide-gray-700">
        <div
          v-for="item in filteredHistory"
          :key="item.id"
          class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
          :class="{ 'bg-blue-50 dark:bg-blue-900/20': selectedItem?.id === item.id }"
          @click="viewDetail(item)"
        >
          <div class="flex items-start gap-3">
            <!-- 分类图标 -->
            <span class="text-2xl flex-shrink-0">{{ getCategoryIcon(item.category) }}</span>
            
            <!-- 内容 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h4 class="font-medium text-gray-900 dark:text-white truncate">
                  {{ item.actionName }}
                </h4>
                <span
                  class="px-1.5 py-0.5 text-xs rounded flex items-center gap-1"
                  :class="getStatusClass(item.status)"
                >
                  <span>{{ getStatusIcon(item.status) }}</span>
                  <span>{{ actionsStore.statusNames[item.status] }}</span>
                </span>
              </div>
              
              <!-- 参数预览 -->
              <p class="text-sm text-gray-500 dark:text-gray-400 truncate mt-1">
                <span v-if="Object.keys(item.params).length > 0">
                  参数: {{ formatJson(item.params).slice(0, 50) }}...
                </span>
                <span v-else class="text-gray-400">无参数</span>
              </p>
              
              <!-- 时间和持续时间 -->
              <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                <span>{{ formatTime(item.executedAt) }}</span>
                <span v-if="item.duration">耗时: {{ formatDuration(item.duration) }}</span>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center gap-1">
              <button
                @click.stop="reexecute(item)"
                :disabled="item.status === 'running'"
                class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                title="重新执行"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              <button
                @click.stop="deleteItem(item.id)"
                class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                title="删除"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 错误信息 -->
          <div
            v-if="item.error"
            class="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded text-sm text-red-600 dark:text-red-400"
          >
            <span class="font-medium">错误:</span> {{ item.error }}
          </div>
        </div>
      </div>
    </div>

    <!-- 详情面板 -->
    <div
      v-if="showDetailPanel && selectedItem"
      class="border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50"
    >
      <div class="p-4">
        <div class="flex items-center justify-between mb-3">
          <h4 class="font-semibold text-gray-900 dark:text-white">执行详情</h4>
          <button
            @click="closeDetail"
            class="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="space-y-3 text-sm">
          <!-- 基本信息 -->
          <div class="grid grid-cols-2 gap-2">
            <div>
              <span class="text-gray-500 dark:text-gray-400">动作名称:</span>
              <span class="ml-1 text-gray-900 dark:text-white">{{ selectedItem.actionName }}</span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">分类:</span>
              <span class="ml-1 text-gray-900 dark:text-white">{{ actionsStore.categoryNames[selectedItem.category] }}</span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">状态:</span>
              <span
                class="ml-1 px-1.5 py-0.5 rounded text-xs"
                :class="getStatusClass(selectedItem.status)"
              >
                {{ actionsStore.statusNames[selectedItem.status] }}
              </span>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">耗时:</span>
              <span class="ml-1 text-gray-900 dark:text-white">{{ formatDuration(selectedItem.duration) }}</span>
            </div>
          </div>

          <!-- 执行时间 -->
          <div>
            <span class="text-gray-500 dark:text-gray-400">执行时间:</span>
            <span class="ml-1 text-gray-900 dark:text-white">
              {{ new Date(selectedItem.executedAt).toLocaleString('zh-CN') }}
            </span>
          </div>

          <!-- 参数 -->
          <div v-if="Object.keys(selectedItem.params).length > 0">
            <span class="text-gray-500 dark:text-gray-400 block mb-1">参数:</span>
            <pre class="p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">{{ formatJson(selectedItem.params) }}</pre>
          </div>

          <!-- 结果 -->
          <div v-if="selectedItem.result">
            <span class="text-gray-500 dark:text-gray-400 block mb-1">执行结果:</span>
            <pre class="p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs overflow-x-auto text-green-700 dark:text-green-400">{{ formatJson(selectedItem.result) }}</pre>
          </div>

          <!-- 错误 -->
          <div v-if="selectedItem.error">
            <span class="text-red-500 dark:text-red-400 block mb-1">错误信息:</span>
            <pre class="p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs overflow-x-auto text-red-700 dark:text-red-400">{{ selectedItem.error }}</pre>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex justify-end gap-2 mt-4">
          <button
            @click="reexecute(selectedItem)"
            class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            重新执行
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
