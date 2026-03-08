/**
 * 权限管理设置组件
 * 配置动作执行的安全策略和权限级别
 */
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useActionsStore } from '@/stores/actions'
import type { PermissionLevel } from '@/types'

// Store
const actionsStore = useActionsStore()

// ==================== 响应式状态 ====================

/**
 * 新敏感目录输入
 */
const newSensitiveDir = ref('')

/**
 * 新脚本路径输入
 */
const newScriptPath = ref('')

/**
 * 是否显示重置确认
 */
const showResetConfirm = ref(false)

// ==================== 计算属性 ====================

/**
 * 当前权限设置
 */
const settings = computed(() => actionsStore.permissionSettings)

/**
 * 权限级别配置
 */
const permissionLevels: { key: PermissionLevel; label: string; description: string; color: string }[] = [
  {
    key: 'low',
    label: '低风险',
    description: '读取文件、查看信息等安全操作',
    color: 'green'
  },
  {
    key: 'medium',
    label: '中等风险',
    description: '写入文件、修改配置等操作',
    color: 'yellow'
  },
  {
    key: 'high',
    label: '高风险',
    description: '删除文件、结束进程等危险操作',
    color: 'orange'
  },
  {
    key: 'critical',
    label: '极高风险',
    description: '执行脚本、运行命令等敏感操作',
    color: 'red'
  }
]

// ==================== 方法 ====================

/**
 * 切换安全模式
 */
const toggleSafeMode = (): void => {
  actionsStore.updatePermissionSettings({
    safeMode: !settings.value.safeMode
  })
}

/**
 * 切换权限级别确认设置
 * @param level - 权限级别
 */
const toggleConfirmLevel = (level: PermissionLevel): void => {
  actionsStore.updatePermissionSettings({
    confirmLevels: {
      ...settings.value.confirmLevels,
      [level]: !settings.value.confirmLevels[level]
    }
  })
}

/**
 * 切换记录所有操作
 */
const toggleLogAllActions = (): void => {
  actionsStore.updatePermissionSettings({
    logAllActions: !settings.value.logAllActions
  })
}

/**
 * 切换自动拒绝高风险
 */
const toggleAutoRejectHighRisk = (): void => {
  actionsStore.updatePermissionSettings({
    autoRejectHighRisk: !settings.value.autoRejectHighRisk
  })
}

/**
 * 添加敏感目录
 */
const addSensitiveDirectory = (): void => {
  const path = newSensitiveDir.value.trim()
  if (path) {
    actionsStore.addSensitiveDirectory(path)
    newSensitiveDir.value = ''
  }
}

/**
 * 移除敏感目录
 * @param path - 目录路径
 */
const removeSensitiveDirectory = (path: string): void => {
  actionsStore.removeSensitiveDirectory(path)
}

/**
 * 添加脚本路径
 */
const addAllowedScriptPath = (): void => {
  const path = newScriptPath.value.trim()
  if (path && !settings.value.allowedScriptPaths.includes(path)) {
    actionsStore.updatePermissionSettings({
      allowedScriptPaths: [...settings.value.allowedScriptPaths, path]
    })
    newScriptPath.value = ''
  }
}

/**
 * 移除脚本路径
 * @param path - 脚本路径
 */
const removeAllowedScriptPath = (path: string): void => {
  actionsStore.updatePermissionSettings({
    allowedScriptPaths: settings.value.allowedScriptPaths.filter(p => p !== path)
  })
}

/**
 * 重置设置
 */
const resetSettings = (): void => {
  actionsStore.resetPermissionSettings()
  showResetConfirm.value = false
}

/**
 * 获取权限级别颜色类
 * @param level - 权限级别
 * @param type - 类型（bg/text）
 */
const getLevelColorClass = (level: PermissionLevel, type: 'bg' | 'text' | 'border'): string => {
  const colors: Record<PermissionLevel, Record<string, string>> = {
    low: {
      bg: 'bg-green-100 dark:bg-green-900/30',
      text: 'text-green-700 dark:text-green-400',
      border: 'border-green-500'
    },
    medium: {
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      text: 'text-yellow-700 dark:text-yellow-400',
      border: 'border-yellow-500'
    },
    high: {
      bg: 'bg-orange-100 dark:bg-orange-900/30',
      text: 'text-orange-700 dark:text-orange-400',
      border: 'border-orange-500'
    },
    critical: {
      bg: 'bg-red-100 dark:bg-red-900/30',
      text: 'text-red-700 dark:text-red-400',
      border: 'border-red-500'
    }
  }
  return colors[level][type]
}
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
    <!-- 头部 -->
    <div class="p-4 border-b dark:border-gray-700">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">权限管理设置</h3>
        <button
          @click="showResetConfirm = true"
          class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          重置为默认
        </button>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        配置动作执行的安全策略，保护系统安全
      </p>
    </div>

    <!-- 设置内容 -->
    <div class="flex-1 overflow-y-auto p-4 space-y-6">
      <!-- 安全模式 -->
      <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
              <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white">安全模式</h4>
              <p class="text-sm text-gray-600 dark:text-gray-400">启用后将强制确认所有需要确认的动作</p>
            </div>
          </div>
          <button
            @click="toggleSafeMode"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
            :class="settings.safeMode ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
              :class="settings.safeMode ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>
      </div>

      <!-- 权限级别确认设置 -->
      <div>
        <h4 class="font-medium text-gray-900 dark:text-white mb-3">权限级别确认设置</h4>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          配置各权限级别的动作是否需要用户确认后才能执行
        </p>
        
        <div class="space-y-3">
          <div
            v-for="level in permissionLevels"
            :key="level.key"
            class="flex items-center justify-between p-3 rounded-lg border"
            :class="[
              getLevelColorClass(level.key, 'bg'),
              'border-l-4',
              getLevelColorClass(level.key, 'border')
            ]"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span
                  class="font-medium"
                  :class="getLevelColorClass(level.key, 'text')"
                >
                  {{ level.label }}
                </span>
                <span
                  v-if="settings.confirmLevels[level.key]"
                  class="px-1.5 py-0.5 text-xs rounded bg-white dark:bg-gray-800"
                  :class="getLevelColorClass(level.key, 'text')"
                >
                  需确认
                </span>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">{{ level.description }}</p>
            </div>
            <button
              @click="toggleConfirmLevel(level.key)"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="settings.confirmLevels[level.key] ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="settings.confirmLevels[level.key] ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- 敏感目录管理 -->
      <div>
        <h4 class="font-medium text-gray-900 dark:text-white mb-3">敏感目录管理</h4>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          在这些目录下的文件操作将触发额外的安全确认
        </p>
        
        <!-- 添加新目录 -->
        <div class="flex gap-2 mb-3">
          <input
            v-model="newSensitiveDir"
            type="text"
            placeholder="输入目录路径，如 C:\Windows"
            class="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            @keyup.enter="addSensitiveDirectory"
          />
          <button
            @click="addSensitiveDirectory"
            :disabled="!newSensitiveDir.trim()"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            添加
          </button>
        </div>

        <!-- 目录列表 -->
        <div class="space-y-2">
          <div
            v-for="dir in settings.sensitiveDirectories"
            :key="dir"
            class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ dir }}</span>
            </div>
            <button
              @click="removeSensitiveDirectory(dir)"
              class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div
            v-if="settings.sensitiveDirectories.length === 0"
            class="text-center py-4 text-gray-400 dark:text-gray-500 text-sm"
          >
            暂无敏感目录
          </div>
        </div>
      </div>

      <!-- 允许的脚本路径 -->
      <div>
        <h4 class="font-medium text-gray-900 dark:text-white mb-3">允许的脚本路径</h4>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          只有在这些目录下的脚本才能被执行（留空表示不允许任何脚本）
        </p>
        
        <!-- 添加新路径 -->
        <div class="flex gap-2 mb-3">
          <input
            v-model="newScriptPath"
            type="text"
            placeholder="输入脚本目录路径"
            class="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            @keyup.enter="addAllowedScriptPath"
          />
          <button
            @click="addAllowedScriptPath"
            :disabled="!newScriptPath.trim()"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            添加
          </button>
        </div>

        <!-- 路径列表 -->
        <div class="space-y-2">
          <div
            v-for="path in settings.allowedScriptPaths"
            :key="path"
            class="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ path }}</span>
            </div>
            <button
              @click="removeAllowedScriptPath(path)"
              class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div
            v-if="settings.allowedScriptPaths.length === 0"
            class="text-center py-4 text-gray-400 dark:text-gray-500 text-sm"
          >
            暂无允许的脚本路径（将禁止执行所有脚本）
          </div>
        </div>
      </div>

      <!-- 其他设置 -->
      <div>
        <h4 class="font-medium text-gray-900 dark:text-white mb-3">其他设置</h4>
        
        <div class="space-y-3">
          <!-- 记录所有操作 -->
          <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <h5 class="font-medium text-gray-900 dark:text-white">记录所有操作</h5>
              <p class="text-sm text-gray-500 dark:text-gray-400">将所有动作执行记录保存到历史</p>
            </div>
            <button
              @click="toggleLogAllActions"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="settings.logAllActions ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="settings.logAllActions ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>

          <!-- 自动拒绝高风险 -->
          <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <h5 class="font-medium text-gray-900 dark:text-white">自动拒绝高风险操作</h5>
              <p class="text-sm text-gray-500 dark:text-gray-400">自动拒绝极高风险级别的动作，无需确认</p>
            </div>
            <button
              @click="toggleAutoRejectHighRisk"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              :class="settings.autoRejectHighRisk ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                :class="settings.autoRejectHighRisk ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- 安全提示 -->
      <div class="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
        <div class="flex gap-3">
          <svg class="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <h5 class="font-medium text-yellow-800 dark:text-yellow-300">安全提示</h5>
            <ul class="text-sm text-yellow-700 dark:text-yellow-400 mt-1 list-disc list-inside space-y-1">
              <li>建议始终开启安全模式以保护系统安全</li>
              <li>高风险和极高风险操作应始终需要确认</li>
              <li>谨慎添加允许的脚本路径，避免执行恶意脚本</li>
              <li>定期检查敏感目录配置是否合理</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 重置确认对话框 -->
    <div
      v-if="showResetConfirm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showResetConfirm = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-sm mx-4">
        <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">确认重置</h4>
        <p class="text-gray-600 dark:text-gray-400 mb-4">
          确定要将所有权限设置重置为默认值吗？此操作不可撤销。
        </p>
        <div class="flex justify-end gap-2">
          <button
            @click="showResetConfirm = false"
            class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            @click="resetSettings"
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            确认重置
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
