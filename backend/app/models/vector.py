"""
向量数据模型
定义向量数据的数据库表结构，集成 SQLite-vec 向量扩展
"""
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.base import BaseModel


class VectorSourceType(str, PyEnum):
    """
    向量来源类型枚举
    
    定义向量的来源类型
    """
    
    DOCUMENT = "document"  # 文档分块
    MEMORY = "memory"  # 记忆
    MESSAGE = "message"  # 消息
    USER_INPUT = "user_input"  # 用户输入
    OTHER = "other"  # 其他


class Vector(BaseModel):
    """
    向量模型
    
    存储文本嵌入向量，支持向量相似度搜索
    注意：实际的向量数据存储在 SQLite-vec 虚拟表中
    """
    
    __tablename__ = "vectors"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="向量ID",
    )
    
    # 来源类型
    source_type: Mapped[VectorSourceType] = mapped_column(
        Enum(VectorSourceType),
        nullable=False,
        default=VectorSourceType.OTHER,
        index=True,
        comment="来源类型",
    )
    
    # 来源 ID
    source_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="来源ID",
    )
    
    # 原始文本内容
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="原始文本内容",
    )
    
    # 嵌入模型名称
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="text-embedding-ada-002",
        index=True,
        comment="嵌入模型名称",
    )
    
    # 向量维度
    dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1536,
        comment="向量维度",
    )
    
    # 向量数据（JSON 格式的浮点数组，备用方案）
    # 当 SQLite-vec 不可用时使用此字段存储向量
    embedding_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="向量数据（JSON格式）",
    )
    
    # 向量元数据（JSON 格式）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="向量元数据（JSON格式）",
    )
    
    def __repr__(self) -> str:
        return f"<Vector(id={self.id}, source_type={self.source_type}, source_id={self.source_id})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        import json
        
        result = super().to_dict()
        # 解析 embedding_json
        if self.embedding_json:
            try:
                result["embedding"] = json.loads(self.embedding_json)
            except (json.JSONDecodeError, TypeError):
                pass
        # 解析 metadata JSON
        if self.metadata:
            try:
                result["metadata"] = json.loads(self.metadata)
            except (json.JSONDecodeError, TypeError):
                pass
        return result
    
    def set_embedding(self, embedding: List[float]) -> None:
        """
        设置向量数据
        
        Args:
            embedding: 向量数据列表
        """
        import json
        
        self.embedding_json = json.dumps(embedding)
        self.dimension = len(embedding)
    
    def get_embedding(self) -> Optional[List[float]]:
        """
        获取向量数据
        
        Returns:
            向量数据列表
        """
        import json
        
        if self.embedding_json:
            try:
                return json.loads(self.embedding_json)
            except (json.JSONDecodeError, TypeError):
                return None
        return None
