"""
文档分块数据模型
定义文档分块的数据库表结构
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(BaseModel):
    """
    文档分块模型
    
    存储文档的分块内容，用于向量检索
    """
    
    __tablename__ = "document_chunks"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="分块ID",
    )
    
    # 关联文档 ID
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联文档ID",
    )
    
    # 分块内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="分块内容",
    )
    
    # 分块索引
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="分块索引",
    )
    
    # 分块哈希
    chunk_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="分块哈希",
    )
    
    # Token 数量
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Token数量",
    )
    
    # 字符数
    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="字符数",
    )
    
    # 起始位置
    start_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="起始字符位置",
    )
    
    # 结束位置
    end_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="结束字符位置",
    )
    
    # 分块元数据（JSON 格式，包含页码、标题等）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="分块元数据（JSON格式）",
    )
    
    # 关联文档
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"
    
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
