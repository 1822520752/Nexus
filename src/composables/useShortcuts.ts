/**
 * 快捷键管理 Composable
 * 提供全局快捷键注册和管理功能
 */
import { onMounted, onUnmounted, ref, computed } from 'vue'

/**
 * 快捷键配置接口
 */
export interface ShortcutConfig {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  handler: (event: KeyboardEvent) => void
  description?: string
  preventDefault?: boolean
}

/**
 * 已注册的快捷键映射
 */
const registeredShortcuts = new Map<string, ShortcutConfig>()

/**
 * 生成快捷键唯一标识
 * @param config - 快捷键配置
 * @returns 唯一标识字符串
 */
const generateShortcutId = (config: ShortcutConfig): string => {
  const modifiers: string[] = []
  if (config.ctrl) modifiers.push('ctrl')
  if (config.shift) modifiers.push('shift')
  if (config.alt) modifiers.push('alt')
  if (config.meta) modifiers.push('meta')
  modifiers.push(config.key.toLowerCase())
  return modifiers.join('+')
}

/**
 * 检查键盘事件是否匹配快捷键配置
 * @param event - 键盘事件
 * @param config - 快捷键配置
 * @returns 是否匹配
 */
const matchesShortcut = (event: KeyboardEvent, config: ShortcutConfig): boolean => {
  const keyMatch = event.key.toLowerCase() === config.key.toLowerCase()
  const ctrlMatch = config.ctrl ? (event.ctrlKey || event.metaKey) : !event.ctrlKey && !event.metaKey
  const shiftMatch = config.shift ? event.shiftKey : !event.shiftKey
  const altMatch = config.alt ? event.altKey : !event.altKey

  return keyMatch && ctrlMatch && shiftMatch && altMatch
}

/**
 * 全局键盘事件处理器
 * @param event - 键盘事件
 */
const handleKeyDown = (event: KeyboardEvent): void => {
  // 如果焦点在输入框中，跳过某些快捷键
  const target = event.target as HTMLElement
  const isInputFocused = target.tagName === 'INPUT' || 
                         target.tagName === 'TEXTAREA' || 
                         target.isContentEditable

  for (const [, config] of registeredShortcuts) {
    if (matchesShortcut(event, config)) {
      // 如果是输入框，某些快捷键仍然生效
      if (isInputFocused && !config.ctrl && !config.alt) {
        continue
      }

      // 阻止默认行为
      if (config.preventDefault !== false) {
        event.preventDefault()
      }

      // 执行处理器
      config.handler(event)
      return
    }
  }
}

/**
 * 快捷键管理 Hook
 * @param shortcuts - 快捷键配置列表（可选）
 */
export function useShortcuts(shortcuts?: ShortcutConfig[]) {
  /**
   * 是否启用快捷键
   */
  const enabled = ref(true)

  /**
   * 已注册的快捷键列表
   */
  const registeredList = computed(() => {
    return Array.from(registeredShortcuts.entries()).map(([id, config]) => ({
      id,
      ...config
    }))
  })

  /**
   * 注册单个快捷键
   * @param config - 快捷键配置
   * @returns 取消注册函数
   */
  const register = (config: ShortcutConfig): (() => void) => {
    const id = generateShortcutId(config)
    registeredShortcuts.set(id, config)

    // 返回取消注册函数
    return () => {
      registeredShortcuts.delete(id)
    }
  }

  /**
   * 批量注册快捷键
   * @param configs - 快捷键配置列表
   * @returns 取消注册函数
   */
  const registerAll = (configs: ShortcutConfig[]): (() => void) => {
    const unregisterFns = configs.map(register)
    return () => {
      unregisterFns.forEach(fn => fn())
    }
  }

  /**
   * 取消注册快捷键
   * @param config - 快捷键配置
   */
  const unregister = (config: ShortcutConfig): void => {
    const id = generateShortcutId(config)
    registeredShortcuts.delete(id)
  }

  /**
   * 清空所有快捷键
   */
  const clearAll = (): void => {
    registeredShortcuts.clear()
  }

  /**
   * 启用快捷键
   */
  const enable = (): void => {
    enabled.value = true
  }

  /**
   * 禁用快捷键
   */
  const disable = (): void => {
    enabled.value = false
  }

  /**
   * 切换启用状态
   */
  const toggle = (): void => {
    enabled.value = !enabled.value
  }

  // 组件挂载时注册传入的快捷键
  let unregisterFn: (() => void) | null = null

  onMounted(() => {
    // 添加全局键盘事件监听
    window.addEventListener('keydown', handleKeyDown)

    // 注册传入的快捷键
    if (shortcuts && shortcuts.length > 0) {
      unregisterFn = registerAll(shortcuts)
    }
  })

  // 组件卸载时清理
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
    if (unregisterFn) {
      unregisterFn()
    }
  })

  return {
    // 状态
    enabled,
    registeredList,

    // 方法
    register,
    registerAll,
    unregister,
    clearAll,
    enable,
    disable,
    toggle
  }
}

/**
 * 预定义快捷键配置
 */
export const defaultShortcuts: ShortcutConfig[] = [
  {
    key: 'Enter',
    ctrl: true,
    handler: () => {
      // 发送消息 - 由组件处理
      window.dispatchEvent(new CustomEvent('shortcut:send-message'))
    },
    description: '发送消息'
  },
  {
    key: 'l',
    ctrl: true,
    handler: () => {
      window.dispatchEvent(new CustomEvent('shortcut:clear-chat'))
    },
    description: '清空对话'
  },
  {
    key: 'n',
    ctrl: true,
    handler: () => {
      window.dispatchEvent(new CustomEvent('shortcut:new-conversation'))
    },
    description: '新建对话'
  },
  {
    key: 's',
    ctrl: true,
    handler: () => {
      window.dispatchEvent(new CustomEvent('shortcut:save-settings'))
    },
    description: '保存设置'
  },
  {
    key: ',',
    ctrl: true,
    handler: () => {
      window.dispatchEvent(new CustomEvent('shortcut:open-settings'))
    },
    description: '打开设置'
  }
]
