"""
Nexus 基础模型类
提供所有数据库模型的公共功能
"""
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    """
    时间戳混入类
    
    为模型提供创建时间和更新时间字段
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class BaseModel(Base, TimestampMixin):
    """
    基础模型类
    
    所有业务模型都应继承此类，提供公共字段和方法
    """
    
    __abstract__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # 处理 datetime 类型
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        从字典更新模型属性
        
        Args:
            data: 包含更新数据的字典
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """
        返回模型的字符串表示
        
        Returns:
            模型的字符串表示
        """
        class_name = self.__class__.__name__
        pk = getattr(self, "id", None)
        return f"<{class_name}(id={pk})>"
