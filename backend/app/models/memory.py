"""
记忆数据模型
定义记忆的数据库表结构，支持三层记忆架构
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class MemoryType(str, PyEnum):
    """
    记忆类型枚举
    
    定义不同类型的记忆
    """
    
    INSTANT = "instant"  # 即时记忆：当前对话上下文
    WORKING = "working"  # 工作记忆：短期重要信息
    LONG_TERM = "long_term"  # 长期记忆：持久化的重要信息


class MemoryCategory(str, PyEnum):
    """
    记忆分类枚举
    
    定义长期记忆的分类类型
    """
    
    FACT = "fact"  # 事实性知识
    PREFERENCE = "preference"  # 用户偏好
    EXPERIENCE = "experience"  # 经验性知识
    SKILL = "skill"  # 技能知识
    CONTEXT = "context"  # 上下文背景
    RELATIONSHIP = "relationship"  # 关系信息
    SCHEDULE = "schedule"  # 日程安排
    PROJECT = "project"  # 项目信息


class MemoryStatus(str, PyEnum):
    """
    记忆状态枚举
    
    定义记忆的生命周期状态
    """
    
    ACTIVE = "active"  # 活跃状态
    ARCHIVED = "archived"  # 已归档
    FORGOTTEN = "forgotten"  # 已遗忘
    CONSOLIDATED = "consolidated"  # 已巩固


class Memory(BaseModel):
    """
    记忆模型
    
    存储不同类型的记忆数据，支持三层记忆架构：
    - 即时记忆（INSTANT）：滑动窗口上下文管理
    - 工作记忆（WORKING）：短期重要信息存储
    - 长期记忆（LONG_TERM）：持久化的重要信息存储
    """
    
    __tablename__ = "memories"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="记忆ID",
    )
    
    # 记忆类型
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType),
        nullable=False,
        default=MemoryType.WORKING,
        index=True,
        comment="记忆类型",
    )
    
    # 记忆内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="记忆内容",
    )
    
    # 重要性评分（0-1）
    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        index=True,
        comment="重要性评分（0-1）",
    )
    
    # 访问次数
    access_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="访问次数",
    )
    
    # 最后访问时间（用于 LRU 淘汰）
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后访问时间",
    )
    
    # 过期时间（用于即时记忆的自动清理）
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="过期时间",
    )
    
    # 来源类型：conversation, document, user_input, system
    source_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="来源类型",
    )
    
    # 来源 ID
    source_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="来源ID",
    )
    
    # 会话追踪（新增）
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="会话ID",
    )
    
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="对话ID",
    )
    
    # 记忆标签（使用原生 JSON 类型）
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="记忆标签",
    )
    
    # 记忆元数据（使用原生 JSON 类型）
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="记忆元数据",
    )
    
    # 知识图谱支持（新增）
    entities: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="关联实体列表",
    )
    
    entity_ids: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="实体ID列表",
    )
    
    # 记忆分类（长期记忆，新增）
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="记忆分类",
    )
    
    keywords: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
        comment="关键词列表",
    )
    
    # 记忆状态（新增）
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
        comment="记忆状态",
    )
    
    is_consolidated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已巩固",
    )
    
    # 向量嵌入 ID（用于语义搜索，新增）
    embedding_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="向量嵌入ID",
    )
    
    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.memory_type}, importance={self.importance})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        result = super().to_dict()
        
        # 确保列表字段不为 None
        if result.get("tags") is None:
            result["tags"] = []
        if result.get("metadata") is None:
            result["metadata"] = {}
        if result.get("entities") is None:
            result["entities"] = []
        if result.get("entity_ids") is None:
            result["entity_ids"] = []
        if result.get("keywords") is None:
            result["keywords"] = []
        
        return result
    
    def increment_access(self) -> None:
        """
        增加访问次数并更新最后访问时间
        """
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """
        检查记忆是否已过期
        
        Returns:
            是否已过期
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def should_consolidate(self, threshold: float = 0.7, min_access_count: int = 3) -> bool:
        """
        检查记忆是否应该被巩固
        
        Args:
            threshold: 重要性阈值
            min_access_count: 最小访问次数
            
        Returns:
            是否应该巩固
        """
        if self.memory_type != MemoryType.WORKING:
            return False
        if self.importance < threshold:
            return False
        if self.access_count < min_access_count:
            return False
        return not self.is_consolidated
    
    def should_forget(self, days_threshold: int = 30, min_access_count: int = 2) -> bool:
        """
        检查记忆是否应该被遗忘
        
        Args:
            days_threshold: 天数阈值
            min_access_count: 最小访问次数
            
        Returns:
            是否应该遗忘
        """
        if self.status == "forgotten":
            return False
        
        if self.last_accessed_at is None:
            return False
        
        days_since_access = (datetime.utcnow() - self.last_accessed_at).days
        return days_since_access > days_threshold and self.access_count < min_access_count
