"""
记忆相关的 Pydantic 模式
定义记忆的请求/响应结构
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.memory import MemoryType


class MemoryBase(BaseModel):
    """
    记忆基础模式
    """
    
    content: str = Field(..., description="记忆内容")
    memory_type: MemoryType = Field(default=MemoryType.WORKING, description="记忆类型")


class MemoryCreate(MemoryBase):
    """
    创建记忆请求模式
    """
    
    importance: float = Field(default=0.5, ge=0, le=1, description="重要性评分")
    source_type: Optional[str] = Field(default=None, description="来源类型")
    source_id: Optional[int] = Field(default=None, description="来源ID")
    tags: Optional[List[str]] = Field(default=None, description="记忆标签")
    metadata: Optional[dict] = Field(default=None, description="记忆元数据")
    expires_at: Optional[str] = Field(default=None, description="过期时间")


class MemoryUpdate(BaseModel):
    """
    更新记忆请求模式
    """
    
    content: Optional[str] = Field(default=None, description="记忆内容")
    importance: Optional[float] = Field(default=None, ge=0, le=1, description="重要性评分")
    memory_type: Optional[MemoryType] = Field(default=None, description="记忆类型")
    tags: Optional[List[str]] = Field(default=None, description="记忆标签")
    metadata: Optional[dict] = Field(default=None, description="记忆元数据")


class MemoryResponse(MemoryBase):
    """
    记忆响应模式
    """
    
    id: int = Field(..., description="记忆ID")
    importance: float = Field(default=0.5, description="重要性评分")
    access_count: int = Field(default=0, description="访问次数")
    last_accessed_at: Optional[str] = Field(default=None, description="最后访问时间")
    expires_at: Optional[str] = Field(default=None, description="过期时间")
    source_type: Optional[str] = Field(default=None, description="来源类型")
    source_id: Optional[int] = Field(default=None, description="来源ID")
    tags: Optional[List[str]] = Field(default=None, description="记忆标签")
    metadata: Optional[dict] = Field(default=None, description="记忆元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


# ==================== 记忆搜索模式 ====================

class MemorySearchRequest(BaseModel):
    """
    记忆搜索请求模式
    """
    
    query: str = Field(..., description="搜索关键词")
    memory_types: Optional[List[MemoryType]] = Field(default=None, description="记忆类型过滤")
    min_importance: Optional[float] = Field(default=None, ge=0, le=1, description="最小重要性")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")


class MemorySearchResult(BaseModel):
    """
    记忆搜索结果模式
    """
    
    memory_id: int = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    memory_type: MemoryType = Field(..., description="记忆类型")
    importance: float = Field(..., description="重要性评分")
    score: float = Field(..., description="相似度分数")
    tags: Optional[List[str]] = Field(default=None, description="记忆标签")
    metadata: Optional[dict] = Field(default=None, description="元数据")


# ==================== 记忆统计模式 ====================

class MemoryStats(BaseModel):
    """
    记忆统计模式
    """
    
    total_count: int = Field(default=0, description="总记忆数量")
    instant_count: int = Field(default=0, description="即时记忆数量")
    working_count: int = Field(default=0, description="工作记忆数量")
    long_term_count: int = Field(default=0, description="长期记忆数量")
    avg_importance: float = Field(default=0, description="平均重要性")
    total_access_count: int = Field(default=0, description="总访问次数")
