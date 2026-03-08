"""
记忆数据模型
定义记忆的数据库表结构
"""
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, Float, Integer, String, Text
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


class Memory(BaseModel):
    """
    记忆模型
    
    存储不同类型的记忆数据，支持 AI 的记忆系统
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
    last_accessed_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="最后访问时间",
    )
    
    # 过期时间（用于即时记忆的自动清理）
    expires_at: Mapped[Optional[str]] = mapped_column(
        String(50),
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
    
    # 记忆标签（JSON 数组）
    tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="记忆标签（JSON数组）",
    )
    
    # 记忆元数据（JSON 格式）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="记忆元数据（JSON格式）",
    )
    
    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.memory_type}, importance={self.importance})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        import json
        
        result = super().to_dict()
        # 解析 tags JSON
        if self.tags:
            try:
                result["tags"] = json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                pass
        # 解析 metadata JSON
        if self.metadata:
            try:
                result["metadata"] = json.loads(self.metadata)
            except (json.JSONDecodeError, TypeError):
                pass
        return result
    
    def increment_access(self) -> None:
        """
        增加访问次数并更新最后访问时间
        """
        from datetime import datetime
        
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow().isoformat()
