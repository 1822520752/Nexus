"""
对话交互 API 端点
提供 AI 对话交互接口
"""
import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.model import AIModel
from app.schemas import MessageCreate, MessageResponse

router = APIRouter()


@router.post("/send", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
) -> Message:
    """
    发送消息并获取 AI 回复
    
    Args:
        message_data: 消息数据
        db: 数据库会话
    
    Returns:
        AI 回复消息
    
    Raises:
        HTTPException: 对话或模型不存在时抛出错误
    """
    # 检查对话是否存在
    conv_query = select(Conversation).where(Conversation.id == message_data.conversation_id)
    conv_result = await db.execute(conv_query)
    conversation = conv_result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"对话 {message_data.conversation_id} 不存在",
        )
    
    # 获取模型配置
    model_query = select(AIModel).where(AIModel.id == conversation.model_id, AIModel.enabled == True)
    model_result = await db.execute(model_query)
    model = model_result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型 {conversation.model_id} 不存在或未启用",
        )
    
    # 创建用户消息
    user_message = Message(
        id=str(uuid4()),
        conversation_id=message_data.conversation_id,
        role=message_data.role,
        content=message_data.content,
        timestamp=datetime.utcnow(),
    )
    db.add(user_message)
    
    try:
        # TODO: 调用实际的 AI 服务
        # 这里模拟 AI 回复
        ai_response = await generate_ai_response(
            message_data.content,
            model,
            conversation,
            db,
        )
        
        # 创建 AI 回复消息
        assistant_message = Message(
            id=str(uuid4()),
            conversation_id=message_data.conversation_id,
            role="assistant",
            content=ai_response["content"],
            timestamp=datetime.utcnow(),
            metadata=json.dumps({
                "model": model.name,
                "tokens": ai_response.get("tokens", 0),
                "latency": ai_response.get("latency", 0),
            }),
        )
        db.add(assistant_message)
        
        # 更新对话时间
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(assistant_message)
        
        return assistant_message
        
    except Exception as e:
        logger.error(f"生成 AI 回复失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成 AI 回复失败: {str(e)}",
        )


async def generate_ai_response(
    user_message: str,
    model: AIModel,
    conversation: Conversation,
    db: AsyncSession,
) -> dict:
    """
    生成 AI 回复
    
    Args:
        user_message: 用户消息
        model: AI 模型配置
        conversation: 对话会话
        db: 数据库会话
    
    Returns:
        包含回复内容和元数据的字典
    
    Note:
        这是一个模拟实现，实际使用时需要连接到真实的 AI 服务
    """
    import time
    
    start_time = time.time()
    
    # TODO: 实现实际的 AI 调用逻辑
    # 根据 model.provider 选择不同的 AI 服务
    
    # 模拟延迟
    await asyncio_dummy_delay(0.5)
    
    # 模拟回复
    response = {
        "content": f"这是对 '{user_message[:50]}...' 的模拟回复。\n\n"
                   f"实际使用时将连接到 {model.provider} 服务。\n\n"
                   f"模型配置: {model.name}, 温度: {model.temperature}, 最大 tokens: {model.max_tokens}",
        "tokens": len(user_message) // 4 + 50,
        "latency": int((time.time() - start_time) * 1000),
    }
    
    return response


async def asyncio_dummy_delay(seconds: float) -> None:
    """
    模拟异步延迟
    
    Args:
        seconds: 延迟秒数
    """
    import asyncio
    await asyncio.sleep(seconds)


@router.post("/stream")
async def stream_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    流式发送消息并获取 AI 回复
    
    Args:
        message_data: 消息数据
        db: 数据库会话
    
    Returns:
        流式 AI 回复
    
    Note:
        使用 Server-Sent Events (SSE) 实现流式响应
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def event_generator():
        """事件生成器"""
        # 模拟流式输出
        response_text = "这是一个流式回复的示例。实际使用时将连接到 AI 服务。"
        
        for char in response_text:
            yield f"data: {char}\n\n"
            await asyncio.sleep(0.05)
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
