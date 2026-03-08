# 服务层模块
# 用于封装业务逻辑和外部服务调用

from app.services.document import (
    DocumentService,
    PDFProcessor,
    TextChunker,
    TextProcessor,
)
from app.services.vector_service import VectorService, DistanceMetric
from app.services.action import (
    ActionService,
    ActionServiceFactory,
    CommandExecutor,
    PermissionChecker,
    SandboxEnvironment,
    SandboxManager,
)
from app.services.embedding import (
    EmbeddingService,
    EmbeddingConfig,
    EmbeddingResult,
    EmbeddingModelType,
)
from app.services.retrieval import (
    HybridRetrieval,
    RetrievalResult,
    RetrievalConfig,
    BM25Retriever,
)
from app.services.memory import (
    # 记忆服务
    MemoryService,
    MemoryServiceConfig,
    get_memory_service,
    init_memory_service,
    # 瞬时记忆
    InstantMemory,
    InstantMemoryManager,
    MessageContext,
    TokenCounter,
    ContextCompressor,
    # 工作记忆
    WorkingMemory,
    WorkingMemoryItem,
    KnowledgeGraph,
    KnowledgeEntity,
    KnowledgeRelation,
    EntityType,
    RelationType,
    InformationExtractor,
    # 长期记忆
    LongTermMemory,
    LongTermMemoryItem,
    MemoryCategory,
    MemoryStatus,
    ImportanceScorer,
    MemoryForgetting,
    CrossSessionIndex,
)

__all__ = [
    "DocumentService",
    "PDFProcessor",
    "TextProcessor",
    "TextChunker",
    "VectorService",
    "DistanceMetric",
    # 动作服务
    "ActionService",
    "ActionServiceFactory",
    "CommandExecutor",
    "PermissionChecker",
    "SandboxEnvironment",
    "SandboxManager",
    # 嵌入服务
    "EmbeddingService",
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingModelType",
    # 检索服务
    "HybridRetrieval",
    "RetrievalResult",
    "RetrievalConfig",
    "BM25Retriever",
    # 记忆服务
    "MemoryService",
    "MemoryServiceConfig",
    "get_memory_service",
    "init_memory_service",
    # 瞬时记忆
    "InstantMemory",
    "InstantMemoryManager",
    "MessageContext",
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
    "ImportanceScorer",
    "MemoryForgetting",
    "CrossSessionIndex",
]
