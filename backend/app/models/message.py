"""
消息数据模型
定义对话消息的数据库表结构
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Message(BaseModel):
    """
    消息模型
    
    存储对话中的每条消息
    """
    
    __tablename__ = "messages"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="消息ID",
    )
    
    # 所属对话 ID
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联对话ID",
    )
    
    # 消息角色：user, assistant, system
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="消息角色",
    )
    
    # 消息内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )
    
    # Token 数量
    tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Token数量",
    )
    
    # 消息元数据（JSON 格式，包含 latency、model 等）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="消息元数据（JSON格式）",
    )
    
    # 父消息 ID（用于消息分支）
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        comment="父消息ID",
    )
    
    # 关联对话
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        import json
        
        result = super().to_dict()
        # 解析 metadata JSON
        if self.metadata:
            try:
                result["metadata"] = json.loads(self.metadata)
            except (json.JSONDecodeError, TypeError):
                pass
        return result
