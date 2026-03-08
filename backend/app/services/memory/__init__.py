"""
记忆服务模块
实现三层记忆架构：瞬时记忆、工作记忆、长期记忆

架构说明：
- 瞬时记忆（InstantMemory）：滑动窗口上下文管理，支持 100K tokens
- 工作记忆（WorkingMemory）：短期重要信息存储，分钟级更新
- 长期记忆（LongTermMemory）：持久化的重要信息存储，跨会话

使用方式：
    from app.services.memory import MemoryService, get_memory_service
    
    # 获取记忆服务实例
    memory_service = get_memory_service()
    
    # 设置会话
    memory_service.set_session("session_id", "conversation_id")
    
    # 添加消息到上下文
    await memory_service.add_message_to_context("user", "你好")
    
    # 检索相关记忆
    memories = await memory_service.retrieve_relevant_memories("关键词")
"""

# 瞬时记忆
from app.services.memory.instant_memory import (
    InstantMemory,
    InstantMemoryManager,
    MessageContext,
    ContextSummary,
    TokenCounter,
    ContextCompressor,
)

# 工作记忆
from app.services.memory.working_memory import (
    WorkingMemory,
    WorkingMemoryItem,
    KnowledgeGraph,
    KnowledgeEntity,
    KnowledgeRelation,
    EntityType,
    RelationType,
    InformationExtractor,
)

# 长期记忆
from app.services.memory.long_term_memory import (
    LongTermMemory,
    LongTermMemoryItem,
    MemoryCategory,
    MemoryStatus,
    MemoryIndex,
    ImportanceScorer,
    MemoryForgetting,
    CrossSessionIndex,
)

# 记忆服务整合层
from app.services.memory.memory_service import (
    MemoryService,
    MemoryServiceConfig,
    get_memory_service,
    init_memory_service,
)

__all__ = [
    # 瞬时记忆
    "InstantMemory",
    "InstantMemoryManager",
    "MessageContext",
    "ContextSummary",
    "TokenCounter",
    "ContextCompressor",
    # 工作记忆
    "WorkingMemory",
    "WorkingMemoryItem",
    "KnowledgeGraph",
    "KnowledgeEntity",
    "KnowledgeRelation",
    "EntityType",
    "RelationType",
    "InformationExtractor",
    # 长期记忆
    "LongTermMemory",
    "LongTermMemoryItem",
    "MemoryCategory",
    "MemoryStatus",
    "MemoryIndex",
    "ImportanceScorer",
    "MemoryForgetting",
    "CrossSessionIndex",
    # 记忆服务
    "MemoryService",
    "MemoryServiceConfig",
    "get_memory_service",
    "init_memory_service",
]
