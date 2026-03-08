"""
通用响应模式
定义 API 响应的通用结构
"""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    基础响应模型
    
    所有 API 响应的基础结构
    """
    
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")


class DataResponse(BaseResponse, Generic[T]):
    """
    数据响应模型
    
    包含单个数据的响应结构
    """
    
    data: Optional[T] = Field(default=None, description="响应数据")


class ListResponse(BaseResponse, Generic[T]):
    """
    列表响应模型
    
    包含列表数据的响应结构
    """
    
    data: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="数据总数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")


class ErrorResponse(BaseModel):
    """
    错误响应模型
    
    错误响应的结构
    """
    
    success: bool = Field(default=False, description="请求是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    details: Optional[dict] = Field(default=None, description="错误详情")


class PaginationParams(BaseModel):
    """
    分页参数模型
    
    用于列表查询的分页参数
    """
    
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """
        计算偏移量
        
        Returns:
            偏移量
        """
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """
        获取限制数量
        
        Returns:
            限制数量
        """
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型
    
    包含分页数据的响应结构
    """
    
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="数据总数")
    skip: int = Field(default=0, description="跳过数量")
    limit: int = Field(default=20, description="返回数量")
