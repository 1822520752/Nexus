"""
AI 模型配置数据模型
定义模型配置的数据库表结构
"""
from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import decrypt_value, encrypt_value
from app.models.base import BaseModel


class ModelConfig(BaseModel):
    """
    AI 模型配置模型
    
    存储用户配置的 AI 模型信息，支持多种提供商
    """
    
    __tablename__ = "model_configs"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="模型配置ID")
    
    # 模型名称
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模型名称",
    )
    
    # 提供商：ollama, openai, deepseek, anthropic, custom
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="模型提供商",
    )
    
    # API 密钥（加密存储）
    _api_key: Mapped[Optional[str]] = mapped_column(
        "api_key",
        String(500),
        nullable=True,
        comment="API密钥（加密存储）",
    )
    
    # API 基础 URL
    base_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API基础URL",
    )
    
    # 模型类型：chat, embedding, image, audio
    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="chat",
        comment="模型类型",
    )
    
    # 是否为默认模型
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否为默认模型",
    )
    
    # 是否启用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否启用",
    )
    
    # 最大 Token 数
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4096,
        comment="最大Token数",
    )
    
    # 温度参数
    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.7,
        comment="温度参数",
    )
    
    # 上下文窗口大小
    context_window: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=8192,
        comment="上下文窗口大小",
    )
    
    # 其他配置（JSON 格式）
    config: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="其他配置（JSON格式）",
    )
    
    @property
    def api_key(self) -> Optional[str]:
        """
        获取解密后的 API 密钥
        
        Returns:
            解密后的 API 密钥
        """
        if self._api_key:
            try:
                return decrypt_value(self._api_key)
            except Exception:
                return self._api_key
        return None
    
    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """
        设置并加密 API 密钥
        
        Args:
            value: 原始 API 密钥
        """
        if value:
            self._api_key = encrypt_value(value)
        else:
            self._api_key = None
    
    def __repr__(self) -> str:
        return f"<ModelConfig(id={self.id}, name={self.name}, provider={self.provider})>"
    
    def to_dict(self, include_api_key: bool = False) -> dict:
        """
        将模型转换为字典
        
        Args:
            include_api_key: 是否包含 API 密钥（脱敏处理）
            
        Returns:
            包含模型属性的字典
        """
        import json
        
        result = {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "base_url": self.base_url,
            "model_type": self.model_type,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_window": self.context_window,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 处理 API 密钥（脱敏）
        if include_api_key and self._api_key:
            # 只显示前4位和后4位
            key = self.api_key or ""
            if len(key) > 8:
                result["api_key"] = key[:4] + "****" + key[-4:]
            else:
                result["api_key"] = "****"
        else:
            result["api_key"] = None
        
        # 解析 config JSON
        if self.config:
            try:
                result["config"] = json.loads(self.config)
            except (json.JSONDecodeError, TypeError):
                result["config"] = self.config
        
        return result
