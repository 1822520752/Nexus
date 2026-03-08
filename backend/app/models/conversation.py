"""
对话会话数据模型
定义对话会话的数据库表结构
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.message import Message


class Conversation(BaseModel):
    """
    对话会话模型
    
    存储用户的对话会话信息
    """
    
    __tablename__ = "conversations"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="对话ID",
    )
    
    # 对话标题
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="新对话",
        comment="对话标题",
    )
    
    # 使用的模型 ID（关联 model_configs 表）
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("model_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联模型ID",
    )
    
    # 对话摘要
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="对话摘要",
    )
    
    # 消息总数
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="消息总数",
    )
    
    # 总 Token 数
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总Token数",
    )
    
    # 对话元数据（JSON 格式）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="对话元数据（JSON格式）",
    )
    
    # 是否置顶
    is_pinned: Mapped[bool] = mapped_column(
        default=False,
        index=True,
        comment="是否置顶",
    )
    
    # 是否归档
    is_archived: Mapped[bool] = mapped_column(
        default=False,
        index=True,
        comment="是否归档",
    )
    
    # 关联消息
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"
    
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
