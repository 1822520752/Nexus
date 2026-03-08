"""
嵌入服务模块
提供统一的文本向量化接口，支持多种嵌入模型
"""
from app.services.embedding.embedding_service import (
    EmbeddingConfig,
    EmbeddingResult,
    EmbeddingService,
    EmbeddingModelType,
    embedding_service,
)

__all__ = [
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingService",
    "EmbeddingModelType",
    "embedding_service",
]
