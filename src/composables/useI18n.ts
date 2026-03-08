/**
 * 国际化管理 Composable
 * 提供多语言支持和翻译功能
 */
import { ref, computed, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'

/**
 * 语言代码类型
 */
export type LanguageCode = 'zh-CN' | 'en-US'

/**
 * 语言配置接口
 */
export interface LanguageConfig {
  code: LanguageCode
  name: string
  nativeName: string
}

/**
 * 支持的语言列表
 */
export const supportedLanguages: LanguageConfig[] = [
  { code: 'zh-CN', name: 'Chinese Simplified', nativeName: '简体中文' },
  { code: 'en-US', name: 'English (US)', nativeName: 'English' }
]

/**
 * 中文翻译
 */
const zhCN: Record<string, string> = {
  // 通用
  'app.name': 'Nexus',
  'app.title': '本地 AI 智能中枢',
  'common.save': '保存',
  'common.cancel': '取消',
  'common.confirm': '确认',
  'common.delete': '删除',
  'common.edit': '编辑',
  'common.copy': '复制',
  'common.copied': '已复制',
  'common.loading': '加载中...',
  'common.error': '错误',
  'common.success': '成功',
  'common.search': '搜索',
  'common.close': '关闭',
  'common.retry': '重试',
  'common.clear': '清空',
  'common.new': '新建',

  // 导航
  'nav.home': '首页',
  'nav.chat': '对话',
  'nav.models': '模型',
  'nav.settings': '设置',

  // 对话
  'chat.title': 'AI 对话',
  'chat.new': '新对话',
  'chat.placeholder': '输入消息...',
  'chat.send': '发送',
  'chat.sending': '发送中...',
  'chat.clear': '清空对话',
  'chat.noMessages': '开始与 AI 对话吧',
  'chat.selectModel': '选择模型',
  'chat.noModel': '未选择模型',
  'chat.conversation': '对话',
  'chat.conversations': '对话列表',
  'chat.deleteConfirm': '确定要删除这个对话吗？',

  // 消息
  'message.user': '我',
  'message.assistant': 'AI',
  'message.system': '系统',
  'message.copyCode': '复制代码',
  'message.copiedCode': '已复制代码',

  // 模型
  'model.title': '模型管理',
  'model.add': '添加模型',
  'model.edit': '编辑模型',
  'model.delete': '删除模型',
  'model.name': '模型名称',
  'model.provider': '提供商',
  'model.status': '状态',
  'model.active': '已启用',
  'model.inactive': '已禁用',
  'model.default': '默认',
  'model.test': '测试连接',
  'model.testing': '测试中...',
  'model.available': '可用',
  'model.unavailable': '不可用',
  'model.noModels': '暂无模型配置',

  // 设置
  'settings.title': '设置',
  'settings.theme': '主题',
  'settings.theme.light': '浅色',
  'settings.theme.dark': '深色',
  'settings.theme.system': '跟随系统',
  'settings.language': '语言',
  'settings.color': '颜色主题',
  'settings.general': '常规',
  'settings.appearance': '外观',
  'settings.about': '关于',
  'settings.reset': '重置设置',
  'settings.resetConfirm': '确定要重置所有设置吗？',
  'settings.autoSave': '自动保存',
  'settings.sendOnEnter': '回车发送',
  'settings.showTokenCount': '显示 Token 数量',
  'settings.backendUrl': '后端地址',

  // 快捷键
  'shortcut.sendMessage': '发送消息',
  'shortcut.clearChat': '清空对话',
  'shortcut.newConversation': '新建对话',
  'shortcut.saveSettings': '保存设置',
  'shortcut.openSettings': '打开设置',

  // 错误
  'error.network': '网络错误',
  'error.server': '服务器错误',
  'error.unknown': '未知错误',
  'error.notFound': '未找到',
  'error.unauthorized': '未授权',

  // 提示
  'tip.welcome': '欢迎使用 Nexus AI 智能中枢',
  'tip.selectModel': '请先选择一个 AI 模型'
}

/**
 * 英文翻译
 */
const enUS: Record<string, string> = {
  // Common
  'app.name': 'Nexus',
  'app.title': 'Local AI Intelligence Hub',
  'common.save': 'Save',
  'common.cancel': 'Cancel',
  'common.confirm': 'Confirm',
  'common.delete': 'Delete',
  'common.edit': 'Edit',
  'common.copy': 'Copy',
  'common.copied': 'Copied',
  'common.loading': 'Loading...',
  'common.error': 'Error',
  'common.success': 'Success',
  'common.search': 'Search',
  'common.close': 'Close',
  'common.retry': 'Retry',
  'common.clear': 'Clear',
  'common.new': 'New',

  // Navigation
  'nav.home': 'Home',
  'nav.chat': 'Chat',
  'nav.models': 'Models',
  'nav.settings': 'Settings',

  // Chat
  'chat.title': 'AI Chat',
  'chat.new': 'New Chat',
  'chat.placeholder': 'Type a message...',
  'chat.send': 'Send',
  'chat.sending': 'Sending...',
  'chat.clear': 'Clear Chat',
  'chat.noMessages': 'Start a conversation with AI',
  'chat.selectModel': 'Select Model',
  'chat.noModel': 'No model selected',
  'chat.conversation': 'Conversation',
  'chat.conversations': 'Conversations',
  'chat.deleteConfirm': 'Are you sure you want to delete this conversation?',

  // Message
  'message.user': 'Me',
  'message.assistant': 'AI',
  'message.system': 'System',
  'message.copyCode': 'Copy Code',
  'message.copiedCode': 'Code Copied',

  // Model
  'model.title': 'Model Management',
  'model.add': 'Add Model',
  'model.edit': 'Edit Model',
  'model.delete': 'Delete Model',
  'model.name': 'Model Name',
  'model.provider': 'Provider',
  'model.status': 'Status',
  'model.active': 'Active',
  'model.inactive': 'Inactive',
  'model.default': 'Default',
  'model.test': 'Test Connection',
  'model.testing': 'Testing...',
  'model.available': 'Available',
  'model.unavailable': 'Unavailable',
  'model.noModels': 'No models configured',

  // Settings
  'settings.title': 'Settings',
  'settings.theme': 'Theme',
  'settings.theme.light': 'Light',
  'settings.theme.dark': 'Dark',
  'settings.theme.system': 'System',
  'settings.language': 'Language',
  'settings.color': 'Color Theme',
  'settings.general': 'General',
  'settings.appearance': 'Appearance',
  'settings.about': 'About',
  'settings.reset': 'Reset Settings',
  'settings.resetConfirm': 'Are you sure you want to reset all settings?',
  'settings.autoSave': 'Auto Save',
  'settings.sendOnEnter': 'Send on Enter',
  'settings.showTokenCount': 'Show Token Count',
  'settings.backendUrl': 'Backend URL',

  // Shortcuts
  'shortcut.sendMessage': 'Send Message',
  'shortcut.clearChat': 'Clear Chat',
  'shortcut.newConversation': 'New Conversation',
  'shortcut.saveSettings': 'Save Settings',
  'shortcut.openSettings': 'Open Settings',

  // Errors
  'error.network': 'Network Error',
  'error.server': 'Server Error',
  'error.unknown': 'Unknown Error',
  'error.notFound': 'Not Found',
  'error.unauthorized': 'Unauthorized',

  // Tips
  'tip.welcome': 'Welcome to Nexus AI Intelligence Hub',
  'tip.selectModel': 'Please select an AI model first'
}

/**
 * 翻译映射
 */
const translations: Record<LanguageCode, Record<string, string>> = {
  'zh-CN': zhCN,
  'en-US': enUS
}

/**
 * 国际化管理 Hook
 */
export function useI18n() {
  const settingsStore = useSettingsStore()

  /**
   * 当前语言
   */
  const currentLanguage = computed<LanguageCode>({
    get: () => settingsStore.settings.language,
    set: (value) => settingsStore.updateSetting('language', value)
  })

  /**
   * 当前翻译映射
   */
  const t = computed(() => translations[currentLanguage.value])

  /**
   * 翻译函数
   * @param key - 翻译键
   * @param params - 插值参数（可选）
   * @returns 翻译后的文本
   */
  const translate = (key: string, params?: Record<string, string | number>): string => {
    let text = t.value[key] || key

    // 处理插值
    if (params) {
      Object.entries(params).forEach(([paramKey, value]) => {
        text = text.replace(`{${paramKey}}`, String(value))
      })
    }

    return text
  }

  /**
   * 设置语言
   * @param code - 语言代码
   */
  const setLanguage = (code: LanguageCode): void => {
    currentLanguage.value = code
  }

  /**
   * 获取当前语言配置
   */
  const currentLanguageConfig = computed<LanguageConfig | undefined>(() => {
    return supportedLanguages.find(lang => lang.code === currentLanguage.value)
  })

  /**
   * 判断是否为中文
   */
  const isChinese = computed(() => currentLanguage.value === 'zh-CN')

  /**
   * 判断是否为英文
   */
  const isEnglish = computed(() => currentLanguage.value === 'en-US')

  // 监听语言变化，更新 HTML lang 属性
  watch(currentLanguage, (lang) => {
    document.documentElement.lang = lang
  }, { immediate: true })

  return {
    // 状态
    currentLanguage,
    currentLanguageConfig,
    supportedLanguages,
    isChinese,
    isEnglish,

    // 方法
    t: translate,
    translate,
    setLanguage
  }
}

// 导出类型和常量
export type { LanguageCode as Language }
