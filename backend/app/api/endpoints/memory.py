"""
记忆管理 API 端点
提供记忆的 CRUD 操作和检索接口
统一使用 MemoryService 进行记忆管理
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.services.memory import MemoryService

router = APIRouter()


# ==================== 记忆列表和详情 ====================


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
    from sqlalchemy import func, select
    
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
    
    # 只显示活跃的记忆
    query = query.where(Memory.status == "active")
    count_query = count_query.where(Memory.status == "active")
    
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
    from sqlalchemy import func, select
    
    # 查询各类型数量
    instant_count_query = select(func.count(Memory.id)).where(
        Memory.memory_type == MemoryType.INSTANT,
        Memory.status == "active",
    )
    working_count_query = select(func.count(Memory.id)).where(
        Memory.memory_type == MemoryType.WORKING,
        Memory.status == "active",
    )
    long_term_count_query = select(func.count(Memory.id)).where(
        Memory.memory_type == MemoryType.LONG_TERM,
        Memory.status == "active",
    )
    
    # 查询平均重要性
    avg_importance_query = select(func.avg(Memory.importance)).where(
        Memory.status == "active"
    )
    
    # 查询总访问次数
    total_access_query = select(func.sum(Memory.access_count)).where(
        Memory.status == "active"
    )
    
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
    from sqlalchemy import select
    
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


# ==================== 记忆 CRUD 操作 ====================


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
    memory_service = MemoryService(db)
    
    # 根据记忆类型选择不同的创建方法
    if memory_data.memory_type == MemoryType.WORKING:
        memory = await memory_service.add_to_working_memory(
            content=memory_data.content,
            source_type=memory_data.source_type,
            source_id=memory_data.source_id,
            tags=memory_data.tags,
            metadata=memory_data.metadata,
        )
    elif memory_data.memory_type == MemoryType.LONG_TERM:
        memory = await memory_service.add_to_long_term_memory(
            content=memory_data.content,
            category=memory_data.metadata.get("category", "fact") if memory_data.metadata else "fact",
            tags=memory_data.tags,
            metadata=memory_data.metadata,
        )
    else:
        # 即时记忆
        memory = await memory_service.add_instant_memory(
            role=memory_data.metadata.get("role", "user") if memory_data.metadata else "user",
            content=memory_data.content,
            metadata=memory_data.metadata,
        )
    
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
    from sqlalchemy import select
    
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
        memory.tags = memory_data.tags
    
    if memory_data.metadata is not None:
        memory.metadata = memory_data.metadata
    
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
    from sqlalchemy import select
    
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


# ==================== 记忆搜索 ====================


@router.post("/search", response_model=List[MemorySearchResult])
async def search_memories(
    search_request: MemorySearchRequest,
    db: AsyncSession = Depends(get_db),
) -> List[MemorySearchResult]:
    """
    搜索记忆（支持跨层检索）
    
    Args:
        search_request: 搜索请求
        db: 数据库会话
    
    Returns:
        搜索结果列表
    """
    memory_service = MemoryService(db)
    
    # 使用跨层检索
    results = await memory_service.retrieve_relevant_memories(
        query=search_request.query,
        top_k=search_request.top_k,
        include_working=not search_request.memory_types or MemoryType.WORKING in search_request.memory_types,
        include_long_term=not search_request.memory_types or MemoryType.LONG_TERM in search_request.memory_types,
    )
    
    # 转换为搜索结果格式
    search_results = []
    for result in results:
        memory_type = MemoryType.WORKING if result["source"] == "working_memory" else MemoryType.LONG_TERM
        
        search_results.append(MemorySearchResult(
            memory_id=result["id"],
            content=result["content"],
            memory_type=memory_type,
            importance=result["importance"],
            score=result["importance"],  # 使用重要性作为分数
            tags=result.get("tags", []),
            metadata={"category": result.get("category")},
        ))
    
    return search_results


# ==================== 记忆服务功能 ====================


@router.post("/consolidate", response_model=dict)
async def consolidate_memories(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    执行记忆巩固
    
    将高重要性的记忆进行巩固，提高其保留率
    
    Returns:
        巩固结果统计
    """
    memory_service = MemoryService(db)
    return await memory_service.consolidate_memories()


@router.post("/reinforce/{memory_id}", response_model=dict)
async def reinforce_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    强化记忆
    
    通过访问或引用来强化记忆，提高其保留率
    
    Args:
        memory_id: 记忆 ID
    
    Returns:
        操作结果
    """
    memory_service = MemoryService(db)
    
    success = await memory_service.reinforce_memory(memory_id)
    
    return {
        "success": success,
        "memory_id": memory_id,
    }


@router.post("/session", response_model=dict)
async def set_session(
    session_id: str = Query(..., description="会话 ID"),
    conversation_id: Optional[str] = Query(None, description="对话 ID"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    设置当前会话
    
    Args:
        session_id: 会话 ID
        conversation_id: 对话 ID（可选）
    
    Returns:
        操作结果
    """
    memory_service = MemoryService(db)
    memory_service.set_session(session_id, conversation_id)
    
    return {
        "success": True,
        "session_id": session_id,
        "conversation_id": conversation_id or session_id,
    }


@router.get("/context", response_model=dict)
async def get_context(
    query: str = Query(..., description="当前查询"),
    conversation_id: Optional[str] = Query(None, description="对话 ID"),
    max_memories: int = Query(5, ge=1, le=20, description="最大记忆数量"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取包含相关记忆的完整上下文
    
    整合瞬时记忆和相关记忆，用于 LLM 推理
    
    Args:
        query: 当前查询
        conversation_id: 对话 ID
        max_memories: 最大记忆数量
    
    Returns:
        包含上下文和记忆的字典
    """
    memory_service = MemoryService(db)
    return await memory_service.get_context_with_memories(
        query=query,
        conversation_id=conversation_id,
        max_memories=max_memories,
    )


@router.get("/service/stats", response_model=dict)
async def get_memory_service_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取记忆服务的综合统计信息
    
    Returns:
        综合统计信息
    """
    memory_service = MemoryService(db)
    return await memory_service.get_all_stats()


@router.delete("/clear", response_model=dict)
async def clear_all_memories(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    清空所有记忆（危险操作）
    
    Returns:
        操作结果
    """
    memory_service = MemoryService(db)
    await memory_service.clear_all()
    
    return {"success": True, "message": "所有记忆已清空"}
