"""
对话管理 API 端点
提供对话的 CRUD 操作接口
"""
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    ConversationListResponse,
    MessageResponse,
)

router = APIRouter()


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    获取对话列表
    
    Args:
        skip: 跳过的记录数
        limit: 返回的记录数
        db: 数据库会话
    
    Returns:
        对话列表
    """
    # 查询总数
    count_query = select(Conversation)
    total_result = await db.execute(count_query)
    total = len(total_result.all())
    
    # 查询列表
    query = select(Conversation).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
    )


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """
    创建新对话
    
    Args:
        conversation_data: 对话创建数据
        db: 数据库会话
    
    Returns:
        创建的对话
    """
    conversation = Conversation(
        id=str(uuid4()),
        title=conversation_data.title,
        model_id=conversation_data.model_id,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """
    获取单个对话详情
    
    Args:
        conversation_id: 对话 ID
        db: 数据库会话
    
    Returns:
        对话详情
    
    Raises:
        HTTPException: 对话不存在时抛出 404
    """
    query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 不存在",
        )
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """
    更新对话
    
    Args:
        conversation_id: 对话 ID
        conversation_data: 更新数据
        db: 数据库会话
    
    Returns:
        更新后的对话
    
    Raises:
        HTTPException: 对话不存在时抛出 404
    """
    query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 不存在",
        )
    
    # 更新字段
    if conversation_data.title is not None:
        conversation.title = conversation_data.title
    
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    删除对话
    
    Args:
        conversation_id: 对话 ID
        db: 数据库会话
    
    Raises:
        HTTPException: 对话不存在时抛出 404
    """
    query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 不存在",
        )
    
    await db.delete(conversation)
    await db.commit()


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[Message]:
    """
    获取对话的所有消息
    
    Args:
        conversation_id: 对话 ID
        db: 数据库会话
    
    Returns:
        消息列表
    
    Raises:
        HTTPException: 对话不存在时抛出 404
    """
    # 检查对话是否存在
    conv_query = select(Conversation).where(Conversation.id == conversation_id)
    conv_result = await db.execute(conv_query)
    if not conv_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {conversation_id} 不存在",
        )
    
    # 查询消息
    query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return messages
