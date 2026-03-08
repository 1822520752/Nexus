/**
 * 文档操作组件
 * 提供删除、重命名等文档操作功能
 */
<script setup lang="ts">
import { ref } from 'vue'
import type { Document } from '@/types'

/**
 * 组件属性
 */
interface Props {
  /**
   * 文档对象
   */
  document: Document
}

const props = defineProps<Props>()

/**
 * 组件事件
 */
const emit = defineEmits<{
  (e: 'rename', document: Document): void
  (e: 'delete', documentId: number): void
}>()

// ==================== 响应式状态 ====================

/**
 * 是否显示操作菜单
 */
const showMenu = ref(false)

// ==================== 方法 ====================

/**
 * 处理重命名
 */
const handleRename = () => {
  emit('rename', props.document)
  showMenu.value = false
}

/**
 * 处理删除
 */
const handleDelete = () => {
  emit('delete', props.document.id)
  showMenu.value = false
}

/**
 * 切换菜单显示
 */
const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

/**
 * 关闭菜单
 */
const closeMenu = () => {
  showMenu.value = false
}
</script>

<template>
  <div class="document-actions relative" @click.stop>
    <!-- 操作按钮组 -->
    <div class="flex items-center gap-1">
      <!-- 重命名按钮 -->
      <button
        @click="handleRename"
        class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
        title="重命名"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      </button>

      <!-- 删除按钮 -->
      <button
        @click="handleDelete"
        class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
        title="删除"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>
