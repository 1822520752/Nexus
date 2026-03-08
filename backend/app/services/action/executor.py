"""
命令执行器
提供命令预览、风险评估和执行确认机制
"""
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from app.core.logger import logger
from app.services.action.permission import (
    OperationCategory,
    PermissionChecker,
    PermissionLevel,
    RiskAssessment,
    default_permission_checker,
)
from app.services.action.sandbox import (
    ExecutionResult,
    ResourceLimits,
    SandboxEnvironment,
    SandboxManager,
)


class ExecutionStatus(str, Enum):
    """
    执行状态枚举
    
    定义动作执行的状态流转
    """
    
    PENDING = "pending"           # 待执行
    PREVIEWING = "previewing"     # 预览中
    AWAITING_CONFIRM = "awaiting_confirm"  # 等待确认
    APPROVED = "approved"         # 已批准
    REJECTED = "rejected"         # 已拒绝
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 执行失败
    TIMEOUT = "timeout"           # 执行超时
    CANCELLED = "cancelled"       # 已取消


@dataclass
class CommandPreview:
    """
    命令预览结果
    
    包含命令解析和风险评估的详细信息
    """
    
    command: str                              # 原始命令
    command_name: str                         # 命令名称
    arguments: List[str]                      # 参数列表
    working_directory: str                    # 工作目录
    risk_assessment: Dict[str, Any]           # 风险评估结果
    safety_tips: List[str]                    # 安全提示
    estimated_impact: str                     # 预估影响
    requires_confirmation: bool               # 是否需要确认
    preview_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含预览信息的字典
        """
        return {
            "command": self.command,
            "command_name": self.command_name,
            "arguments": self.arguments,
            "working_directory": self.working_directory,
            "risk_assessment": self.risk_assessment,
            "safety_tips": self.safety_tips,
            "estimated_impact": self.estimated_impact,
            "requires_confirmation": self.requires_confirmation,
            "preview_time": self.preview_time,
        }


@dataclass
class ExecutionRequest:
    """
    执行请求
    
    包含执行命令所需的所有信息
    """
    
    command: str                              # 要执行的命令
    arguments: Optional[List[str]] = None     # 命令参数
    working_directory: Optional[str] = None   # 工作目录
    environment: Optional[Dict[str, str]] = None  # 环境变量
    timeout: int = 30                         # 超时时间（秒）
    input_data: Optional[str] = None          # 标准输入
    auto_approve_safe: bool = True            # 是否自动批准安全操作
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含请求信息的字典
        """
        return {
            "command": self.command,
            "arguments": self.arguments,
            "working_directory": self.working_directory,
            "environment": self.environment,
            "timeout": self.timeout,
            "input_data": self.input_data,
            "auto_approve_safe": self.auto_approve_safe,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionRecord:
    """
    执行记录
    
    记录完整的执行过程和结果
    """
    
    request_id: str                           # 请求 ID
    request: ExecutionRequest                 # 执行请求
    preview: Optional[CommandPreview] = None  # 命令预览
    status: ExecutionStatus = ExecutionStatus.PENDING  # 执行状态
    result: Optional[ExecutionResult] = None  # 执行结果
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None          # 开始时间
    finished_at: Optional[str] = None         # 结束时间
    confirmed_by: Optional[str] = None        # 确认用户
    confirmed_at: Optional[str] = None        # 确认时间
    error_message: Optional[str] = None       # 错误信息
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含执行记录的字典
        """
        return {
            "request_id": self.request_id,
            "request": self.request.to_dict(),
            "preview": self.preview.to_dict() if self.preview else None,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at,
            "error_message": self.error_message,
        }


class CommandExecutor:
    """
    命令执行器
    
    提供命令预览、风险评估、执行确认和结果反馈的完整流程
    """
    
    def __init__(
        self,
        permission_checker: Optional[PermissionChecker] = None,
        sandbox_manager: Optional[SandboxManager] = None,
        resource_limits: Optional[ResourceLimits] = None,
        confirmation_callback: Optional[Callable] = None,
    ):
        """
        初始化命令执行器
        
        Args:
            permission_checker: 权限检查器
            sandbox_manager: 沙箱管理器
            resource_limits: 资源限制配置
            confirmation_callback: 确认回调函数
        """
        self.permission_checker = permission_checker or default_permission_checker
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.resource_limits = resource_limits or ResourceLimits()
        self.confirmation_callback = confirmation_callback
        
        # 执行记录存储
        self._records: Dict[str, ExecutionRecord] = {}
        self._pending_confirmations: Dict[str, ExecutionRecord] = {}
    
    def preview_command(
        self,
        request: ExecutionRequest,
    ) -> CommandPreview:
        """
        预览命令并评估风险
        
        Args:
            request: 执行请求
        
        Returns:
            命令预览结果
        """
        logger.info(f"预览命令: {request.command}")
        
        # 获取风险评估
        assessment = self.permission_checker.assess_command(request.command)
        
        # 解析命令组件
        parts = request.command.split()
        command_name = parts[0] if parts else ""
        arguments = parts[1:] if len(parts) > 1 else []
        if request.arguments:
            arguments = request.arguments
        
        # 确定工作目录
        working_directory = request.working_directory or str(self._get_default_working_directory())
        
        # 评估预估影响
        estimated_impact = self._estimate_impact(assessment, request)
        
        # 确定是否需要确认
        requires_confirmation = assessment.requires_confirmation
        if request.auto_approve_safe and assessment.level == PermissionLevel.SAFE:
            requires_confirmation = False
        
        preview = CommandPreview(
            command=request.command,
            command_name=command_name,
            arguments=arguments,
            working_directory=working_directory,
            risk_assessment=assessment.to_dict(),
            safety_tips=self.permission_checker._get_safety_tips(assessment),
            estimated_impact=estimated_impact,
            requires_confirmation=requires_confirmation,
        )
        
        logger.debug(f"命令预览完成: {request.command[:50]}... -> {assessment.level.value}")
        
        return preview
    
    async def execute(
        self,
        request: ExecutionRequest,
        request_id: Optional[str] = None,
        skip_confirmation: bool = False,
    ) -> ExecutionRecord:
        """
        执行命令
        
        Args:
            request: 执行请求
            request_id: 请求 ID（可选）
            skip_confirmation: 是否跳过确认（仅用于安全操作）
        
        Returns:
            执行记录
        """
        import uuid
        
        # 生成请求 ID
        request_id = request_id or str(uuid.uuid4())
        
        # 创建执行记录
        record = ExecutionRecord(
            request_id=request_id,
            request=request,
            status=ExecutionStatus.PENDING,
        )
        self._records[request_id] = record
        
        try:
            # 预览命令
            record.status = ExecutionStatus.PREVIEWING
            preview = self.preview_command(request)
            record.preview = preview
            
            # 检查是否需要确认
            if preview.requires_confirmation and not skip_confirmation:
                record.status = ExecutionStatus.AWAITING_CONFIRM
                self._pending_confirmations[request_id] = record
                
                logger.info(f"命令等待确认: {request_id}")
                
                # 如果有确认回调，调用它
                if self.confirmation_callback:
                    await self.confirmation_callback(record)
                
                return record
            
            # 直接执行
            return await self._execute_internal(record)
            
        except Exception as e:
            record.status = ExecutionStatus.FAILED
            record.error_message = str(e)
            record.finished_at = datetime.utcnow().isoformat()
            
            logger.error(f"命令执行失败: {request_id}, 错误: {e}")
            
            return record
    
    async def confirm_execution(
        self,
        request_id: str,
        approved: bool,
        confirmed_by: Optional[str] = None,
    ) -> ExecutionRecord:
        """
        确认执行
        
        Args:
            request_id: 请求 ID
            approved: 是否批准
            confirmed_by: 确认用户
        
        Returns:
            更新后的执行记录
        
        Raises:
            ValueError: 请求不存在或状态不正确
        """
        record = self._pending_confirmations.get(request_id)
        if not record:
            raise ValueError(f"请求 {request_id} 不存在或不需要确认")
        
        if record.status != ExecutionStatus.AWAITING_CONFIRM:
            raise ValueError(f"请求状态不正确: {record.status.value}")
        
        record.confirmed_by = confirmed_by
        record.confirmed_at = datetime.utcnow().isoformat()
        
        if approved:
            record.status = ExecutionStatus.APPROVED
            # 从待确认列表移除
            self._pending_confirmations.pop(request_id, None)
            
            # 执行命令
            return await self._execute_internal(record)
        else:
            record.status = ExecutionStatus.REJECTED
            record.finished_at = datetime.utcnow().isoformat()
            
            # 从待确认列表移除
            self._pending_confirmations.pop(request_id, None)
            
            logger.info(f"命令执行被拒绝: {request_id}")
            
            return record
    
    async def _execute_internal(self, record: ExecutionRecord) -> ExecutionRecord:
        """
        内部执行方法
        
        Args:
            record: 执行记录
        
        Returns:
            更新后的执行记录
        """
        request = record.request
        
        logger.info(f"开始执行命令: {record.request_id}")
        
        record.status = ExecutionStatus.RUNNING
        record.started_at = datetime.utcnow().isoformat()
        
        try:
            # 创建沙箱环境
            sandbox = SandboxEnvironment(
                working_directory=request.working_directory,
                resource_limits=self.resource_limits,
                custom_env=request.environment,
            )
            
            # 执行命令
            result = await sandbox.execute(
                command=request.command,
                args=request.arguments,
                input_data=request.input_data,
                timeout=request.timeout,
            )
            
            record.result = result
            
            # 更新状态
            if result.success:
                record.status = ExecutionStatus.COMPLETED
            elif result.timed_out:
                record.status = ExecutionStatus.TIMEOUT
            else:
                record.status = ExecutionStatus.FAILED
                record.error_message = result.error_message or f"命令执行失败，退出码: {result.exit_code}"
            
            record.finished_at = datetime.utcnow().isoformat()
            
            logger.info(
                f"命令执行完成: {record.request_id}, "
                f"状态: {record.status.value}, "
                f"耗时: {result.duration_ms}ms"
            )
            
            return record
            
        except Exception as e:
            record.status = ExecutionStatus.FAILED
            record.error_message = str(e)
            record.finished_at = datetime.utcnow().isoformat()
            
            logger.error(f"命令执行异常: {record.request_id}, 错误: {e}")
            
            return record
    
    def get_record(self, request_id: str) -> Optional[ExecutionRecord]:
        """
        获取执行记录
        
        Args:
            request_id: 请求 ID
        
        Returns:
            执行记录，不存在则返回 None
        """
        return self._records.get(request_id)
    
    def get_pending_confirmations(self) -> List[ExecutionRecord]:
        """
        获取所有待确认的执行记录
        
        Returns:
            待确认的执行记录列表
        """
        return list(self._pending_confirmations.values())
    
    def get_history(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[ExecutionStatus] = None,
    ) -> List[ExecutionRecord]:
        """
        获取执行历史
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            status: 状态过滤
        
        Returns:
            执行记录列表
        """
        records = list(self._records.values())
        
        # 按创建时间倒序排序
        records.sort(key=lambda r: r.created_at, reverse=True)
        
        # 状态过滤
        if status:
            records = [r for r in records if r.status == status]
        
        # 分页
        return records[offset:offset + limit]
    
    def cancel_execution(self, request_id: str) -> ExecutionRecord:
        """
        取消执行
        
        Args:
            request_id: 请求 ID
        
        Returns:
            更新后的执行记录
        
        Raises:
            ValueError: 请求不存在或无法取消
        """
        record = self._records.get(request_id)
        if not record:
            raise ValueError(f"请求 {request_id} 不存在")
        
        if record.status not in (ExecutionStatus.PENDING, ExecutionStatus.AWAITING_CONFIRM):
            raise ValueError(f"请求状态不允许取消: {record.status.value}")
        
        record.status = ExecutionStatus.CANCELLED
        record.finished_at = datetime.utcnow().isoformat()
        
        # 从待确认列表移除
        self._pending_confirmations.pop(request_id, None)
        
        logger.info(f"命令执行已取消: {request_id}")
        
        return record
    
    def _get_default_working_directory(self) -> str:
        """
        获取默认工作目录
        
        Returns:
            默认工作目录路径
        """
        import tempfile
        return tempfile.gettempdir()
    
    def _estimate_impact(
        self,
        assessment: RiskAssessment,
        request: ExecutionRequest,
    ) -> str:
        """
        评估预估影响
        
        Args:
            assessment: 风险评估结果
            request: 执行请求
        
        Returns:
            预估影响描述
        """
        if assessment.level == PermissionLevel.DANGEROUS:
            return "高风险操作，可能影响系统稳定性或数据安全"
        elif assessment.level == PermissionLevel.MODERATE:
            return "中等风险操作，可能修改文件或配置"
        else:
            return "低风险操作，通常只读取信息"


class FileOperationExecutor:
    """
    文件操作执行器
    
    提供文件操作的预览、确认和执行
    """
    
    def __init__(
        self,
        permission_checker: Optional[PermissionChecker] = None,
    ):
        """
        初始化文件操作执行器
        
        Args:
            permission_checker: 权限检查器
        """
        self.permission_checker = permission_checker or default_permission_checker
    
    def preview_file_operation(
        self,
        operation: OperationCategory,
        file_path: str,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        预览文件操作
        
        Args:
            operation: 操作类型
            file_path: 文件路径
            content: 文件内容（写入操作时）
        
        Returns:
            预览信息字典
        """
        from pathlib import Path
        
        logger.info(f"预览文件操作: {operation.value} {file_path}")
        
        # 获取风险评估
        assessment = self.permission_checker.assess_file_operation(operation, file_path)
        
        # 获取文件信息
        path = Path(file_path)
        file_exists = path.exists()
        file_size = path.stat().st_size if file_exists else 0
        
        preview = {
            "operation": operation.value,
            "file_path": file_path,
            "file_exists": file_exists,
            "file_size": file_size,
            "risk_assessment": assessment.to_dict(),
            "requires_confirmation": assessment.requires_confirmation,
            "preview_time": datetime.utcnow().isoformat(),
        }
        
        # 添加操作特定信息
        if operation == OperationCategory.FILE_READ:
            preview["estimated_impact"] = "读取文件内容，不会修改文件"
        elif operation == OperationCategory.FILE_WRITE:
            preview["estimated_impact"] = "创建或覆盖文件"
            preview["content_size"] = len(content) if content else 0
        elif operation == OperationCategory.FILE_DELETE:
            preview["estimated_impact"] = "永久删除文件，无法恢复"
        
        return preview
    
    async def execute_file_operation(
        self,
        operation: OperationCategory,
        file_path: str,
        content: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        执行文件操作
        
        Args:
            operation: 操作类型
            file_path: 文件路径
            content: 文件内容（写入操作时）
            encoding: 文件编码
        
        Returns:
            执行结果字典
        """
        from pathlib import Path
        
        logger.info(f"执行文件操作: {operation.value} {file_path}")
        
        start_time = datetime.utcnow()
        path = Path(file_path)
        
        result = {
            "operation": operation.value,
            "file_path": file_path,
            "success": False,
            "started_at": start_time.isoformat(),
        }
        
        try:
            if operation == OperationCategory.FILE_READ:
                # 读取文件
                content = path.read_text(encoding=encoding)
                result["success"] = True
                result["content"] = content
                result["file_size"] = len(content)
                
            elif operation == OperationCategory.FILE_WRITE:
                # 写入文件
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content or "", encoding=encoding)
                result["success"] = True
                result["bytes_written"] = len(content or "")
                
            elif operation == OperationCategory.FILE_DELETE:
                # 删除文件
                if path.exists():
                    path.unlink()
                    result["success"] = True
                else:
                    result["error_message"] = "文件不存在"
            
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"文件操作失败: {operation.value} {file_path}, 错误: {e}")
        
        end_time = datetime.utcnow()
        result["finished_at"] = end_time.isoformat()
        result["duration_ms"] = int((end_time - start_time).total_seconds() * 1000)
        
        return result


# 创建默认执行器实例
default_executor = CommandExecutor()
default_file_executor = FileOperationExecutor()
