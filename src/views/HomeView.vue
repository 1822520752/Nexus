<script setup lang="ts">
/**
 * 首页视图组件
 * 展示应用概览和快捷入口
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/**
 * 快捷功能列表
 */
const features = ref([
  {
    title: 'AI 对话',
    description: '与本地 AI 模型进行智能对话',
    icon: 'chat',
    path: '/chat'
  },
  {
    title: '模型管理',
    description: '管理和配置本地 AI 模型',
    icon: 'model',
    path: '/models'
  },
  {
    title: '系统设置',
    description: '自定义应用偏好设置',
    icon: 'settings',
    path: '/settings'
  }
])

/**
 * 导航到指定路径
 * @param path - 目标路径
 */
const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<template>
  <div class="min-h-screen p-8">
    <!-- 头部区域 -->
    <header class="mb-12 text-center">
      <h1 class="text-4xl font-bold text-gradient mb-4">
        Nexus
      </h1>
      <p class="text-secondary-400 text-lg">
        本地 AI 智能中枢 - 您的私人 AI 助手
      </p>
    </header>

    <!-- 功能入口 -->
    <div class="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="card-hover"
        @click="navigateTo(feature.path)"
      >
        <div class="text-primary-400 mb-4">
          <!-- 图标占位 -->
          <div class="w-12 h-12 rounded-lg bg-primary-500/20 flex items-center justify-center">
            <span class="text-2xl">
              {{ feature.icon === 'chat' ? '💬' : feature.icon === 'model' ? '🤖' : '⚙️' }}
            </span>
          </div>
        </div>
        <h3 class="text-xl font-semibold text-white mb-2">
          {{ feature.title }}
        </h3>
        <p class="text-secondary-400">
          {{ feature.description }}
        </p>
      </div>
    </div>

    <!-- 状态指示 -->
    <div class="mt-12 text-center">
      <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary-800 border border-secondary-700">
        <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
        <span class="text-secondary-300 text-sm">后端服务运行中</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>
