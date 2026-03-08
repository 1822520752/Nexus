"""
记忆服务模块
实现三层记忆架构：瞬时记忆、工作记忆、长期记忆
所有记忆都存储在数据库中，确保数据一致性和可靠性

架构说明：
- 瞬时记忆（INSTANT）：滑动窗口上下文管理，支持自动过期
- 工作记忆（WORKING）：短期重要信息存储，支持自动流转到长期记忆
- 长期记忆（LONG_TERM）：持久化的重要信息存储，支持跨会话检索

使用方式：
    from app.services.memory import MemoryService
    
    # 获取记忆服务实例
    memory_service = MemoryService(db_session)
    
    # 设置会话
    memory_service.set_session("session_id", "conversation_id")
    
    # 添加消息到上下文
    await memory_service.add_instant_memory("user", "你好")
    
    # 检索相关记忆
    memories = await memory_service.retrieve_relevant_memories("关键词")
"""

# 记忆服务整合层
from app.services.memory.memory_service import (
    MemoryService,
    MemoryServiceConfig,
    get_memory_service,
)

__all__ = [
    # 记忆服务
    "MemoryService",
    "MemoryServiceConfig",
    "get_memory_service",
]
