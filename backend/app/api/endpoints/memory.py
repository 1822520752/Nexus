"""
记忆管理 API 端点
提供记忆的 CRUD 操作和检索接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.memory import Memory, MemoryType
from app.schemas.memory import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryStats,
    MemoryUpdate,
)
from app.services.memory import (
    get_memory_service,
    MemoryCategory,
    MemoryService,
)

router = APIRouter()


# ==================== 数据库操作端点 ====================


@router.get("/", response_model=dict)
async def list_memories(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    memory_type: Optional[MemoryType] = Query(None, description="记忆类型过滤"),
    min_importance: Optional[float] = Query(None, ge=0, le=1, description="最小重要性"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取记忆列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        memory_type: 记忆类型过滤
        min_importance: 最小重要性过滤
        db: 数据库会话
    
    Returns:
        记忆列表和总数
    """
    # 构建查询
    query = select(Memory)
    count_query = select(func.count(Memory.id))
    
    # 应用过滤条件
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
        count_query = count_query.where(Memory.memory_type == memory_type)
    
    if min_importance is not None:
        query = query.where(Memory.importance >= min_importance)
        count_query = count_query.where(Memory.importance >= min_importance)
    
    # 查询总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 查询列表
    query = query.order_by(Memory.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    memories = result.scalars().all()
    
    return {
        "items": [MemoryResponse.model_validate(m) for m in memories],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    db: AsyncSession = Depends(get_db),
) -> MemoryStats:
    """
    获取记忆统计信息
    
    Args:
        db: 数据库会话
    
    Returns:
        记忆统计信息
    """
    # 查询各类型数量
    instant_count_query = select(func.count(Memory.id)).where(
        Memory.memory_type == MemoryType.INSTANT
    )
    working_count_query = select(func.count(Memory.id)).where(
        Memory.memory_type == MemoryType.WORKING
    )
    long_term_count_query = select(func.count(Memory.id)).where(
        Memory.memory_type == MemoryType.LONG_TERM
    )
    
    # 查询平均重要性
    avg_importance_query = select(func.avg(Memory.importance))
    
    # 查询总访问次数
    total_access_query = select(func.sum(Memory.access_count))
    
    # 执行查询
    instant_result = await db.execute(instant_count_query)
    instant_count = instant_result.scalar() or 0
    
    working_result = await db.execute(working_count_query)
    working_count = working_result.scalar() or 0
    
    long_term_result = await db.execute(long_term_count_query)
    long_term_count = long_term_result.scalar() or 0
    
    avg_result = await db.execute(avg_importance_query)
    avg_importance = avg_result.scalar() or 0.0
    
    access_result = await db.execute(total_access_query)
    total_access = access_result.scalar() or 0
    
    return MemoryStats(
        total_count=instant_count + working_count + long_term_count,
        instant_count=instant_count,
        working_count=working_count,
        long_term_count=long_term_count,
        avg_importance=float(avg_importance),
        total_access_count=int(total_access),
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
) -> Memory:
    """
    获取单个记忆详情
    
    Args:
        memory_id: 记忆 ID
        db: 数据库会话
    
    Returns:
        记忆详情
    
    Raises:
        HTTPException: 记忆不存在时抛出 404
    """
    query = select(Memory).where(Memory.id == memory_id)
    result = await db.execute(query)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记忆 {memory_id} 不存在",
        )
    
    # 增加访问计数
    memory.increment_access()
    await db.commit()
    await db.refresh(memory)
    
    return memory


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory_data: MemoryCreate,
    db: AsyncSession = Depends(get_db),
) -> Memory:
    """
    创建新记忆
    
    Args:
        memory_data: 记忆创建数据
        db: 数据库会话
    
    Returns:
        创建的记忆
    """
    import json
    from datetime import datetime
    
    memory = Memory(
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        importance=memory_data.importance,
        source_type=memory_data.source_type,
        source_id=memory_data.source_id,
        tags=json.dumps(memory_data.tags, ensure_ascii=False) if memory_data.tags else None,
        metadata=json.dumps(memory_data.metadata, ensure_ascii=False) if memory_data.metadata else None,
        expires_at=memory_data.expires_at,
        last_accessed_at=datetime.utcnow().isoformat(),
    )
    
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    
    return memory


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    memory_data: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> Memory:
    """
    更新记忆
    
    Args:
        memory_id: 记忆 ID
        memory_data: 更新数据
        db: 数据库会话
    
    Returns:
        更新后的记忆
    
    Raises:
        HTTPException: 记忆不存在时抛出 404
    """
    import json
    
    query = select(Memory).where(Memory.id == memory_id)
    result = await db.execute(query)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记忆 {memory_id} 不存在",
        )
    
    # 更新字段
    if memory_data.content is not None:
        memory.content = memory_data.content
    
    if memory_data.importance is not None:
        memory.importance = memory_data.importance
    
    if memory_data.memory_type is not None:
        memory.memory_type = memory_data.memory_type
    
    if memory_data.tags is not None:
        memory.tags = json.dumps(memory_data.tags, ensure_ascii=False)
    
    if memory_data.metadata is not None:
        memory.metadata = json.dumps(memory_data.metadata, ensure_ascii=False)
    
    await db.commit()
    await db.refresh(memory)
    
    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    删除记忆
    
    Args:
        memory_id: 记忆 ID
        db: 数据库会话
    
    Raises:
        HTTPException: 记忆不存在时抛出 404
    """
    query = select(Memory).where(Memory.id == memory_id)
    result = await db.execute(query)
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记忆 {memory_id} 不存在",
        )
    
    await db.delete(memory)
    await db.commit()


@router.post("/search", response_model=List[MemorySearchResult])
async def search_memories(
    search_request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
) -> List[MemorySearchResult]:
    """
    搜索记忆
    
    Args:
        search_request: 搜索请求
        db: 数据库会话
    
    Returns:
        搜索结果列表
    """
    import json
    
    # 构建查询
    query = select(Memory)
    
    # 应用过滤条件
    if search_request.memory_types:
        query = query.where(Memory.memory_type.in_(search_request.memory_types))
    
    if search_request.min_importance is not None:
        query = query.where(Memory.importance >= search_request.min_importance)
    
    # 全文搜索（简单实现，实际应使用向量搜索）
    search_term = f"%{search_request.query}%"
    query = query.where(Memory.content.ilike(search_term))
    
    # 排序和限制
    query = query.order_by(Memory.importance.desc()).limit(search_request.top_k)
    
    result = await db.execute(query)
    memories = result.scalars().all()
    
    # 构建结果
    results = []
    for memory in memories:
        # 计算简单的相似度分数
        score = _calculate_simple_score(memory, search_request.query)
        
        # 解析 tags 和 metadata
        tags = None
        if memory.tags:
            try:
                tags = json.loads(memory.tags)
            except (json.JSONDecodeError, TypeError):
                pass
        
        metadata = None
        if memory.metadata:
            try:
                metadata = json.loads(memory.metadata)
            except (json.JSONDecodeError, TypeError):
                pass
        
        results.append(MemorySearchResult(
            memory_id=memory.id,
            content=memory.content,
            memory_type=memory.memory_type,
            importance=memory.importance,
            score=score,
            tags=tags,
            metadata=metadata,
        ))
    
    return results


def _calculate_simple_score(memory: Memory, query: str) -> float:
    """
    计算简单的匹配分数
    
    Args:
        memory: 记忆对象
        query: 查询字符串
    
    Returns:
        匹配分数（0-1）
    """
    query_lower = query.lower()
    content_lower = memory.content.lower()
    
    # 完全匹配
    if query_lower == content_lower:
        return 1.0
    
    # 包含匹配
    if query_lower in content_lower:
        # 根据匹配位置和长度计算分数
        position = content_lower.index(query_lower)
        length_ratio = len(query_lower) / len(content_lower)
        return 0.5 + (0.5 * length_ratio) - (position / len(content_lower) * 0.2)
    
    # 部分匹配（单词级别）
    query_words = set(query_lower.split())
    content_words = set(content_lower.split())
    common_words = query_words.intersection(content_words)
    
    if common_words:
        return len(common_words) / len(query_words) * 0.5
    
    return 0.0


# ==================== 记忆服务端点 ====================


@router.post("/service/search", response_model=List[dict])
async def search_memory_service(
    query: str = Query(..., description="搜索关键词"),
    top_k: int = Query(10, ge=1, le=100, description="返回结果数量"),
    include_working: bool = Query(True, description="是否包含工作记忆"),
    include_long_term: bool = Query(True, description="是否包含长期记忆"),
) -> List[dict]:
    """
    使用记忆服务进行跨层检索
    
    从工作记忆和长期记忆中检索相关信息
    
    Args:
        query: 搜索关键词
        top_k: 返回结果数量
        include_working: 是否包含工作记忆
        include_long_term: 是否包含长期记忆
    
    Returns:
        检索结果列表
    """
    memory_service = get_memory_service()
    
    return await memory_service.retrieve_relevant_memories(
        query=query,
        top_k=top_k,
        include_working=include_working,
        include_long_term=include_long_term,
    )


@router.get("/service/stats", response_model=dict)
async def get_memory_service_stats() -> dict:
    """
    获取记忆服务的综合统计信息
    
    Returns:
        综合统计信息
    """
    memory_service = get_memory_service()
    return await memory_service.get_all_stats()


@router.post("/service/consolidate", response_model=dict)
async def consolidate_memories() -> dict:
    """
    执行记忆巩固
    
    将高重要性的记忆进行巩固，提高其保留率
    
    Returns:
        巩固结果统计
    """
    memory_service = get_memory_service()
    return await memory_service.consolidate_memories()


@router.post("/service/reinforce/{memory_id}", response_model=dict)
async def reinforce_memory(
    memory_id: int,
    memory_type: str = Query("long_term", description="记忆类型：working 或 long_term"),
) -> dict:
    """
    强化记忆
    
    通过访问或引用来强化记忆，提高其保留率
    
    Args:
        memory_id: 记忆 ID
        memory_type: 记忆类型
    
    Returns:
        操作结果
    """
    memory_service = get_memory_service()
    
    success = await memory_service.reinforce_memory(memory_id, memory_type)
    
    return {
        "success": success,
        "memory_id": memory_id,
        "memory_type": memory_type,
    }


@router.post("/service/session", response_model=dict)
async def set_session(
    session_id: str = Query(..., description="会话 ID"),
    conversation_id: Optional[str] = Query(None, description="对话 ID"),
) -> dict:
    """
    设置当前会话
    
    Args:
        session_id: 会话 ID
        conversation_id: 对话 ID（可选）
    
    Returns:
        操作结果
    """
    memory_service = get_memory_service()
    memory_service.set_session(session_id, conversation_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "conversation_id": conversation_id or session_id,
    }


@router.post("/service/save", response_model=dict)
async def save_memory_state() -> dict:
    """
    保存记忆状态到文件
    
    Returns:
        操作结果
    """
    memory_service = get_memory_service()
    await memory_service.save_state()
    
    return {"success": True, "message": "记忆状态已保存"}


@router.post("/service/load", response_model=dict)
async def load_memory_state() -> dict:
    """
    从文件加载记忆状态
    
    Returns:
        操作结果
    """
    memory_service = get_memory_service()
    await memory_service.load_state()
    
    return {"success": True, "message": "记忆状态已加载"}


@router.delete("/service/clear", response_model=dict)
async def clear_all_memories() -> dict:
    """
    清空所有记忆（危险操作）
    
    Returns:
        操作结果
    """
    memory_service = get_memory_service()
    await memory_service.clear_all()
    
    return {"success": True, "message": "所有记忆已清空"}
