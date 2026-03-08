"""
用户配置数据模型
定义用户配置的数据库表结构
"""
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserConfig(BaseModel):
    """
    用户配置模型
    
    存储应用程序的用户配置信息，以键值对形式存储
    """
    
    __tablename__ = "user_configs"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="配置ID")
    
    # 配置键（唯一）
    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="配置键",
    )
    
    # 配置值（JSON 格式）
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="配置值（JSON格式）",
    )
    
    # 配置描述
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="配置描述",
    )
    
    def __repr__(self) -> str:
        return f"<UserConfig(id={self.id}, key={self.key})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        import json
        
        result = super().to_dict()
        # 尝试解析 JSON 值
        try:
            result["value"] = json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            pass
        return result
