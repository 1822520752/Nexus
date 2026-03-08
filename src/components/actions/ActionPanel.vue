/**
 * 动作选择面板组件
 * 展示可用动作列表，支持分类浏览和搜索过滤
 */
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useActionsStore } from '@/stores/actions'
import type { ActionDefinition, ActionCategory } from '@/types'

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'select', action: ActionDefinition): void
  (e: 'execute', action: ActionDefinition, params: Record<string, unknown>): void
}>()

// Store
const actionsStore = useActionsStore()

// ==================== 响应式状态 ====================

/**
 * 搜索关键词
 */
const searchKeyword = ref('')

/**
 * 当前选中的分类
 */
const selectedCategory = ref<ActionCategory | 'all'>('all')

/**
 * 当前选中的动作
 */
const localSelectedAction = ref<ActionDefinition | null>(null)

/**
 * 展开的分类
 */
const expandedCategories = ref<Set<ActionCategory>>(new Set(['file', 'note', 'system', 'script']))

/**
 * 参数表单数据
 */
const paramValues = ref<Record<string, unknown>>({})

// ==================== 计算属性 ====================

/**
 * 过滤后的动作列表
 */
const filteredActions = computed(() => {
  return actionsStore.searchActions(searchKeyword.value, 
    selectedCategory.value === 'all' ? undefined : selectedCategory.value
  )
})

/**
 * 分类统计
 */
const categoryStats = computed(() => {
  const stats: Record<string, number> = {
    all: actionsStore.actions.length
  }
  Object.entries(actionsStore.actionsByCategory).forEach(([category, actions]) => {
    stats[category] = actions.length
  })
  return stats
})

/**
 * 分类标签配置
 */
const categoryTabs = computed(() => {
  const tabs: { key: ActionCategory | 'all'; label: string; icon: string }[] = [
    { key: 'all', label: '全部', icon: '📋' }
  ]
  const categoryIcons: Record<ActionCategory, string> = {
    file: '📁',
    note: '📝',
    system: '⚙️',
    script: '⚡'
  }
  Object.entries(actionsStore.categoryNames).forEach(([key, name]) => {
    tabs.push({
      key: key as ActionCategory,
      label: name,
      icon: categoryIcons[key as ActionCategory]
    })
  })
  return tabs
})

/**
 * 当前选中动作的参数是否有效
 */
const isParamsValid = computed(() => {
  if (!localSelectedAction.value) return false
  
  for (const param of localSelectedAction.value.params) {
    if (param.required) {
      const value = paramValues.value[param.name]
      if (value === undefined || value === null || value === '') {
        return false
      }
    }
  }
  return true
})

// ==================== 监听器 ====================

/**
 * 监听选中动作变化，重置参数表单
 */
watch(localSelectedAction, (action) => {
  if (action) {
    // 初始化参数默认值
    const defaults: Record<string, unknown> = {}
    action.params.forEach(param => {
      if (param.default !== undefined) {
        defaults[param.name] = param.default
      } else if (param.type === 'boolean') {
        defaults[param.name] = false
      } else {
        defaults[param.name] = ''
      }
    })
    paramValues.value = defaults
  }
})

// ==================== 方法 ====================

/**
 * 切换分类展开状态
 * @param category - 分类名称
 */
const toggleCategory = (category: ActionCategory): void => {
  if (expandedCategories.value.has(category)) {
    expandedCategories.value.delete(category)
  } else {
    expandedCategories.value.add(category)
  }
}

/**
 * 选择动作
 * @param action - 动作定义
 */
const selectAction = (action: ActionDefinition): void => {
  localSelectedAction.value = action
  actionsStore.setSelectedAction(action)
  emit('select', action)
}

/**
 * 执行动作
 */
const executeAction = (): void => {
  if (!localSelectedAction.value || !isParamsValid.value) return
  
  emit('execute', localSelectedAction.value, { ...paramValues.value })
  
  // 清空选择
  localSelectedAction.value = null
  paramValues.value = {}
}

/**
 * 取消选择
 */
const cancelSelection = (): void => {
  localSelectedAction.value = null
  paramValues.value = {}
}

/**
 * 获取权限级别样式类
 * @param level - 权限级别
 */
const getPermissionLevelClass = (level: string): string => {
  switch (level) {
    case 'low':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    case 'medium':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    case 'high':
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
    case 'critical':
      return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }
}

/**
 * 获取权限级别边框样式类
 * @param level - 权限级别
 */
const getPermissionBorderClass = (level: string): string => {
  switch (level) {
    case 'low':
      return 'border-l-green-500'
    case 'medium':
      return 'border-l-yellow-500'
    case 'high':
      return 'border-l-orange-500'
    case 'critical':
      return 'border-l-red-500'
    default:
      return 'border-l-gray-500'
  }
}
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow">
    <!-- 搜索栏 -->
    <div class="p-4 border-b dark:border-gray-700">
      <div class="relative">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索动作..."
          class="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        />
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="flex gap-1 p-2 border-b dark:border-gray-700 overflow-x-auto">
      <button
        v-for="tab in categoryTabs"
        :key="tab.key"
        @click="selectedCategory = tab.key"
        class="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors"
        :class="selectedCategory === tab.key 
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' 
          : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'"
      >
        <span>{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
        <span class="text-xs opacity-60">({{ categoryStats[tab.key] || 0 }})</span>
      </button>
    </div>

    <!-- 动作列表 -->
    <div class="flex-1 overflow-y-auto p-2">
      <div v-if="filteredActions.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p>未找到匹配的动作</p>
      </div>

      <!-- 按分类分组显示 -->
      <template v-else-if="selectedCategory === 'all'">
        <div
          v-for="(actions, category) in actionsStore.actionsByCategory"
          :key="category"
          class="mb-2"
        >
          <button
            v-if="actions.length > 0"
            @click="toggleCategory(category as ActionCategory)"
            class="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <span class="flex items-center gap-2">
              <span>{{ category === 'file' ? '📁' : category === 'note' ? '📝' : category === 'system' ? '⚙️' : '⚡' }}</span>
              <span>{{ actionsStore.categoryNames[category as ActionCategory] }}</span>
              <span class="text-xs text-gray-400">({{ actions.length }})</span>
            </span>
            <svg
              class="w-4 h-4 transition-transform"
              :class="{ 'rotate-180': expandedCategories.has(category as ActionCategory) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          <div v-show="expandedCategories.has(category as ActionCategory)" class="mt-1 space-y-1">
            <button
              v-for="action in actions"
              :key="action.id"
              @click="selectAction(action)"
              class="w-full flex items-start gap-3 p-3 rounded-lg border-l-4 text-left transition-all hover:shadow-md"
              :class="[
                getPermissionBorderClass(action.permissionLevel),
                localSelectedAction?.id === action.id
                  ? 'bg-blue-50 dark:bg-blue-900/20 shadow-md'
                  : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
            >
              <span class="text-2xl flex-shrink-0">{{ action.icon }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <h4 class="font-medium text-gray-900 dark:text-white">{{ action.name }}</h4>
                  <span
                    class="px-1.5 py-0.5 text-xs rounded"
                    :class="getPermissionLevelClass(action.permissionLevel)"
                  >
                    {{ actionsStore.permissionLevelNames[action.permissionLevel] }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{{ action.description }}</p>
              </div>
            </button>
          </div>
        </div>
      </template>

      <!-- 单分类显示 -->
      <div v-else class="space-y-1">
        <button
          v-for="action in filteredActions"
          :key="action.id"
          @click="selectAction(action)"
          class="w-full flex items-start gap-3 p-3 rounded-lg border-l-4 text-left transition-all hover:shadow-md"
          :class="[
            getPermissionBorderClass(action.permissionLevel),
            localSelectedAction?.id === action.id
              ? 'bg-blue-50 dark:bg-blue-900/20 shadow-md'
              : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
          ]"
        >
          <span class="text-2xl flex-shrink-0">{{ action.icon }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h4 class="font-medium text-gray-900 dark:text-white">{{ action.name }}</h4>
              <span
                class="px-1.5 py-0.5 text-xs rounded"
                :class="getPermissionLevelClass(action.permissionLevel)"
              >
                {{ actionsStore.permissionLevelNames[action.permissionLevel] }}
              </span>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{{ action.description }}</p>
          </div>
        </button>
      </div>
    </div>

    <!-- 动作详情和参数面板 -->
    <div
      v-if="localSelectedAction"
      class="border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50"
    >
      <!-- 动作详情 -->
      <div class="p-4 border-b dark:border-gray-700">
        <div class="flex items-start gap-3">
          <span class="text-3xl">{{ localSelectedAction.icon }}</span>
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ localSelectedAction.name }}
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {{ localSelectedAction.description }}
            </p>
            
            <!-- 风险提示 -->
            <div
              v-if="localSelectedAction.risks && localSelectedAction.risks.length > 0"
              class="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg"
            >
              <p class="text-xs font-medium text-red-700 dark:text-red-400 flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                风险提示
              </p>
              <ul class="mt-1 text-xs text-red-600 dark:text-red-400 list-disc list-inside">
                <li v-for="(risk, index) in localSelectedAction.risks" :key="index">{{ risk }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 参数表单 -->
      <div v-if="localSelectedAction.params.length > 0" class="p-4 space-y-3">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">参数配置</h4>
        
        <div
          v-for="param in localSelectedAction.params"
          :key="param.name"
          class="space-y-1"
        >
          <label class="flex items-center gap-1 text-sm text-gray-700 dark:text-gray-300">
            {{ param.description || param.name }}
            <span v-if="param.required" class="text-red-500">*</span>
          </label>
          
          <!-- 文本输入 -->
          <input
            v-if="param.type === 'string'"
            v-model="paramValues[param.name]"
            type="text"
            :placeholder="param.description"
            class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
          
          <!-- 数字输入 -->
          <input
            v-else-if="param.type === 'number'"
            v-model.number="paramValues[param.name]"
            type="number"
            :min="param.validation?.min"
            :max="param.validation?.max"
            :placeholder="param.description"
            class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
          
          <!-- 路径输入 -->
          <div
            v-else-if="param.type === 'path'"
            class="flex gap-2"
          >
            <input
              v-model="paramValues[param.name]"
              type="text"
              :placeholder="param.description || '输入文件路径'"
              class="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <button
              class="px-3 py-2 bg-gray-100 dark:bg-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-500 transition-colors"
              title="浏览"
            >
              <svg class="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </button>
          </div>
          
          <!-- 布尔开关 -->
          <label
            v-else-if="param.type === 'boolean'"
            class="flex items-center gap-2 cursor-pointer"
          >
            <input
              v-model="paramValues[param.name]"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm text-gray-600 dark:text-gray-400">启用</span>
          </label>
          
          <!-- 下拉选择 -->
          <select
            v-else-if="param.type === 'select'"
            v-model="paramValues[param.name]"
            class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          >
            <option value="" disabled>请选择</option>
            <option
              v-for="option in param.options"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-2 p-4 border-t dark:border-gray-700">
        <button
          @click="cancelSelection"
          class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          取消
        </button>
        <button
          @click="executeAction"
          :disabled="!isParamsValid"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          执行动作
        </button>
      </div>
    </div>
  </div>
</template>
