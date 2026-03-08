/**
 * Vue 应用入口文件
 * 初始化 Vue 应用、路由、状态管理和样式
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 导入全局样式
import './assets/styles/main.css'

// 创建 Vue 应用实例
const app = createApp(App)

// 使用 Pinia 状态管理
app.use(createPinia())

// 使用 Vue Router
app.use(router)

// 挂载应用
app.mount('#app')
