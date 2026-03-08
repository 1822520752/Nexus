"""
混合检索服务模块
提供 BM25 关键词检索、向量检索和混合检索策略
"""
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.services.embedding.embedding_service import EmbeddingService, embedding_service
from app.services.vector_service import VectorService, VectorSearchResult, vector_service


class DistanceMetric(str, Enum):
    """
    距离度量类型枚举
    
    定义向量相似度计算的距离度量方法
    """
    
    COSINE = "cosine"  # 余弦相似度
    EUCLIDEAN = "euclidean"  # 欧几里得距离
    DOT_PRODUCT = "dot_product"  # 点积


class FusionMethod(str, Enum):
    """
    融合方法枚举
    
    定义混合检索的融合策略
    """
    
    RRF = "rrf"  # Reciprocal Rank Fusion
    WEIGHTED = "weighted"  # 加权融合
    COMBINED = "combined"  # 组合融合


@dataclass
class RetrievalResult:
    """
    检索结果类
    
    封装检索结果的数据
    """
    
    vector_id: int
    content: str
    score: float
    source_type: str
    source_id: int
    metadata: Optional[Dict[str, Any]] = None
    vector_score: float = 0.0  # 向量检索分数
    keyword_score: float = 0.0  # 关键词检索分数
    
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
            "vector_score": self.vector_score,
            "keyword_score": self.keyword_score,
        }


@dataclass
class RetrievalConfig:
    """
    检索配置类
    
    配置检索服务的参数
    """
    
    # Top-K 结果数量
    top_k: int = 10
    
    # 最小相似度分数
    min_score: float = 0.0
    
    # 向量检索权重
    vector_weight: float = 0.7
    
    # 关键词检索权重
    keyword_weight: float = 0.3
    
    # 距离度量方法
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    
    # 融合方法
    fusion_method: FusionMethod = FusionMethod.RRF
    
    # RRF 常数 K
    rrf_k: int = 60
    
    # BM25 参数
    bm25_k1: float = 1.5
    bm25_b: float = 0.75


class BM25Retriever:
    """
    BM25 关键词检索器
    
    实现 BM25 算法进行关键词检索
    """
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        """
        初始化 BM25 检索器
        
        Args:
            k1: BM25 参数 k1，控制词频饱和度
            b: BM25 参数 b，控制文档长度归一化
        """
        self.k1 = k1
        self.b = b
        self._documents: List[Dict[str, Any]] = []
        self._doc_tokens: List[List[str]] = []
        self._doc_lengths: List[int] = []
        self._avg_doc_length: float = 0.0
        self._idf: Dict[str, float] = {}
        self._doc_count: int = 0
    
    def tokenize(self, text: str) -> List[str]:
        """
        文本分词
        
        Args:
            text: 待分词的文本
            
        Returns:
            分词结果列表
        """
        # 简单的分词策略：按空格和标点符号分割
        # 转换为小写
        text = text.lower()
        
        # 使用正则表达式分割
        tokens = re.findall(r'\w+', text)
        
        return tokens
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        索引文档
        
        Args:
            documents: 文档列表，每个文档包含 'id' 和 'content' 字段
        """
        self._documents = documents
        self._doc_count = len(documents)
        
        # 分词并计算文档长度
        self._doc_tokens = []
        self._doc_lengths = []
        
        total_length = 0
        
        for doc in documents:
            tokens = self.tokenize(doc.get("content", ""))
            self._doc_tokens.append(tokens)
            self._doc_lengths.append(len(tokens))
            total_length += len(tokens)
        
        # 计算平均文档长度
        self._avg_doc_length = total_length / self._doc_count if self._doc_count > 0 else 0
        
        # 计算 IDF
        self._compute_idf()
        
        logger.info(f"BM25 索引完成: {self._doc_count} 个文档, 平均长度: {self._avg_doc_length:.2f}")
    
    def _compute_idf(self) -> None:
        """
        计算 IDF（逆文档频率）
        """
        # 统计每个词出现的文档数
        doc_freq: Dict[str, int] = Counter()
        
        for tokens in self._doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1
        
        # 计算 IDF
        self._idf = {}
        for token, df in doc_freq.items():
            # 使用 BM25 IDF 公式
            self._idf[token] = math.log(
                (self._doc_count - df + 0.5) / (df + 0.5) + 1
            )
    
    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            (文档索引, 分数) 列表
        """
        if not self._documents:
            return []
        
        # 分词查询
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        # 计算每个文档的 BM25 分数
        scores = []
        
        for i, doc_tokens in enumerate(self._doc_tokens):
            score = self._compute_bm25_score(
                query_tokens,
                doc_tokens,
                self._doc_lengths[i],
            )
            scores.append((i, score))
        
        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def _compute_bm25_score(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_length: int,
    ) -> float:
        """
        计算 BM25 分数
        
        Args:
            query_tokens: 查询词列表
            doc_tokens: 文档词列表
            doc_length: 文档长度
            
        Returns:
            BM25 分数
        """
        score = 0.0
        
        # 统计文档中每个词的频率
        doc_tf = Counter(doc_tokens)
        
        for token in query_tokens:
            if token not in self._idf:
                continue
            
            # 获取词频
            tf = doc_tf.get(token, 0)
            
            if tf == 0:
                continue
            
            # BM25 公式
            idf = self._idf[token]
            
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * doc_length / self._avg_doc_length
            )
            
            score += idf * numerator / denominator
        
        return score
    
    def get_document(self, index: int) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            index: 文档索引
            
        Returns:
            文档数据
        """
        if 0 <= index < len(self._documents):
            return self._documents[index]
        return None


class HybridRetrieval:
    """
    混合检索类
    
    结合向量检索和关键词检索，提供更准确的检索结果
    """
    
    def __init__(
        self,
        config: Optional[RetrievalConfig] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_service: Optional[VectorService] = None,
    ):
        """
        初始化混合检索服务
        
        Args:
            config: 检索配置
            embedding_service: 嵌入服务实例
            vector_service: 向量服务实例
        """
        self.config = config or RetrievalConfig()
        self.embedding_service = embedding_service or embedding_service
        self.vector_service = vector_service or vector_service
        self._bm25 = BM25Retriever(
            k1=self.config.bm25_k1,
            b=self.config.bm25_b,
        )
        
        logger.info(
            f"初始化混合检索服务: top_k={self.config.top_k}, "
            f"vector_weight={self.config.vector_weight}, "
            f"keyword_weight={self.config.keyword_weight}"
        )
    
    async def search(
        self,
        query: str,
        session,
        source_types: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            session: 数据库会话
            source_types: 来源类型过滤
            top_k: 返回结果数量
            min_score: 最小分数
            
        Returns:
            检索结果列表
        """
        top_k = top_k or self.config.top_k
        min_score = min_score or self.config.min_score
        
        # 生成查询向量
        embedding_result = await self.embedding_service.embed(query)
        query_embedding = embedding_result.embedding
        
        # 执行向量检索
        vector_results = await self._vector_search(
            session=session,
            query_embedding=query_embedding,
            source_types=source_types,
            top_k=top_k * 2,  # 获取更多结果用于融合
        )
        
        # 执行关键词检索
        keyword_results = await self._keyword_search(
            session=session,
            query=query,
            source_types=source_types,
            top_k=top_k * 2,
        )
        
        # 融合结果
        fused_results = self._fuse_results(
            vector_results=vector_results,
            keyword_results=keyword_results,
            top_k=top_k,
        )
        
        # 过滤低分结果
        if min_score > 0:
            fused_results = [r for r in fused_results if r.score >= min_score]
        
        return fused_results
    
    async def _vector_search(
        self,
        session,
        query_embedding: List[float],
        source_types: Optional[List[str]] = None,
        top_k: int = 20,
    ) -> List[VectorSearchResult]:
        """
        执行向量检索
        
        Args:
            session: 数据库会话
            query_embedding: 查询向量
            source_types: 来源类型过滤
            top_k: 返回结果数量
            
        Returns:
            向量检索结果列表
        """
        from app.models.vector import VectorSourceType
        
        # 转换来源类型
        types = None
        if source_types:
            types = [VectorSourceType(t) for t in source_types]
        
        return await self.vector_service.similarity_search(
            session=session,
            query_embedding=query_embedding,
            top_k=top_k,
            source_types=types,
        )
    
    async def _keyword_search(
        self,
        session,
        query: str,
        source_types: Optional[List[str]] = None,
        top_k: int = 20,
    ) -> List[VectorSearchResult]:
        """
        执行关键词检索
        
        Args:
            session: 数据库会话
            query: 查询文本
            source_types: 来源类型过滤
            top_k: 返回结果数量
            
        Returns:
            关键词检索结果列表
        """
        from sqlalchemy import or_, select, func
        from app.models.vector import Vector, VectorSourceType
        
        # 构建查询
        db_query = select(Vector)
        
        # 添加来源类型过滤
        if source_types:
            types = [VectorSourceType(t) for t in source_types]
            db_query = db_query.where(Vector.source_type.in_(types))
        
        # 关键词搜索条件
        keywords = self._bm25.tokenize(query)
        if keywords:
            keyword_conditions = [
                func.lower(Vector.content).contains(keyword)
                for keyword in keywords[:5]  # 限制关键词数量
            ]
            db_query = db_query.where(or_(*keyword_conditions))
        
        # 执行查询
        result = await session.execute(db_query.limit(top_k * 2))
        vectors = result.scalars().all()
        
        # 构建文档列表用于 BM25
        documents = [
            {
                "id": v.id,
                "content": v.content,
                "source_type": v.source_type.value,
                "source_id": v.source_id,
                "metadata": v.metadata,
            }
            for v in vectors
        ]
        
        # 索引并搜索
        self._bm25.index_documents(documents)
        bm25_results = self._bm25.search(query, top_k=top_k)
        
        # 转换结果
        results = []
        for idx, score in bm25_results:
            doc = self._bm25.get_document(idx)
            if doc:
                # 归一化分数到 [0, 1]
                normalized_score = 1.0 / (1.0 + math.exp(-score / 10))
                
                results.append(VectorSearchResult(
                    vector_id=doc["id"],
                    content=doc["content"],
                    score=normalized_score,
                    source_type=doc["source_type"],
                    source_id=doc["source_id"],
                    metadata=doc.get("metadata"),
                ))
        
        return results
    
    def _fuse_results(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[VectorSearchResult],
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        融合向量检索和关键词检索结果
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回结果数量
            
        Returns:
            融合后的检索结果列表
        """
        if self.config.fusion_method == FusionMethod.RRF:
            return self._rrf_fusion(vector_results, keyword_results, top_k)
        elif self.config.fusion_method == FusionMethod.WEIGHTED:
            return self._weighted_fusion(vector_results, keyword_results, top_k)
        else:
            return self._combined_fusion(vector_results, keyword_results, top_k)
    
    def _rrf_fusion(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[VectorSearchResult],
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion 融合
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回结果数量
            
        Returns:
            融合后的检索结果列表
        """
        k = self.config.rrf_k
        
        # 计算每个文档的 RRF 分数
        rrf_scores: Dict[int, Dict[str, Any]] = {}
        
        # 向量检索结果
        for rank, result in enumerate(vector_results, 1):
            vid = result.vector_id
            if vid not in rrf_scores:
                rrf_scores[vid] = {
                    "result": result,
                    "vector_rank": rank,
                    "keyword_rank": float('inf'),
                }
            else:
                rrf_scores[vid]["vector_rank"] = rank
        
        # 关键词检索结果
        for rank, result in enumerate(keyword_results, 1):
            vid = result.vector_id
            if vid not in rrf_scores:
                rrf_scores[vid] = {
                    "result": result,
                    "vector_rank": float('inf'),
                    "keyword_rank": rank,
                }
            else:
                rrf_scores[vid]["keyword_rank"] = rank
        
        # 计算 RRF 分数
        fused_results = []
        for vid, data in rrf_scores.items():
            result = data["result"]
            vector_rank = data["vector_rank"]
            keyword_rank = data["keyword_rank"]
            
            # RRF 公式
            rrf_score = 0.0
            if vector_rank != float('inf'):
                rrf_score += 1.0 / (k + vector_rank)
            if keyword_rank != float('inf'):
                rrf_score += 1.0 / (k + keyword_rank)
            
            # 获取原始分数
            vector_score = 0.0
            keyword_score = 0.0
            
            if vector_rank != float('inf') and vector_rank <= len(vector_results):
                vector_score = vector_results[vector_rank - 1].score
            if keyword_rank != float('inf') and keyword_rank <= len(keyword_results):
                keyword_score = keyword_results[keyword_rank - 1].score
            
            fused_results.append(RetrievalResult(
                vector_id=vid,
                content=result.content,
                score=rrf_score,
                source_type=result.source_type,
                source_id=result.source_id,
                metadata=result.metadata,
                vector_score=vector_score,
                keyword_score=keyword_score,
            ))
        
        # 按分数排序
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results[:top_k]
    
    def _weighted_fusion(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[VectorSearchResult],
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        加权融合
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回结果数量
            
        Returns:
            融合后的检索结果列表
        """
        vector_weight = self.config.vector_weight
        keyword_weight = self.config.keyword_weight
        
        # 合并结果
        merged: Dict[int, Dict[str, Any]] = {}
        
        # 向量检索结果
        for result in vector_results:
            vid = result.vector_id
            merged[vid] = {
                "result": result,
                "vector_score": result.score,
                "keyword_score": 0.0,
            }
        
        # 关键词检索结果
        for result in keyword_results:
            vid = result.vector_id
            if vid in merged:
                merged[vid]["keyword_score"] = result.score
            else:
                merged[vid] = {
                    "result": result,
                    "vector_score": 0.0,
                    "keyword_score": result.score,
                }
        
        # 计算加权分数
        fused_results = []
        for vid, data in merged.items():
            result = data["result"]
            vector_score = data["vector_score"]
            keyword_score = data["keyword_score"]
            
            weighted_score = (
                vector_weight * vector_score +
                keyword_weight * keyword_score
            )
            
            fused_results.append(RetrievalResult(
                vector_id=vid,
                content=result.content,
                score=weighted_score,
                source_type=result.source_type,
                source_id=result.source_id,
                metadata=result.metadata,
                vector_score=vector_score,
                keyword_score=keyword_score,
            ))
        
        # 按分数排序
        fused_results.sort(key=lambda x: x.score, reverse=True)
        
        return fused_results[:top_k]
    
    def _combined_fusion(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[VectorSearchResult],
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        组合融合（RRF + 加权）
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回结果数量
            
        Returns:
            融合后的检索结果列表
        """
        # 先进行 RRF 融合
        rrf_results = self._rrf_fusion(vector_results, keyword_results, top_k * 2)
        
        # 再进行加权调整
        vector_weight = self.config.vector_weight
        keyword_weight = self.config.keyword_weight
        
        for result in rrf_results:
            # 根据原始分数调整 RRF 分数
            adjustment = (
                vector_weight * result.vector_score +
                keyword_weight * result.keyword_score
            )
            result.score = result.score * 0.5 + adjustment * 0.5
        
        # 重新排序
        rrf_results.sort(key=lambda x: x.score, reverse=True)
        
        return rrf_results[:top_k]
    
    async def vector_only_search(
        self,
        query: str,
        session,
        source_types: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        distance_metric: Optional[DistanceMetric] = None,
    ) -> List[RetrievalResult]:
        """
        仅使用向量检索
        
        Args:
            query: 查询文本
            session: 数据库会话
            source_types: 来源类型过滤
            top_k: 返回结果数量
            distance_metric: 距离度量方法
            
        Returns:
            检索结果列表
        """
        top_k = top_k or self.config.top_k
        
        # 生成查询向量
        embedding_result = await self.embedding_service.embed(query)
        query_embedding = embedding_result.embedding
        
        # 执行向量检索
        vector_results = await self._vector_search(
            session=session,
            query_embedding=query_embedding,
            source_types=source_types,
            top_k=top_k,
        )
        
        # 转换结果
        results = []
        for vr in vector_results:
            results.append(RetrievalResult(
                vector_id=vr.vector_id,
                content=vr.content,
                score=vr.score,
                source_type=vr.source_type,
                source_id=vr.source_id,
                metadata=vr.metadata,
                vector_score=vr.score,
                keyword_score=0.0,
            ))
        
        return results
    
    async def keyword_only_search(
        self,
        query: str,
        session,
        source_types: Optional[List[str]] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        仅使用关键词检索
        
        Args:
            query: 查询文本
            session: 数据库会话
            source_types: 来源类型过滤
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        top_k = top_k or self.config.top_k
        
        # 执行关键词检索
        keyword_results = await self._keyword_search(
            session=session,
            query=query,
            source_types=source_types,
            top_k=top_k,
        )
        
        # 转换结果
        results = []
        for kr in keyword_results:
            results.append(RetrievalResult(
                vector_id=kr.vector_id,
                content=kr.content,
                score=kr.score,
                source_type=kr.source_type,
                source_id=kr.source_id,
                metadata=kr.metadata,
                vector_score=0.0,
                keyword_score=kr.score,
            ))
        
        return results


# 创建全局混合检索服务实例
hybrid_retrieval = HybridRetrieval()
