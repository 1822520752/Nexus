"""
动作服务
整合权限检查、沙箱执行和数据库记录的完整服务
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.action import ActionHistory, ActionStatus, ActionType
from app.services.action.executor import (
    CommandExecutor,
    ExecutionRecord,
    ExecutionRequest,
    ExecutionStatus,
    FileOperationExecutor,
    default_executor,
    default_file_executor,
)
from app.services.action.permission import (
    OperationCategory,
    PermissionChecker,
    PermissionLevel,
    default_permission_checker,
)
from app.services.action.sandbox import (
    ExecutionResult,
    ResourceLimits,
    SandboxEnvironment,
    SandboxManager,
)


class ActionService:
    """
    动作服务
    
    整合权限检查、沙箱执行和数据库记录的完整服务
    """
    
    def __init__(
        self,
        db: AsyncSession,
        permission_checker: Optional[PermissionChecker] = None,
        executor: Optional[CommandExecutor] = None,
        file_executor: Optional[FileOperationExecutor] = None,
    ):
        """
        初始化动作服务
        
        Args:
            db: 数据库会话
            permission_checker: 权限检查器
            executor: 命令执行器
            file_executor: 文件操作执行器
        """
        self.db = db
        self.permission_checker = permission_checker or default_permission_checker
        self.executor = executor or default_executor
        self.file_executor = file_executor or default_file_executor
    
    async def preview_command(
        self,
        command: str,
        arguments: Optional[List[str]] = None,
        working_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        预览命令
        
        Args:
            command: 要预览的命令
            arguments: 命令参数
            working_directory: 工作目录
        
        Returns:
            预览结果字典
        """
        logger.info(f"预览命令: {command}")
        
        request = ExecutionRequest(
            command=command,
            arguments=arguments,
            working_directory=working_directory,
        )
        
        preview = self.executor.preview_command(request)
        
        return preview.to_dict()
    
    async def execute_command(
        self,
        command: str,
        arguments: Optional[List[str]] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        input_data: Optional[str] = None,
        auto_approve_safe: bool = True,
        conversation_id: Optional[int] = None,
        message_id: Optional[int] = None,
        action_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            arguments: 命令参数
            working_directory: 工作目录
            environment: 环境变量
            timeout: 超时时间
            input_data: 标准输入
            auto_approve_safe: 是否自动批准安全操作
            conversation_id: 关联对话 ID
            message_id: 关联消息 ID
            action_name: 动作名称
            metadata: 额外元数据
        
        Returns:
            执行结果字典
        """
        logger.info(f"执行命令: {command}")
        
        # 创建执行请求
        request = ExecutionRequest(
            command=command,
            arguments=arguments,
            working_directory=working_directory,
            environment=environment,
            timeout=timeout,
            input_data=input_data,
            auto_approve_safe=auto_approve_safe,
            metadata=metadata or {},
        )
        
        # 创建数据库记录
        action_history = ActionHistory(
            action_type=ActionType.SHELL_COMMAND,
            action_name=action_name or command.split()[0] if command else "unknown",
            command=command,
            status=ActionStatus.PENDING,
            conversation_id=conversation_id,
            message_id=message_id,
            metadata=json.dumps(metadata) if metadata else None,
        )
        
        self.db.add(action_history)
        await self.db.flush()
        
        try:
            # 执行命令
            record = await self.executor.execute(
                request=request,
                request_id=str(action_history.id),
            )
            
            # 更新数据库记录
            await self._update_action_from_record(action_history, record)
            
            await self.db.commit()
            await self.db.refresh(action_history)
            
            return {
                "action_id": action_history.id,
                "status": action_history.status.value,
                "result": action_history.result,
                "error_message": action_history.error_message,
                "duration_ms": action_history.duration_ms,
                "execution_record": record.to_dict(),
            }
            
        except Exception as e:
            logger.error(f"执行命令失败: {e}")
            action_history.status = ActionStatus.FAILED
            action_history.error_message = str(e)
            action_history.finished_at = datetime.utcnow().isoformat()
            await self.db.commit()
            
            raise
    
    async def confirm_execution(
        self,
        action_id: int,
        approved: bool,
        confirmed_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        确认执行
        
        Args:
            action_id: 动作 ID
            approved: 是否批准
            confirmed_by: 确认用户
        
        Returns:
            更新后的动作信息
        """
        logger.info(f"确认执行: action_id={action_id}, approved={approved}")
        
        # 查询动作记录
        query = select(ActionHistory).where(ActionHistory.id == action_id)
        result = await self.db.execute(query)
        action_history = result.scalar_one_or_none()
        
        if not action_history:
            raise ValueError(f"动作 {action_id} 不存在")
        
        if action_history.status != ActionStatus.PENDING:
            raise ValueError(f"动作状态不正确: {action_history.status.value}")
        
        if approved:
            action_history.mark_approved()
            
            # 执行命令
            request = ExecutionRequest(
                command=action_history.command,
                metadata=json.loads(action_history.metadata) if action_history.metadata else {},
            )
            
            record = await self.executor.execute(
                request=request,
                request_id=str(action_history.id),
                skip_confirmation=True,
            )
            
            await self._update_action_from_record(action_history, record)
        else:
            action_history.status = ActionStatus.REJECTED
            action_history.finished_at = datetime.utcnow().isoformat()
        
        await self.db.commit()
        await self.db.refresh(action_history)
        
        return action_history.to_dict()
    
    async def get_action_status(self, action_id: int) -> Dict[str, Any]:
        """
        获取动作状态
        
        Args:
            action_id: 动作 ID
        
        Returns:
            动作状态信息
        """
        query = select(ActionHistory).where(ActionHistory.id == action_id)
        result = await self.db.execute(query)
        action_history = result.scalar_one_or_none()
        
        if not action_history:
            raise ValueError(f"动作 {action_id} 不存在")
        
        return action_history.to_dict()
    
    async def get_action_history(
        self,
        conversation_id: Optional[int] = None,
        status: Optional[ActionStatus] = None,
        action_type: Optional[ActionType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        获取动作历史
        
        Args:
            conversation_id: 对话 ID 过滤
            status: 状态过滤
            action_type: 类型过滤
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            动作历史列表
        """
        query = select(ActionHistory)
        
        if conversation_id:
            query = query.where(ActionHistory.conversation_id == conversation_id)
        if status:
            query = query.where(ActionHistory.status == status)
        if action_type:
            query = query.where(ActionHistory.action_type == action_type)
        
        query = query.order_by(ActionHistory.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        actions = result.scalars().all()
        
        return [action.to_dict() for action in actions]
    
    async def execute_file_operation(
        self,
        operation: str,
        file_path: str,
        content: Optional[str] = None,
        conversation_id: Optional[int] = None,
        message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        执行文件操作
        
        Args:
            operation: 操作类型 (read/write/delete)
            file_path: 文件路径
            content: 文件内容（写入时需要）
            conversation_id: 关联对话 ID
            message_id: 关联消息 ID
        
        Returns:
            执行结果
        """
        # 映射操作类型
        operation_map = {
            "read": OperationCategory.FILE_READ,
            "write": OperationCategory.FILE_WRITE,
            "delete": OperationCategory.FILE_DELETE,
        }
        
        op_category = operation_map.get(operation.lower())
        if not op_category:
            raise ValueError(f"不支持的操作类型: {operation}")
        
        logger.info(f"执行文件操作: {operation} {file_path}")
        
        # 预览操作
        preview = self.file_executor.preview_file_operation(
            operation=op_category,
            file_path=file_path,
            content=content,
        )
        
        # 检查是否需要确认
        assessment = preview.get("risk_assessment", {})
        if assessment.get("requires_confirmation", False):
            # 创建待确认记录
            action_history = ActionHistory(
                action_type=ActionType.FILE_OPERATION,
                action_name=f"文件{operation}",
                command=f"{operation} {file_path}",
                status=ActionStatus.PENDING,
                conversation_id=conversation_id,
                message_id=message_id,
                metadata=json.dumps(preview),
            )
            
            self.db.add(action_history)
            await self.db.commit()
            await self.db.refresh(action_history)
            
            return {
                "action_id": action_history.id,
                "status": "awaiting_confirmation",
                "preview": preview,
                "message": "操作需要确认",
            }
        
        # 执行操作
        result = await self.file_executor.execute_file_operation(
            operation=op_category,
            file_path=file_path,
            content=content,
        )
        
        # 记录到数据库
        action_history = ActionHistory(
            action_type=ActionType.FILE_OPERATION,
            action_name=f"文件{operation}",
            command=f"{operation} {file_path}",
            status=ActionStatus.COMPLETED if result.get("success") else ActionStatus.FAILED,
            result=json.dumps(result),
            error_message=result.get("error_message"),
            conversation_id=conversation_id,
            message_id=message_id,
            duration_ms=result.get("duration_ms"),
        )
        
        self.db.add(action_history)
        await self.db.commit()
        await self.db.refresh(action_history)
        
        return {
            "action_id": action_history.id,
            "status": action_history.status.value,
            "result": result,
        }
    
    async def cancel_action(self, action_id: int) -> Dict[str, Any]:
        """
        取消动作
        
        Args:
            action_id: 动作 ID
        
        Returns:
            更新后的动作信息
        """
        query = select(ActionHistory).where(ActionHistory.id == action_id)
        result = await self.db.execute(query)
        action_history = result.scalar_one_or_none()
        
        if not action_history:
            raise ValueError(f"动作 {action_id} 不存在")
        
        if action_history.status not in (ActionStatus.PENDING,):
            raise ValueError(f"动作状态不允许取消: {action_history.status.value}")
        
        action_history.status = ActionStatus.CANCELLED
        action_history.finished_at = datetime.utcnow().isoformat()
        
        await self.db.commit()
        await self.db.refresh(action_history)
        
        return action_history.to_dict()
    
    async def get_pending_confirmations(self) -> List[Dict[str, Any]]:
        """
        获取待确认的动作列表
        
        Returns:
            待确认动作列表
        """
        query = select(ActionHistory).where(
            ActionHistory.status == ActionStatus.PENDING
        )
        query = query.order_by(ActionHistory.created_at.desc())
        
        result = await self.db.execute(query)
        actions = result.scalars().all()
        
        return [action.to_dict() for action in actions]
    
    async def _update_action_from_record(
        self,
        action: ActionHistory,
        record: ExecutionRecord,
    ) -> None:
        """
        从执行记录更新动作
        
        Args:
            action: 动作记录
            record: 执行记录
        """
        # 映射状态
        status_map = {
            ExecutionStatus.PENDING: ActionStatus.PENDING,
            ExecutionStatus.PREVIEWING: ActionStatus.PENDING,
            ExecutionStatus.AWAITING_CONFIRM: ActionStatus.PENDING,
            ExecutionStatus.APPROVED: ActionStatus.APPROVED,
            ExecutionStatus.REJECTED: ActionStatus.REJECTED,
            ExecutionStatus.RUNNING: ActionStatus.RUNNING,
            ExecutionStatus.COMPLETED: ActionStatus.COMPLETED,
            ExecutionStatus.FAILED: ActionStatus.FAILED,
            ExecutionStatus.TIMEOUT: ActionStatus.FAILED,
            ExecutionStatus.CANCELLED: ActionStatus.CANCELLED,
        }
        
        action.status = status_map.get(record.status, ActionStatus.PENDING)
        
        if record.result:
            action.result = json.dumps(record.result.to_dict())
            action.duration_ms = record.result.duration_ms
        
        if record.error_message:
            action.error_message = record.error_message
        
        if record.started_at:
            action.started_at = record.started_at
        
        if record.finished_at:
            action.finished_at = record.finished_at
        
        if record.confirmed_at:
            action.approved_at = record.confirmed_at


class ActionServiceFactory:
    """
    动作服务工厂
    
    用于创建配置好的动作服务实例
    """
    
    @staticmethod
    def create(
        db: AsyncSession,
        allowed_directories: Optional[List[str]] = None,
        blocked_directories: Optional[List[str]] = None,
        auto_approve_safe: bool = True,
        max_cpu_time: int = 30,
        max_memory_mb: int = 512,
    ) -> ActionService:
        """
        创建动作服务实例
        
        Args:
            db: 数据库会话
            allowed_directories: 允许操作的目录
            blocked_directories: 禁止操作的目录
            auto_approve_safe: 是否自动批准安全操作
            max_cpu_time: 最大 CPU 时间
            max_memory_mb: 最大内存使用
        
        Returns:
            配置好的动作服务实例
        """
        # 创建权限检查器
        permission_checker = PermissionChecker(
            allowed_directories=allowed_directories,
            blocked_directories=blocked_directories,
            auto_approve_safe=auto_approve_safe,
        )
        
        # 创建资源限制
        resource_limits = ResourceLimits(
            max_cpu_time=max_cpu_time,
            max_memory_mb=max_memory_mb,
        )
        
        # 创建沙箱管理器
        sandbox_manager = SandboxManager()
        
        # 创建执行器
        executor = CommandExecutor(
            permission_checker=permission_checker,
            sandbox_manager=sandbox_manager,
            resource_limits=resource_limits,
        )
        
        # 创建文件操作执行器
        file_executor = FileOperationExecutor(
            permission_checker=permission_checker,
        )
        
        return ActionService(
            db=db,
            permission_checker=permission_checker,
            executor=executor,
            file_executor=file_executor,
        )
