"""
文档相关的 Pydantic 模式
定义文档和文档分块的请求/响应结构
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus, DocumentType


# ==================== 文档分块模式 ====================

class DocumentChunkBase(BaseModel):
    """
    文档分块基础模式
    """
    
    content: str = Field(..., description="分块内容")


class DocumentChunkResponse(DocumentChunkBase):
    """
    文档分块响应模式
    """
    
    id: int = Field(..., description="分块ID")
    document_id: int = Field(..., description="文档ID")
    chunk_index: int = Field(..., description="分块索引")
    chunk_hash: Optional[str] = Field(default=None, description="分块哈希")
    token_count: int = Field(default=0, description="Token数量")
    char_count: int = Field(default=0, description="字符数")
    start_char: int = Field(default=0, description="起始字符位置")
    end_char: int = Field(default=0, description="结束字符位置")
    metadata: Optional[dict] = Field(default=None, description="分块元数据")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


# ==================== 文档模式 ====================

class DocumentBase(BaseModel):
    """
    文档基础模式
    """
    
    filename: str = Field(..., description="文件名")
    file_type: DocumentType = Field(..., description="文件类型")


class DocumentCreate(BaseModel):
    """
    创建文档请求模式
    """
    
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_type: DocumentType = Field(default=DocumentType.OTHER, description="文件类型")
    file_size: int = Field(default=0, description="文件大小")
    file_hash: Optional[str] = Field(default=None, description="文件哈希")
    title: Optional[str] = Field(default=None, description="文档标题")


class DocumentUpdate(BaseModel):
    """
    更新文档请求模式
    """
    
    title: Optional[str] = Field(default=None, description="文档标题")
    summary: Optional[str] = Field(default=None, description="文档摘要")
    status: Optional[DocumentStatus] = Field(default=None, description="处理状态")
    metadata: Optional[dict] = Field(default=None, description="文档元数据")


class DocumentResponse(DocumentBase):
    """
    文档响应模式
    """
    
    id: int = Field(..., description="文档ID")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(default=0, description="文件大小（字节）")
    file_hash: Optional[str] = Field(default=None, description="文件哈希")
    status: DocumentStatus = Field(..., description="处理状态")
    chunk_count: int = Field(default=0, description="分块数量")
    title: Optional[str] = Field(default=None, description="文档标题")
    summary: Optional[str] = Field(default=None, description="文档摘要")
    metadata: Optional[dict] = Field(default=None, description="文档元数据")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """
    文档详情响应模式（包含分块）
    """
    
    chunks: List[DocumentChunkResponse] = Field(default_factory=list, description="分块列表")
    
    class Config:
        from_attributes = True


# ==================== 文档上传模式 ====================

class DocumentUploadResponse(BaseModel):
    """
    文档上传响应模式
    """
    
    id: int = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    status: DocumentStatus = Field(..., description="处理状态")
    message: str = Field(default="文档上传成功，正在处理中", description="响应消息")


# ==================== 文档搜索模式 ====================

class DocumentSearchRequest(BaseModel):
    """
    文档搜索请求模式
    """
    
    query: str = Field(..., description="搜索关键词")
    file_types: Optional[List[DocumentType]] = Field(default=None, description="文件类型过滤")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")


class DocumentSearchResult(BaseModel):
    """
    文档搜索结果模式
    """
    
    chunk_id: int = Field(..., description="分块ID")
    document_id: int = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    content: str = Field(..., description="分块内容")
    score: float = Field(..., description="相似度分数")
    metadata: Optional[dict] = Field(default=None, description="元数据")
