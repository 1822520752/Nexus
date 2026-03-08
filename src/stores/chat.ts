/**
 * 对话状态管理 Store
 * 管理对话会话和消息状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, Message, AIModel } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // ==================== 状态 ====================

  /**
   * 所有对话会话列表
   */
  const conversations = ref<Conversation[]>([])

  /**
   * 当前活跃的对话 ID
   */
  const currentConversationId = ref<string | null>(null)

  /**
   * 当前选择的模型
   */
  const currentModel = ref<AIModel | null>(null)

  /**
   * 是否正在加载
   */
  const isLoading = ref(false)

  /**
   * 错误信息
   */
  const error = ref<string | null>(null)

  // ==================== 计算属性 ====================

  /**
   * 当前对话会话
   */
  const currentConversation = computed(() => {
    return conversations.value.find(c => c.id === currentConversationId.value) || null
  })

  /**
   * 对话总数
   */
  const totalConversations = computed(() => conversations.value.length)

  // ==================== 方法 ====================

  /**
   * 创建新的对话会话
   * @param model - 使用的模型
   * @returns 新创建的对话
   */
  const createConversation = (model: AIModel): Conversation => {
    const conversation: Conversation = {
      id: generateId(),
      title: '新对话',
      messages: [],
      model: model.id,
      createdAt: new Date(),
      updatedAt: new Date()
    }

    conversations.value.unshift(conversation)
    currentConversationId.value = conversation.id
    currentModel.value = model

    return conversation
  }

  /**
   * 发送消息
   * @param content - 消息内容
   */
  const sendMessage = async (content: string): Promise<void> => {
    if (!currentConversation.value || !currentModel.value) {
      error.value = '请先创建对话或选择模型'
      return
    }

    isLoading.value = true
    error.value = null

    try {
      // 创建用户消息
      const userMessage: Message = {
        id: generateId(),
        conversationId: currentConversation.value.id,
        role: 'user',
        content,
        timestamp: new Date()
      }

      // 添加到对话
      currentConversation.value.messages.push(userMessage)
      currentConversation.value.updatedAt = new Date()

      // TODO: 调用后端 API 获取 AI 回复
      // 这里模拟 AI 回复
      const assistantMessage: Message = {
        id: generateId(),
        conversationId: currentConversation.value.id,
        role: 'assistant',
        content: `这是对 "${content}" 的模拟回复。实际使用时将连接到后端 AI 服务。`,
        timestamp: new Date(),
        metadata: {
          model: currentModel.value.name,
          tokens: Math.floor(Math.random() * 100) + 50,
          latency: Math.floor(Math.random() * 500) + 100
        }
      }

      currentConversation.value.messages.push(assistantMessage)
      currentConversation.value.updatedAt = new Date()

      // 更新对话标题（使用第一条消息）
      if (currentConversation.value.messages.length === 2) {
        currentConversation.value.title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '发送消息失败'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 删除对话
   * @param conversationId - 对话 ID
   */
  const deleteConversation = (conversationId: string): void => {
    const index = conversations.value.findIndex(c => c.id === conversationId)
    if (index !== -1) {
      conversations.value.splice(index, 1)
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = conversations.value[0]?.id || null
      }
    }
  }

  /**
   * 选择对话
   * @param conversationId - 对话 ID
   */
  const selectConversation = (conversationId: string): void => {
    currentConversationId.value = conversationId
  }

  /**
   * 设置当前模型
   * @param model - AI 模型
   */
  const setCurrentModel = (model: AIModel): void => {
    currentModel.value = model
  }

  /**
   * 清空所有对话
   */
  const clearAllConversations = (): void => {
    conversations.value = []
    currentConversationId.value = null
  }

  // ==================== 辅助函数 ====================

  /**
   * 生成唯一 ID
   */
  const generateId = (): string => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  return {
    // 状态
    conversations,
    currentConversationId,
    currentModel,
    isLoading,
    error,

    // 计算属性
    currentConversation,
    totalConversations,

    // 方法
    createConversation,
    sendMessage,
    deleteConversation,
    selectConversation,
    setCurrentModel,
    clearAllConversations
  }
})
