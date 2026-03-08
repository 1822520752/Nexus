"""
向量检索服务
提供向量相似度搜索和混合检索功能
支持 SQLite-vec 向量扩展和多种距离度量
"""
import json
import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, delete, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.models.vector import Vector, VectorSourceType


class DistanceMetric(str, Enum):
    """
    距离度量类型枚举
    
    定义向量相似度计算的距离度量方法
    """
    
    COSINE = "cosine"  # 余弦相似度
    EUCLIDEAN = "euclidean"  # 欧几里得距离
    DOT_PRODUCT = "dot_product"  # 点积


class VectorSearchResult:
    """
    向量搜索结果类
    
    封装向量搜索的结果数据
    """
    
    def __init__(
        self,
        vector_id: int,
        content: str,
        score: float,
        source_type: str,
        source_id: int,
        metadata: Optional[dict] = None,
    ):
        """
        初始化搜索结果
        
        Args:
            vector_id: 向量 ID
            content: 文本内容
            score: 相似度分数
            source_type: 来源类型
            source_id: 来源 ID
            metadata: 元数据
        """
        self.vector_id = vector_id
        self.content = content
        self.score = score
        self.source_type = source_type
        self.source_id = source_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            "vector_id": self.vector_id,
            "content": self.content,
            "score": self.score,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "metadata": self.metadata,
        }


class VectorService:
    """
    向量服务类
    
    提供向量存储、检索和管理功能
    支持多种距离度量和批量操作
    """
    
    def __init__(self, dimension: int = None):
        """
        初始化向量服务
        
        Args:
            dimension: 向量维度，默认使用配置中的维度
        """
        self.dimension = dimension or settings.VECTOR_DIMENSION
        self._use_sqlite_vec = False  # 是否使用 SQLite-vec 扩展
    
    async def store_vector(
        self,
        session: AsyncSession,
        content: str,
        embedding: List[float],
        source_type: VectorSourceType,
        source_id: int,
        embedding_model: str = "text-embedding-ada-002",
        metadata: Optional[dict] = None,
    ) -> Vector:
        """
        存储向量
        
        Args:
            session: 数据库会话
            content: 原始文本内容
            embedding: 向量数据
            source_type: 来源类型
            source_id: 来源 ID
            embedding_model: 嵌入模型名称
            metadata: 元数据
            
        Returns:
            创建的向量对象
        """
        # 验证向量维度
        self._validate_embedding(embedding)
        
        vector = Vector(
            source_type=source_type,
            source_id=source_id,
            content=content,
            embedding_model=embedding_model,
            dimension=len(embedding),
            metadata=json.dumps(metadata) if metadata else None,
        )
        vector.set_embedding(embedding)
        
        session.add(vector)
        await session.flush()
        
        logger.debug(f"存储向量: id={vector.id}, source={source_type}:{source_id}")
        return vector
    
    def _validate_embedding(self, embedding: List[float]) -> None:
        """
        验证向量数据
        
        Args:
            embedding: 向量数据
            
        Raises:
            ValueError: 向量维度不匹配时抛出
        """
        if not embedding:
            raise ValueError("向量数据不能为空")
        
        if len(embedding) != self.dimension:
            logger.warning(
                f"向量维度不匹配: 期望 {self.dimension}, 实际 {len(embedding)}"
            )
    
    async def batch_store_vectors(
        self,
        session: AsyncSession,
        items: List[Tuple[str, List[float], VectorSourceType, int, Optional[dict]]],
        embedding_model: str = "text-embedding-ada-002",
    ) -> List[Vector]:
        """
        批量存储向量
        
        Args:
            session: 数据库会话
            items: 向量数据列表，每项为 (content, embedding, source_type, source_id, metadata)
            embedding_model: 嵌入模型名称
            
        Returns:
            创建的向量对象列表
        """
        vectors = []
        for content, embedding, source_type, source_id, metadata in items:
            vector = Vector(
                source_type=source_type,
                source_id=source_id,
                content=content,
                embedding_model=embedding_model,
                dimension=len(embedding),
                metadata=json.dumps(metadata) if metadata else None,
            )
            vector.set_embedding(embedding)
            vectors.append(vector)
        
        session.add_all(vectors)
        await session.flush()
        
        logger.debug(f"批量存储向量: count={len(vectors)}")
        return vectors
    
    async def similarity_search(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        top_k: int = 10,
        source_types: Optional[List[VectorSourceType]] = None,
        min_score: float = 0.0,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
    ) -> List[VectorSearchResult]:
        """
        向量相似度搜索
        
        Args:
            session: 数据库会话
            query_embedding: 查询向量
            top_k: 返回结果数量
            source_types: 过滤来源类型
            min_score: 最小相似度分数
            distance_metric: 距离度量方法
            
        Returns:
            搜索结果列表
        """
        # 构建基础查询
        query = select(Vector)
        
        # 添加来源类型过滤
        if source_types:
            query = query.where(Vector.source_type.in_(source_types))
        
        # 执行查询
        result = await session.execute(query)
        vectors = result.scalars().all()
        
        # 根据距离度量选择计算方法
        if distance_metric == DistanceMetric.COSINE:
            score_func = self._cosine_similarity
        elif distance_metric == DistanceMetric.EUCLIDEAN:
            score_func = self._euclidean_distance_score
        else:
            score_func = self._dot_product_score
        
        # 计算相似度并排序
        results = []
        for vector in vectors:
            embedding = vector.get_embedding()
            if embedding:
                score = score_func(query_embedding, embedding)
                if score >= min_score:
                    metadata = None
                    if vector.metadata:
                        try:
                            metadata = json.loads(vector.metadata)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    results.append(
                        VectorSearchResult(
                            vector_id=vector.id,
                            content=vector.content,
                            score=score,
                            source_type=vector.source_type.value,
                            source_id=vector.source_id,
                            metadata=metadata,
                        )
                    )
        
        # 按相似度排序并返回 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    async def hybrid_search(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        source_types: Optional[List[VectorSourceType]] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[VectorSearchResult]:
        """
        混合检索（向量 + 关键词）
        
        Args:
            session: 数据库会话
            query_embedding: 查询向量
            query_text: 查询文本
            top_k: 返回结果数量
            source_types: 过滤来源类型
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            
        Returns:
            搜索结果列表
        """
        # 构建基础查询
        query = select(Vector)
        
        # 添加来源类型过滤
        if source_types:
            query = query.where(Vector.source_type.in_(source_types))
        
        # 关键词搜索条件
        keywords = query_text.lower().split()
        if keywords:
            keyword_conditions = [
                func.lower(Vector.content).contains(keyword) for keyword in keywords[:5]  # 限制关键词数量
            ]
            query = query.where(or_(*keyword_conditions))
        
        # 执行查询
        result = await session.execute(query)
        vectors = result.scalars().all()
        
        # 计算混合分数
        results = []
        for vector in vectors:
            embedding = vector.get_embedding()
            vector_score = 0.0
            if embedding:
                vector_score = self._cosine_similarity(query_embedding, embedding)
            
            # 计算关键词匹配分数
            keyword_score = self._keyword_match_score(query_text, vector.content)
            
            # 混合分数
            final_score = vector_weight * vector_score + keyword_weight * keyword_score
            
            metadata = None
            if vector.metadata:
                try:
                    metadata = json.loads(vector.metadata)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            results.append(
                VectorSearchResult(
                    vector_id=vector.id,
                    content=vector.content,
                    score=final_score,
                    source_type=vector.source_type.value,
                    source_id=vector.source_id,
                    metadata=metadata,
                )
            )
        
        # 按分数排序并返回 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    async def delete_by_source(
        self,
        session: AsyncSession,
        source_type: VectorSourceType,
        source_id: int,
    ) -> int:
        """
        根据来源删除向量
        
        Args:
            session: 数据库会话
            source_type: 来源类型
            source_id: 来源 ID
            
        Returns:
            删除的向量数量
        """
        query = delete(Vector).where(
            and_(
                Vector.source_type == source_type,
                Vector.source_id == source_id,
            )
        )
        result = await session.execute(query)
        deleted_count = result.rowcount
        
        logger.debug(f"删除向量: source={source_type}:{source_id}, count={deleted_count}")
        return deleted_count
    
    async def delete_by_model(
        self,
        session: AsyncSession,
        embedding_model: str,
    ) -> int:
        """
        根据嵌入模型删除向量
        
        Args:
            session: 数据库会话
            embedding_model: 嵌入模型名称
            
        Returns:
            删除的向量数量
        """
        query = delete(Vector).where(Vector.embedding_model == embedding_model)
        result = await session.execute(query)
        deleted_count = result.rowcount
        
        logger.debug(f"删除向量: model={embedding_model}, count={deleted_count}")
        return deleted_count
    
    async def get_vector_count(
        self,
        session: AsyncSession,
        source_type: Optional[VectorSourceType] = None,
    ) -> int:
        """
        获取向量数量
        
        Args:
            session: 数据库会话
            source_type: 过滤来源类型
            
        Returns:
            向量数量
        """
        query = select(func.count(Vector.id))
        if source_type:
            query = query.where(Vector.source_type == source_type)
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度分数
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _euclidean_distance_score(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算欧几里得距离分数（转换为相似度）
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            欧几里得距离分数（越大越相似）
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        # 计算欧几里得距离
        distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
        
        # 转换为相似度分数（距离越小，分数越高）
        # 使用 1 / (1 + distance) 将距离转换为 [0, 1] 范围的相似度
        return 1.0 / (1.0 + distance)
    
    def _dot_product_score(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算点积分数
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            点积分数
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        return sum(a * b for a, b in zip(vec1, vec2))
    
    def _keyword_match_score(self, query: str, content: str) -> float:
        """
        计算关键词匹配分数
        
        Args:
            query: 查询文本
            content: 内容文本
            
        Returns:
            关键词匹配分数
        """
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        # 计算交集比例
        intersection = query_words & content_words
        return len(intersection) / len(query_words)
    
    async def get_vector_by_id(
        self,
        session: AsyncSession,
        vector_id: int,
    ) -> Optional[Vector]:
        """
        根据 ID 获取向量
        
        Args:
            session: 数据库会话
            vector_id: 向量 ID
            
        Returns:
            向量对象，不存在则返回 None
        """
        query = select(Vector).where(Vector.id == vector_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_vectors_by_source(
        self,
        session: AsyncSession,
        source_type: VectorSourceType,
        source_id: int,
    ) -> List[Vector]:
        """
        根据来源获取向量列表
        
        Args:
            session: 数据库会话
            source_type: 来源类型
            source_id: 来源 ID
            
        Returns:
            向量列表
        """
        query = select(Vector).where(
            and_(
                Vector.source_type == source_type,
                Vector.source_id == source_id,
            )
        )
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def update_vector_metadata(
        self,
        session: AsyncSession,
        vector_id: int,
        metadata: dict,
    ) -> Optional[Vector]:
        """
        更新向量元数据
        
        Args:
            session: 数据库会话
            vector_id: 向量 ID
            metadata: 新的元数据
            
        Returns:
            更新后的向量对象，不存在则返回 None
        """
        vector = await self.get_vector_by_id(session, vector_id)
        
        if vector:
            # 合并现有元数据和新元数据
            existing_metadata = {}
            if vector.metadata:
                try:
                    existing_metadata = json.loads(vector.metadata)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            existing_metadata.update(metadata)
            vector.metadata = json.dumps(existing_metadata)
            
            await session.flush()
            logger.debug(f"更新向量元数据: id={vector_id}")
        
        return vector
    
    async def get_stats(
        self,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        获取向量存储统计信息
        
        Args:
            session: 数据库会话
            
        Returns:
            统计信息字典
        """
        # 总向量数
        total_count = await self.get_vector_count(session)
        
        # 按来源类型统计
        from sqlalchemy import distinct
        
        source_stats = {}
        for source_type in VectorSourceType:
            count = await self.get_vector_count(session, source_type)
            if count > 0:
                source_stats[source_type.value] = count
        
        # 按嵌入模型统计
        model_query = select(
            Vector.embedding_model,
            func.count(Vector.id).label("count"),
        ).group_by(Vector.embedding_model)
        
        model_result = await session.execute(model_query)
        model_stats = {row.embedding_model: row.count for row in model_result}
        
        return {
            "total_count": total_count,
            "by_source_type": source_stats,
            "by_embedding_model": model_stats,
            "dimension": self.dimension,
        }


# 创建全局向量服务实例
vector_service = VectorService()
