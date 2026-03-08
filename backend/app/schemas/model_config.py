"""
模型配置相关的 Pydantic 模式
定义模型配置的请求/响应结构
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ModelConfigBase(BaseModel):
    """
    模型配置基础模式
    """
    
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="模型提供商")
    model_type: str = Field(default="chat", description="模型类型")


class ModelConfigCreate(ModelConfigBase):
    """
    创建模型配置请求模式
    """
    
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    is_default: bool = Field(default=False, description="是否为默认模型")
    max_tokens: int = Field(default=4096, description="最大Token数")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    context_window: int = Field(default=8192, description="上下文窗口大小")
    config: Optional[dict] = Field(default=None, description="其他配置")


class ModelConfigUpdate(BaseModel):
    """
    更新模型配置请求模式
    """
    
    name: Optional[str] = Field(default=None, description="模型名称")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    is_default: Optional[bool] = Field(default=None, description="是否为默认模型")
    is_active: Optional[bool] = Field(default=None, description="是否启用")
    max_tokens: Optional[int] = Field(default=None, description="最大Token数")
    temperature: Optional[float] = Field(default=None, ge=0, le=2, description="温度参数")
    context_window: Optional[int] = Field(default=None, description="上下文窗口大小")
    config: Optional[dict] = Field(default=None, description="其他配置")


class ModelConfigResponse(ModelConfigBase):
    """
    模型配置响应模式
    """
    
    id: int = Field(..., description="模型配置ID")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    is_default: bool = Field(default=False, description="是否为默认模型")
    is_active: bool = Field(default=True, description="是否启用")
    max_tokens: int = Field(default=4096, description="最大Token数")
    temperature: float = Field(default=0.7, description="温度参数")
    context_window: int = Field(default=8192, description="上下文窗口大小")
    config: Optional[dict] = Field(default=None, description="其他配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class ModelConfigListResponse(BaseModel):
    """
    模型配置列表响应模式（不包含敏感信息）
    """
    
    id: int = Field(..., description="模型配置ID")
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="模型提供商")
    model_type: str = Field(..., description="模型类型")
    is_default: bool = Field(default=False, description="是否为默认模型")
    is_active: bool = Field(default=True, description="是否启用")
    max_tokens: int = Field(default=4096, description="最大Token数")
    temperature: float = Field(default=0.7, description="温度参数")
    
    class Config:
        from_attributes = True


# ==================== 用户配置模式 ====================

class UserConfigBase(BaseModel):
    """
    用户配置基础模式
    """
    
    key: str = Field(..., description="配置键")
    value: dict = Field(..., description="配置值")


class UserConfigCreate(UserConfigBase):
    """
    创建用户配置请求模式
    """
    
    description: Optional[str] = Field(default=None, description="配置描述")


class UserConfigUpdate(BaseModel):
    """
    更新用户配置请求模式
    """
    
    value: Optional[dict] = Field(default=None, description="配置值")
    description: Optional[str] = Field(default=None, description="配置描述")


class UserConfigResponse(UserConfigBase):
    """
    用户配置响应模式
    """
    
    id: int = Field(..., description="配置ID")
    description: Optional[str] = Field(default=None, description="配置描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
