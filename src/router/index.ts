/**
 * Vue Router 配置文件
 * 定义应用的路由规则和导航守卫
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

/**
 * 路由配置列表
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: {
      title: '首页 - Nexus'
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: {
      title: '对话 - Nexus'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: {
      title: '设置 - Nexus'
    }
  },
  {
    path: '/models',
    name: 'Models',
    component: () => import('@/views/ModelsView.vue'),
    meta: {
      title: '模型管理 - Nexus'
    }
  },
  {
    // 404 页面
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: {
      title: '页面未找到 - Nexus'
    }
  }
]

/**
 * 创建路由实例
 */
const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 全局前置守卫
 * 设置页面标题
 */
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = (to.meta.title as string) || 'Nexus - 本地AI智能中枢'
  next()
})

export default router
