<script setup lang="ts">
/**
 * 404 页面组件
 * 处理未找到路由的情况
 */
import { useRouter } from 'vue-router'

const router = useRouter()

/**
 * 返回首页
 */
const goHome = () => {
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-8">
    <div class="text-center">
      <h1 class="text-6xl font-bold text-gradient mb-4">404</h1>
      <p class="text-xl text-secondary-400 mb-8">页面未找到</p>
      <button
        class="btn-primary"
        @click="goHome"
      >
        返回首页
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 组件特定样式 */
</style>
