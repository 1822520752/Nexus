"""
动作历史数据模型
定义动作历史的数据库表结构
"""
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ActionStatus(str, PyEnum):
    """
    动作状态枚举
    
    定义动作执行的各个状态
    """
    
    PENDING = "pending"  # 待执行
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消


class ActionType(str, PyEnum):
    """
    动作类型枚举
    
    定义不同类型的动作
    """
    
    SHELL_COMMAND = "shell_command"  # Shell 命令
    FILE_OPERATION = "file_operation"  # 文件操作
    API_CALL = "api_call"  # API 调用
    CODE_EXECUTION = "code_execution"  # 代码执行
    WEB_SEARCH = "web_search"  # 网络搜索
    DOCUMENT_PROCESSING = "document_processing"  # 文档处理
    MEMORY_OPERATION = "memory_operation"  # 记忆操作
    OTHER = "other"  # 其他


class ActionHistory(BaseModel):
    """
    动作历史模型
    
    存储 AI 执行的动作历史记录
    """
    
    __tablename__ = "action_histories"
    
    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="动作ID",
    )
    
    # 动作类型
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType),
        nullable=False,
        default=ActionType.OTHER,
        index=True,
        comment="动作类型",
    )
    
    # 动作名称
    action_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="动作名称",
    )
    
    # 执行命令/参数
    command: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="执行命令/参数",
    )
    
    # 执行状态
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus),
        nullable=False,
        default=ActionStatus.PENDING,
        index=True,
        comment="执行状态",
    )
    
    # 执行结果
    result: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="执行结果",
    )
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    
    # 关联对话 ID
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment="关联对话ID",
    )
    
    # 关联消息 ID
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="关联消息ID",
    )
    
    # 用户批准时间
    approved_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="用户批准时间",
    )
    
    # 执行开始时间
    started_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="执行开始时间",
    )
    
    # 执行结束时间
    finished_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="执行结束时间",
    )
    
    # 执行耗时（毫秒）
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行耗时（毫秒）",
    )
    
    # 动作元数据（JSON 格式）
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="动作元数据（JSON格式）",
    )
    
    def __repr__(self) -> str:
        return f"<ActionHistory(id={self.id}, type={self.action_type}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            包含模型属性的字典
        """
        import json
        
        result = super().to_dict()
        # 解析 metadata JSON
        if self.metadata:
            try:
                result["metadata"] = json.loads(self.metadata)
            except (json.JSONDecodeError, TypeError):
                pass
        return result
    
    def mark_approved(self) -> None:
        """
        标记动作为已批准
        """
        from datetime import datetime
        
        self.status = ActionStatus.APPROVED
        self.approved_at = datetime.utcnow().isoformat()
    
    def mark_running(self) -> None:
        """
        标记动作为执行中
        """
        from datetime import datetime
        
        self.status = ActionStatus.RUNNING
        self.started_at = datetime.utcnow().isoformat()
    
    def mark_completed(self, result: str) -> None:
        """
        标记动作为已完成
        
        Args:
            result: 执行结果
        """
        from datetime import datetime
        
        self.status = ActionStatus.COMPLETED
        self.result = result
        self.finished_at = datetime.utcnow().isoformat()
        
        # 计算执行耗时
        if self.started_at:
            from datetime import datetime as dt
            
            start = dt.fromisoformat(self.started_at)
            end = dt.fromisoformat(self.finished_at)
            self.duration_ms = int((end - start).total_seconds() * 1000)
    
    def mark_failed(self, error: str) -> None:
        """
        标记动作为执行失败
        
        Args:
            error: 错误信息
        """
        from datetime import datetime
        
        self.status = ActionStatus.FAILED
        self.error_message = error
        self.finished_at = datetime.utcnow().isoformat()
        
        # 计算执行耗时
        if self.started_at:
            from datetime import datetime as dt
            
            start = dt.fromisoformat(self.started_at)
            end = dt.fromisoformat(self.finished_at)
            self.duration_ms = int((end - start).total_seconds() * 1000)
