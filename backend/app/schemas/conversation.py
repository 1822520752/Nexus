"""
对话相关的 Pydantic 模式
定义对话和消息的请求/响应结构
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 消息模式 ====================

class MessageBase(BaseModel):
    """
    消息基础模式
    """
    
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., description="消息内容")


class MessageCreate(MessageBase):
    """
    创建消息请求模式
    """
    
    tokens: int = Field(default=0, description="Token数量")
    metadata: Optional[dict] = Field(default=None, description="消息元数据")
    parent_id: Optional[int] = Field(default=None, description="父消息ID")


class MessageResponse(MessageBase):
    """
    消息响应模式
    """
    
    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="对话ID")
    tokens: int = Field(default=0, description="Token数量")
    metadata: Optional[dict] = Field(default=None, description="消息元数据")
    parent_id: Optional[int] = Field(default=None, description="父消息ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# ==================== 对话模式 ====================

class ConversationBase(BaseModel):
    """
    对话基础模式
    """
    
    title: str = Field(default="新对话", description="对话标题")


class ConversationCreate(ConversationBase):
    """
    创建对话请求模式
    """
    
    model_id: Optional[int] = Field(default=None, description="模型ID")
    metadata: Optional[dict] = Field(default=None, description="对话元数据")


class ConversationUpdate(BaseModel):
    """
    更新对话请求模式
    """
    
    title: Optional[str] = Field(default=None, description="对话标题")
    model_id: Optional[int] = Field(default=None, description="模型ID")
    summary: Optional[str] = Field(default=None, description="对话摘要")
    is_pinned: Optional[bool] = Field(default=None, description="是否置顶")
    is_archived: Optional[bool] = Field(default=None, description="是否归档")
    metadata: Optional[dict] = Field(default=None, description="对话元数据")


class ConversationResponse(ConversationBase):
    """
    对话响应模式
    """
    
    id: int = Field(..., description="对话ID")
    model_id: Optional[int] = Field(default=None, description="模型ID")
    summary: Optional[str] = Field(default=None, description="对话摘要")
    message_count: int = Field(default=0, description="消息总数")
    total_tokens: int = Field(default=0, description="总Token数")
    metadata: Optional[dict] = Field(default=None, description="对话元数据")
    is_pinned: bool = Field(default=False, description="是否置顶")
    is_archived: bool = Field(default=False, description="是否归档")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    messages: List[MessageResponse] = Field(default_factory=list, description="消息列表")
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """
    对话列表响应模式（不包含消息）
    """
    
    id: int = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    model_id: Optional[int] = Field(default=None, description="模型ID")
    summary: Optional[str] = Field(default=None, description="对话摘要")
    message_count: int = Field(default=0, description="消息总数")
    total_tokens: int = Field(default=0, description="总Token数")
    is_pinned: bool = Field(default=False, description="是否置顶")
    is_archived: bool = Field(default=False, description="是否归档")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# ==================== 聊天请求模式 ====================

class ChatRequest(BaseModel):
    """
    聊天请求模式
    """
    
    conversation_id: Optional[int] = Field(default=None, description="对话ID，不提供则创建新对话")
    message: str = Field(..., description="用户消息")
    model_id: Optional[int] = Field(default=None, description="使用的模型ID")
    stream: bool = Field(default=False, description="是否使用流式响应")
    temperature: Optional[float] = Field(default=None, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="最大Token数")


class ChatMessage(BaseModel):
    """
    聊天消息模式
    """
    
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")


class ChatResponse(BaseModel):
    """
    聊天响应模式
    """
    
    conversation_id: int = Field(..., description="对话ID")
    message: MessageResponse = Field(..., description="AI响应消息")
    usage: Optional[dict] = Field(default=None, description="Token使用统计")
