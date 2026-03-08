/**
 * 动作确认对话框组件
 * 用于高风险动作执行前的确认，显示命令预览和风险提示
 */
<script setup lang="ts">
import { computed, watch } from 'vue'
import { useActionsStore } from '@/stores/actions'
import type { PendingAction, PermissionLevel } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 是否显示对话框
   */
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: true
})

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'confirm', pendingId: string): void
  (e: 'cancel', pendingId: string): void
  (e: 'close'): void
}>()

// Store
const actionsStore = useActionsStore()

// ==================== 计算属性 ====================

/**
 * 当前待确认动作
 */
const currentPending = computed<PendingAction | null>(() => {
  return actionsStore.currentPendingAction
})

/**
 * 是否显示对话框
 */
const showDialog = computed(() => {
  return props.visible && actionsStore.hasPendingActions && currentPending.value
})

// ==================== 方法 ====================

/**
 * 获取权限级别样式类
 * @param level - 权限级别
 */
const getPermissionLevelClass = (level: PermissionLevel): string => {
  switch (level) {
    case 'low':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-500'
    case 'medium':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-500'
    case 'high':
      return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 border-orange-500'
    case 'critical':
      return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-red-500'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 border-gray-500'
  }
}

/**
 * 获取权限级别图标
 * @param level - 权限级别
 */
const getPermissionLevelIcon = (level: PermissionLevel): string => {
  switch (level) {
    case 'low':
      return '✓'
    case 'medium':
      return '!'
    case 'high':
      return '⚠'
    case 'critical':
      return '⚡'
    default:
      return '?'
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

/**
 * 确认执行
 */
const handleConfirm = (): void => {
  if (currentPending.value) {
    actionsStore.confirmPendingAction(currentPending.value.id, true)
    emit('confirm', currentPending.value.id)
  }
}

/**
 * 取消执行
 */
const handleCancel = (): void => {
  if (currentPending.value) {
    actionsStore.confirmPendingAction(currentPending.value.id, false)
    emit('cancel', currentPending.value.id)
  }
}

/**
 * 关闭对话框（等同于取消）
 */
const closeDialog = (): void => {
  handleCancel()
  emit('close')
}

/**
 * 阻止背景点击冒泡
 * @param event - 点击事件
 */
const preventBubble = (event: MouseEvent): void => {
  event.stopPropagation()
}
</script>

<template>
  <!-- 对话框遮罩 -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showDialog"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click="closeDialog"
      >
        <!-- 对话框内容 -->
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-150 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="showDialog && currentPending"
            class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden"
            @click="preventBubble"
          >
            <!-- 头部 -->
            <div
              class="px-6 py-4 border-b dark:border-gray-700"
              :class="getPermissionLevelClass(currentPending.action.permissionLevel).split(' ').slice(0, 2).join(' ')"
            >
              <div class="flex items-center gap-3">
                <span class="text-3xl">{{ currentPending.action.icon }}</span>
                <div class="flex-1">
                  <h3 class="text-lg font-semibold">
                    {{ currentPending.action.name }}
                  </h3>
                  <p class="text-sm opacity-80">
                    {{ currentPending.action.description }}
                  </p>
                </div>
                <div
                  class="px-3 py-1 rounded-full text-sm font-medium border-l-4"
                  :class="getPermissionLevelClass(currentPending.action.permissionLevel)"
                >
                  <span class="flex items-center gap-1">
                    <span>{{ getPermissionLevelIcon(currentPending.action.permissionLevel) }}</span>
                    <span>{{ actionsStore.permissionLevelNames[currentPending.action.permissionLevel] }}</span>
                  </span>
                </div>
              </div>
            </div>

            <!-- 内容区域 -->
            <div class="px-6 py-4 space-y-4 max-h-[50vh] overflow-y-auto">
              <!-- 安全警告 -->
              <div
                v-if="currentPending.action.permissionLevel === 'critical' || currentPending.action.permissionLevel === 'high'"
                class="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800"
              >
                <div class="flex items-start gap-2">
                  <svg class="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <div>
                    <p class="font-medium text-red-800 dark:text-red-300">
                      {{ currentPending.action.permissionLevel === 'critical' ? '极高风险操作' : '高风险操作' }}
                    </p>
                    <p class="text-sm text-red-700 dark:text-red-400 mt-1">
                      此操作可能对系统造成不可逆的影响，请谨慎确认
                    </p>
                  </div>
                </div>
              </div>

              <!-- 风险提示 -->
              <div
                v-if="currentPending.action.risks && currentPending.action.risks.length > 0"
                class="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
              >
                <p class="font-medium text-yellow-800 dark:text-yellow-300 flex items-center gap-2">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  风险提示
                </p>
                <ul class="mt-2 text-sm text-yellow-700 dark:text-yellow-400 list-disc list-inside space-y-1">
                  <li v-for="(risk, index) in currentPending.action.risks" :key="index">
                    {{ risk }}
                  </li>
                </ul>
              </div>

              <!-- 执行参数 -->
              <div>
                <h4 class="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  执行参数
                </h4>
                <div
                  v-if="Object.keys(currentPending.params).length > 0"
                  class="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3 font-mono text-sm overflow-x-auto"
                >
                  <pre class="text-gray-800 dark:text-gray-200">{{ formatJson(currentPending.params) }}</pre>
                </div>
                <p v-else class="text-gray-500 dark:text-gray-400 text-sm">无参数</p>
              </div>

              <!-- 示例（如果有） -->
              <div v-if="currentPending.action.examples && currentPending.action.examples.length > 0">
                <h4 class="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                  <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  使用示例
                </h4>
                <ul class="text-sm text-gray-600 dark:text-gray-400 list-disc list-inside space-y-1">
                  <li v-for="(example, index) in currentPending.action.examples" :key="index">
                    {{ example }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 底部操作按钮 -->
            <div class="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t dark:border-gray-700 flex items-center justify-between">
              <div class="text-sm text-gray-500 dark:text-gray-400">
                <span v-if="actionsStore.pendingActions.length > 1">
                  还有 {{ actionsStore.pendingActions.length - 1 }} 个待确认操作
                </span>
              </div>
              <div class="flex gap-3">
                <button
                  @click="handleCancel"
                  class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  取消
                </button>
                <button
                  @click="handleConfirm"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                  :class="{
                    'bg-orange-600 hover:bg-orange-700': currentPending.action.permissionLevel === 'high',
                    'bg-red-600 hover:bg-red-700': currentPending.action.permissionLevel === 'critical'
                  }"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  确认执行
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
