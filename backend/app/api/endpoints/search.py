"""
搜索 API 端点
提供相似度搜索、混合搜索和嵌入生成接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.vector import VectorSourceType
from app.services.embedding.embedding_service import (
    EmbeddingModelType,
    EmbeddingService,
    embedding_service,
)
from app.services.retrieval.hybrid_retrieval import (
    DistanceMetric,
    FusionMethod,
    HybridRetrieval,
    RetrievalConfig,
    RetrievalResult,
    hybrid_retrieval,
)
from app.services.vector_service import VectorService, vector_service


# 创建路由器
router = APIRouter(prefix="/search", tags=["搜索服务"])


# ==================== 请求/响应模型 ====================

class EmbedRequest(BaseModel):
    """
    嵌入生成请求模型
    """
    
    text: str = Field(..., description="待向量化的文本")
    model_type: Optional[str] = Field(
        default="text-embedding-ada-002",
        description="嵌入模型类型",
    )


class EmbedBatchRequest(BaseModel):
    """
    批量嵌入生成请求模型
    """
    
    texts: List[str] = Field(..., description="待向量化的文本列表")
    model_type: Optional[str] = Field(
        default="text-embedding-ada-002",
        description="嵌入模型类型",
    )


class EmbedResponse(BaseModel):
    """
    嵌入生成响应模型
    """
    
    embedding: List[float] = Field(..., description="嵌入向量")
    model: str = Field(..., description="使用的模型名称")
    dimension: int = Field(..., description="向量维度")
    tokens_used: int = Field(default=0, description="使用的 Token 数量")
    cached: bool = Field(default=False, description="是否来自缓存")


class EmbedBatchResponse(BaseModel):
    """
    批量嵌入生成响应模型
    """
    
    embeddings: List[List[float]] = Field(..., description="嵌入向量列表")
    model: str = Field(..., description="使用的模型名称")
    dimension: int = Field(..., description="向量维度")
    total_tokens: int = Field(default=0, description="总 Token 数量")
    cached_count: int = Field(default=0, description="缓存命中数量")


class SimilarSearchRequest(BaseModel):
    """
    相似度搜索请求模型
    """
    
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="最小相似度分数")
    source_types: Optional[List[str]] = Field(default=None, description="来源类型过滤")
    distance_metric: str = Field(default="cosine", description="距离度量方法")
    model_type: Optional[str] = Field(
        default="text-embedding-ada-002",
        description="嵌入模型类型",
    )


class SearchResultItem(BaseModel):
    """
    搜索结果项模型
    """
    
    vector_id: int = Field(..., description="向量 ID")
    content: str = Field(..., description="文本内容")
    score: float = Field(..., description="相似度分数")
    source_type: str = Field(..., description="来源类型")
    source_id: int = Field(..., description="来源 ID")
    metadata: Optional[dict] = Field(default=None, description="元数据")
    vector_score: float = Field(default=0.0, description="向量检索分数")
    keyword_score: float = Field(default=0.0, description="关键词检索分数")


class SearchResponse(BaseModel):
    """
    搜索响应模型
    """
    
    results: List[SearchResultItem] = Field(..., description="搜索结果列表")
    total: int = Field(..., description="结果总数")
    query: str = Field(..., description="查询文本")
    model: str = Field(..., description="使用的嵌入模型")


class HybridSearchRequest(BaseModel):
    """
    混合搜索请求模型
    """
    
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="最小分数")
    source_types: Optional[List[str]] = Field(default=None, description="来源类型过滤")
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="向量检索权重")
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="关键词检索权重")
    fusion_method: str = Field(default="rrf", description="融合方法")
    model_type: Optional[str] = Field(
        default="text-embedding-ada-002",
        description="嵌入模型类型",
    )


class VectorStatsResponse(BaseModel):
    """
    向量统计响应模型
    """
    
    total_count: int = Field(..., description="总向量数")
    by_source_type: dict = Field(..., description="按来源类型统计")
    by_embedding_model: dict = Field(..., description="按嵌入模型统计")
    dimension: int = Field(..., description="向量维度")


# ==================== API 端点 ====================

@router.post(
    "/embed",
    response_model=EmbedResponse,
    summary="生成嵌入向量",
    description="将文本转换为向量表示",
)
async def create_embedding(
    request: EmbedRequest,
    db: AsyncSession = Depends(get_db),
) -> EmbedResponse:
    """
    生成嵌入向量
    
    Args:
        request: 嵌入请求
        db: 数据库会话
        
    Returns:
        嵌入响应
    """
    try:
        # 解析模型类型
        model_type = None
        if request.model_type:
            try:
                model_type = EmbeddingModelType(request.model_type)
            except ValueError:
                pass
        
        # 生成嵌入
        result = await embedding_service.embed(
            text=request.text,
            model_type=model_type,
        )
        
        return EmbedResponse(
            embedding=result.embedding,
            model=result.model,
            dimension=result.dimension,
            tokens_used=result.tokens_used,
            cached=result.cached,
        )
        
    except Exception as e:
        logger.error(f"生成嵌入失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成嵌入失败: {str(e)}",
        )


@router.post(
    "/embed/batch",
    response_model=EmbedBatchResponse,
    summary="批量生成嵌入向量",
    description="批量将文本转换为向量表示",
)
async def create_embeddings_batch(
    request: EmbedBatchRequest,
    db: AsyncSession = Depends(get_db),
) -> EmbedBatchResponse:
    """
    批量生成嵌入向量
    
    Args:
        request: 批量嵌入请求
        db: 数据库会话
        
    Returns:
        批量嵌入响应
    """
    if not request.texts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文本列表不能为空",
        )
    
    try:
        # 解析模型类型
        model_type = None
        if request.model_type:
            try:
                model_type = EmbeddingModelType(request.model_type)
            except ValueError:
                pass
        
        # 批量生成嵌入
        results = await embedding_service.embed_batch(
            texts=request.texts,
            model_type=model_type,
        )
        
        # 统计信息
        total_tokens = sum(r.tokens_used for r in results)
        cached_count = sum(1 for r in results if r.cached)
        
        return EmbedBatchResponse(
            embeddings=[r.embedding for r in results],
            model=results[0].model if results else request.model_type,
            dimension=results[0].dimension if results else 0,
            total_tokens=total_tokens,
            cached_count=cached_count,
        )
        
    except Exception as e:
        logger.error(f"批量生成嵌入失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量生成嵌入失败: {str(e)}",
        )


@router.post(
    "/similar",
    response_model=SearchResponse,
    summary="相似度搜索",
    description="使用向量相似度进行搜索",
)
async def similarity_search(
    request: SimilarSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    相似度搜索
    
    Args:
        request: 搜索请求
        db: 数据库会话
        
    Returns:
        搜索响应
    """
    try:
        # 解析模型类型
        model_type = None
        if request.model_type:
            try:
                model_type = EmbeddingModelType(request.model_type)
            except ValueError:
                pass
        
        # 生成查询向量
        embedding_result = await embedding_service.embed(
            text=request.query,
            model_type=model_type,
        )
        
        # 解析来源类型
        source_types = None
        if request.source_types:
            source_types = []
            for st in request.source_types:
                try:
                    source_types.append(VectorSourceType(st))
                except ValueError:
                    pass
        
        # 解析距离度量
        try:
            distance_metric = DistanceMetric(request.distance_metric)
        except ValueError:
            distance_metric = DistanceMetric.COSINE
        
        # 执行搜索
        results = await vector_service.similarity_search(
            session=db,
            query_embedding=embedding_result.embedding,
            top_k=request.top_k,
            source_types=source_types,
            min_score=request.min_score,
            distance_metric=distance_metric,
        )
        
        # 转换结果
        search_results = [
            SearchResultItem(
                vector_id=r.vector_id,
                content=r.content,
                score=r.score,
                source_type=r.source_type,
                source_id=r.source_id,
                metadata=r.metadata,
            )
            for r in results
        ]
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            model=embedding_result.model,
        )
        
    except Exception as e:
        logger.error(f"相似度搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"相似度搜索失败: {str(e)}",
        )


@router.post(
    "/hybrid",
    response_model=SearchResponse,
    summary="混合搜索",
    description="结合向量检索和关键词检索进行搜索",
)
async def hybrid_search(
    request: HybridSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    混合搜索
    
    Args:
        request: 混合搜索请求
        db: 数据库会话
        
    Returns:
        搜索响应
    """
    try:
        # 配置检索参数
        config = RetrievalConfig(
            top_k=request.top_k,
            min_score=request.min_score,
            vector_weight=request.vector_weight,
            keyword_weight=request.keyword_weight,
        )
        
        # 解析融合方法
        try:
            config.fusion_method = FusionMethod(request.fusion_method)
        except ValueError:
            config.fusion_method = FusionMethod.RRF
        
        # 创建混合检索实例
        retrieval = HybridRetrieval(config=config)
        
        # 执行搜索
        results = await retrieval.search(
            query=request.query,
            session=db,
            source_types=request.source_types,
            top_k=request.top_k,
            min_score=request.min_score,
        )
        
        # 转换结果
        search_results = [
            SearchResultItem(
                vector_id=r.vector_id,
                content=r.content,
                score=r.score,
                source_type=r.source_type,
                source_id=r.source_id,
                metadata=r.metadata,
                vector_score=r.vector_score,
                keyword_score=r.keyword_score,
            )
            for r in results
        ]
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            model=embedding_service.config.model_type.value,
        )
        
    except Exception as e:
        logger.error(f"混合搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"混合搜索失败: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=VectorStatsResponse,
    summary="获取向量统计",
    description="获取向量存储的统计信息",
)
async def get_vector_stats(
    db: AsyncSession = Depends(get_db),
) -> VectorStatsResponse:
    """
    获取向量统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        向量统计响应
    """
    try:
        stats = await vector_service.get_stats(db)
        
        return VectorStatsResponse(
            total_count=stats["total_count"],
            by_source_type=stats["by_source_type"],
            by_embedding_model=stats["by_embedding_model"],
            dimension=stats["dimension"],
        )
        
    except Exception as e:
        logger.error(f"获取向量统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取向量统计失败: {str(e)}",
        )


@router.get(
    "/cache/stats",
    summary="获取嵌入缓存统计",
    description="获取嵌入缓存的统计信息",
)
async def get_cache_stats() -> dict:
    """
    获取嵌入缓存统计信息
    
    Returns:
        缓存统计信息
    """
    stats = embedding_service.get_cache_stats()
    
    if stats is None:
        return {
            "enabled": False,
            "message": "缓存未启用",
        }
    
    return {
        "enabled": True,
        "size": stats["size"],
        "max_size": stats["max_size"],
    }


@router.delete(
    "/cache",
    summary="清空嵌入缓存",
    description="清空嵌入缓存",
)
async def clear_cache() -> dict:
    """
    清空嵌入缓存
    
    Returns:
        操作结果
    """
    embedding_service.clear_cache()
    
    return {
        "success": True,
        "message": "嵌入缓存已清空",
    }
