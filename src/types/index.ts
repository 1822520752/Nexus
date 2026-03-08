/**
 * 全局类型定义文件
 * 定义应用中使用的核心类型
 */

/**
 * 用户信息类型
 */
export interface User {
  id: string
  name: string
  email?: string
  avatar?: string
  createdAt: Date
  updatedAt: Date
}

/**
 * 对话消息类型
 */
export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: MessageMetadata
}

/**
 * 消息元数据
 */
export interface MessageMetadata {
  model?: string
  tokens?: number
  latency?: number
  error?: string
}

/**
 * 对话会话类型
 */
export interface Conversation {
  id: string
  title: string
  messages: Message[]
  model: string
  createdAt: Date
  updatedAt: Date
  metadata?: ConversationMetadata
}

/**
 * 对话元数据
 */
export interface ConversationMetadata {
  totalTokens?: number
  totalMessages?: number
  lastMessageAt?: Date
}

/**
 * AI 模型提供商类型
 */
export type ModelProvider = 'ollama' | 'openai' | 'deepseek' | 'anthropic' | 'custom'

/**
 * AI 模型类型
 */
export type ModelType = 'chat' | 'embedding' | 'image' | 'audio'

/**
 * AI 模型配置类型（与后端 ModelConfig 对应）
 */
export interface ModelConfig {
  id: number
  name: string
  provider: ModelProvider
  base_url?: string
  model_type: ModelType
  is_default: boolean
  is_active: boolean
  max_tokens: number
  temperature: number
  context_window: number
  config?: Record<string, unknown>
  created_at: string
  updated_at: string
}

/**
 * 创建模型配置请求类型
 */
export interface CreateModelConfigRequest {
  name: string
  provider: ModelProvider
  api_key?: string
  base_url?: string
  model_type?: ModelType
  is_default?: boolean
  max_tokens?: number
  temperature?: number
  context_window?: number
  config?: Record<string, unknown>
}

/**
 * 更新模型配置请求类型
 */
export interface UpdateModelConfigRequest {
  name?: string
  api_key?: string
  base_url?: string
  is_default?: boolean
  is_active?: boolean
  max_tokens?: number
  temperature?: number
  context_window?: number
  config?: Record<string, unknown>
}

/**
 * 模型状态信息
 */
export interface ModelStatus {
  status: 'available' | 'unavailable' | 'error' | 'not_found' | 'unknown'
  available: boolean
  message: string
  model_info?: Record<string, unknown>
  error?: string
  checked_at: string
}

/**
 * 模型测试结果
 */
export interface ModelTestResult {
  success: boolean
  message: string
  response?: string
  error?: string
  tested_at: string
}

/**
 * 提供商配置信息
 */
export interface ProviderConfig {
  name: string
  description: string
  requires_api_key: boolean
  default_base_url: string
  supports_local: boolean
}

/**
 * 可用模型信息（从提供商获取）
 */
export interface AvailableModel {
  name: string
  description?: string
  size?: number
  modified_at?: string
  digest?: string
}

/**
 * 模型配置列表响应
 */
export interface ModelConfigListResponse {
  items: ModelConfig[]
  total: number
}

/**
 * 提供商列表响应
 */
export interface ProvidersResponse {
  providers: Record<string, ProviderConfig>
  total: number
}

/**
 * 兼容旧版本的 AIModel 类型（保持向后兼容）
 * @deprecated 请使用 ModelConfig
 */
export interface AIModel {
  id: string
  name: string
  provider: ModelProvider | 'local'
  endpoint?: string
  apiKey?: string
  maxTokens: number
  temperature: number
  contextWindow: number
  enabled: boolean
  createdAt: Date
  updatedAt: Date
}

/**
 * 应用设置类型
 */
export interface AppSettings {
  theme: 'light' | 'dark' | 'system'
  language: 'zh-CN' | 'en-US'
  defaultModel: string
  autoSave: boolean
  sendOnEnter: boolean
  showTokenCount: boolean
  backendUrl: string
}

/**
 * API 响应基础类型
 */
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: ApiError
  timestamp: Date
}

/**
 * API 错误类型
 */
export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page: number
  pageSize: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

/**
 * 分页响应数据
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// ==================== 文档管理相关类型 ====================

/**
 * 文档处理状态
 */
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'

/**
 * 文档类型
 */
export type DocumentType = 'pdf' | 'md' | 'txt' | 'docx' | 'html'

/**
 * 文档信息类型
 */
export interface Document {
  id: number
  filename: string
  original_name: string
  file_type: DocumentType
  file_size: number
  file_path: string
  status: DocumentStatus
  chunk_count: number
  error_message?: string
  created_at: string
  updated_at: string
}

/**
 * 文档分块信息
 */
export interface DocumentChunk {
  id: number
  document_id: number
  chunk_index: number
  content: string
  token_count: number
  created_at: string
}

/**
 * 文档上传进度信息
 */
export interface UploadProgress {
  fileId: string
  fileName: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  error?: string
}

/**
 * 创建文档请求类型
 */
export interface CreateDocumentRequest {
  file: File
}

/**
 * 更新文档请求类型
 */
export interface UpdateDocumentRequest {
  filename?: string
}

/**
 * 文档列表响应
 */
export interface DocumentListResponse {
  items: Document[]
  total: number
}

/**
 * 文档详情响应
 */
export interface DocumentDetailResponse {
  document: Document
  chunks: DocumentChunk[]
}

// ==================== 动作管理相关类型 ====================

/**
 * 动作分类类型
 */
export type ActionCategory = 'file' | 'note' | 'system' | 'script'

/**
 * 动作权限级别
 */
export type PermissionLevel = 'low' | 'medium' | 'high' | 'critical'

/**
 * 动作执行状态
 */
export type ActionStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled'

/**
 * 动作定义类型
 */
export interface ActionDefinition {
  id: string
  name: string
  description: string
  category: ActionCategory
  permissionLevel: PermissionLevel
  icon: string
  params: ActionParam[]
  examples?: string[]
  risks?: string[]
  requiresConfirmation: boolean
}

/**
 * 动作参数定义
 */
export interface ActionParam {
  name: string
  type: 'string' | 'number' | 'boolean' | 'path' | 'select'
  required: boolean
  default?: unknown
  description?: string
  options?: { label: string; value: string | number }[]
  validation?: {
    min?: number
    max?: number
    pattern?: string
    message?: string
  }
}

/**
 * 动作执行请求
 */
export interface ActionExecutionRequest {
  actionId: string
  params: Record<string, unknown>
  conversationId?: string
}

/**
 * 动作执行结果
 */
export interface ActionExecutionResult {
  id: string
  actionId: string
  actionName: string
  status: ActionStatus
  params: Record<string, unknown>
  result?: unknown
  error?: string
  startedAt: Date
  completedAt?: Date
  duration?: number
}

/**
 * 动作历史记录
 */
export interface ActionHistoryItem {
  id: string
  actionId: string
  actionName: string
  category: ActionCategory
  status: ActionStatus
  params: Record<string, unknown>
  result?: unknown
  error?: string
  executedAt: Date
  duration?: number
  conversationId?: string
}

/**
 * 待确认动作
 */
export interface PendingAction {
  id: string
  action: ActionDefinition
  params: Record<string, unknown>
  resolve: (confirmed: boolean) => void
  timestamp: Date
}

/**
 * 权限设置
 */
export interface PermissionSettings {
  // 安全模式开关
  safeMode: boolean
  // 各权限级别是否需要确认
  confirmLevels: Record<PermissionLevel, boolean>
  // 敏感目录列表
  sensitiveDirectories: string[]
  // 允许的脚本路径
  allowedScriptPaths: string[]
  // 是否记录所有操作
  logAllActions: boolean
  // 自动拒绝高风险操作
  autoRejectHighRisk: boolean
}

/**
 * 默认权限设置
 */
export const defaultPermissionSettings: PermissionSettings = {
  safeMode: true,
  confirmLevels: {
    low: false,
    medium: true,
    high: true,
    critical: true
  },
  sensitiveDirectories: [
    'C:\\Windows',
    'C:\\Program Files',
    'C:\\Program Files (x86)',
    'C:\\Users\\*\\AppData'
  ],
  allowedScriptPaths: [],
  logAllActions: true,
  autoRejectHighRisk: false
}

// ==================== 记忆管理相关类型 ====================

/**
 * 记忆类型
 */
export type MemoryType = 'instant' | 'working' | 'long_term'

/**
 * 记忆分类
 */
export type MemoryCategory = 'fact' | 'preference' | 'experience' | 'skill' | 'context' | 'relationship' | 'schedule' | 'project'

/**
 * 记忆状态
 */
export type MemoryStatus = 'active' | 'archived' | 'forgotten' | 'consolidated'

/**
 * 记忆信息类型
 */
export interface Memory {
  id: number
  memoryType: MemoryType
  content: string
  importance: number
  accessCount: number
  lastAccessedAt?: string
  expiresAt?: string
  sourceType?: string
  sourceId?: number
  sessionId?: string
  conversationId?: string
  tags: string[]
  metadata: Record<string, unknown>
  entities: string[]
  entityIds: number[]
  category?: MemoryCategory
  keywords: string[]
  status: MemoryStatus
  isConsolidated: boolean
  embeddingId?: string
  createdAt: string
  updatedAt: string
}

/**
 * 创建记忆请求类型
 */
export interface CreateMemoryRequest {
  memoryType: MemoryType
  content: string
  importance?: number
  sourceType?: string
  sourceId?: number
  tags?: string[]
  metadata?: Record<string, unknown>
  expiresAt?: string
}

/**
 * 更新记忆请求类型
 */
export interface UpdateMemoryRequest {
  memoryType?: MemoryType
  content?: string
  importance?: number
  tags?: string[]
  metadata?: Record<string, unknown>
}

/**
 * 记忆搜索参数
 */
export interface MemorySearchParams {
  query: string
  memoryTypes?: MemoryType[]
  minImportance?: number
  topK?: number
}

/**
 * 记忆搜索结果
 */
export interface MemorySearchResult {
  memoryId: number
  content: string
  memoryType: MemoryType
  importance: number
  score: number
  tags: string[]
  metadata: Record<string, unknown>
}

/**
 * 记忆统计信息
 */
export interface MemoryStats {
  totalCount: number
  instantCount: number
  workingCount: number
  longTermCount: number
  avgImportance: number
  totalAccessCount: number
}

/**
 * 记忆列表响应
 */
export interface MemoryListResponse {
  items: Memory[]
  total: number
  skip: number
  limit: number
}

/**
 * 记忆类型配置
 */
export const memoryTypeConfig: Record<MemoryType, { label: string; color: string; description: string }> = {
  instant: {
    label: '瞬时记忆',
    color: 'blue',
    description: '临时存储的信息，生命周期较短'
  },
  working: {
    label: '工作记忆',
    color: 'yellow',
    description: '当前正在处理的信息，用于任务执行'
  },
  long_term: {
    label: '长期记忆',
    color: 'green',
    description: '持久存储的重要信息，可长期检索'
  }
}

/**
 * 记忆分类配置
 */
export const memoryCategoryConfig: Record<MemoryCategory, { label: string; description: string }> = {
  fact: { label: '事实', description: '事实性知识' },
  preference: { label: '偏好', description: '用户偏好' },
  experience: { label: '经验', description: '经验性知识' },
  skill: { label: '技能', description: '技能知识' },
  context: { label: '上下文', description: '上下文背景' },
  relationship: { label: '关系', description: '关系信息' },
  schedule: { label: '日程', description: '日程安排' },
  project: { label: '项目', description: '项目信息' },
}
