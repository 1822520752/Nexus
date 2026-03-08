<script setup lang="ts">
/**
 * 根组件
 * 提供应用的整体布局和路由视图
 */
import { onMounted } from 'vue'
import MainLayout from '@/layouts/MainLayout.vue'
import { useTheme, useI18n } from '@/composables'

// ==================== 组合式函数 ====================

const { applyTheme } = useTheme()
const { t } = useI18n()

// ==================== 生命周期 ====================

onMounted(() => {
  // 应用初始主题
  applyTheme()
  
  // 设置页面标题
  document.title = `${t('app.name')} - ${t('app.title')}`
})
</script>

<template>
  <MainLayout />
</template>

<style>
/* 全局样式已移至 main.css */
</style>
