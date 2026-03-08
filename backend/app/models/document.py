"""
文档数据模型
定义文档的数据库表结构
"""
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class DocumentStatus(str, PyEnum):
    """
    文档状态枚举
    
    定义文档处理的各个状态
    """
    
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 处理失败


class DocumentType(str, PyEnum):
    """
    文档类型枚举
    
    定义支持的文档类型
    """
    
    PDF = "pdf"
    MARKDOWN = "md"
    TEXT = "txt"
    HTML = "html"
    DOCX = "docx"
    CSV = "csv"
    JSON = "json"
    OTHER = "other"


class Document(BaseModel):
    """
    文档模型
    
    存储上传的文档信息
    """
    
    __tablename__ = "documents"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="文档ID",
    )
    
    # 文件名
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="文件名",
    )
    
    # 文件路径
    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="文件路径",
    )
    
    # 文件类型
    file_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        nullable=False,
        default=DocumentType.OTHER,
        comment="文件类型",
    )
    
    # 文件大小（字节）
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="文件大小（字节）",
    )
    
    # 文件哈希（用于去重）
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="文件哈希（SHA256）",
    )
    
    # 处理状态
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
        comment="处理状态",
    )
    
    # 分块数量
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="分块数量",
    )
    
    # 文档标题
    title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="文档标题",
    )
    
    # 文档摘要
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文档摘要",
    )
    
    # 文档元数据（JSON 格式）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文档元数据（JSON格式）",
    )
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    
    # 关联分块
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
    
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
