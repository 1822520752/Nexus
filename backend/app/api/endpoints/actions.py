"""
动作执行 API 端点
提供命令预览、执行、确认和历史查询接口
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.action import ActionStatus, ActionType
from app.schemas.action import (
    ActionConfirmRequest,
    ActionHistoryListResponse,
    ActionStatusResponse,
    CommandExecuteRequest,
    CommandExecuteResponse,
    CommandPreviewRequest,
    CommandPreviewResponse,
    CommandPreviewResponse,
    FileOperationRequest,
    FileOperationResponse,
    PendingConfirmationsResponse,
    RiskAssessmentResponse,
)
from app.schemas.common import BaseResponse, DataResponse, ListResponse
from app.services.action.action_service import ActionService, ActionServiceFactory

router = APIRouter()


def get_action_service(db: AsyncSession = Depends(get_db)) -> ActionService:
    """
    获取动作服务实例
    
    Args:
        db: 数据库会话
    
    Returns:
        动作服务实例
    """
    return ActionServiceFactory.create(db)


@router.post("/preview", response_model=DataResponse[CommandPreviewResponse])
async def preview_command(
    request: CommandPreviewRequest,
    service: ActionService = Depends(get_action_service),
) -> DataResponse[CommandPreviewResponse]:
    """
    预览命令
    
    分析命令风险并返回预览信息，不执行命令。
    
    Args:
        request: 预览请求
        service: 动作服务
    
    Returns:
        包含命令预览信息的响应
    """
    try:
        logger.info(f"预览命令: {request.command}")
        
        result = await service.preview_command(
            command=request.command,
            arguments=request.arguments,
            working_directory=request.working_directory,
        )
        
        # 构建响应
        preview = CommandPreviewResponse(
            command=result["command"],
            command_name=result["command_name"],
            arguments=result["arguments"],
            working_directory=result["working_directory"],
            risk_assessment=RiskAssessmentResponse(**result["risk_assessment"]),
            safety_tips=result["safety_tips"],
            estimated_impact=result["estimated_impact"],
            requires_confirmation=result["requires_confirmation"],
            preview_time=result["preview_time"],
        )
        
        return DataResponse(
            success=True,
            message="命令预览成功",
            data=preview,
        )
        
    except Exception as e:
        logger.error(f"预览命令失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览命令失败: {str(e)}",
        )


@router.post("/execute", response_model=DataResponse[CommandExecuteResponse])
async def execute_command(
    request: CommandExecuteRequest,
    service: ActionService = Depends(get_action_service),
) -> DataResponse[CommandExecuteResponse]:
    """
    执行命令
    
    执行指定的命令，根据风险评估可能需要用户确认。
    
    Args:
        request: 执行请求
        service: 动作服务
    
    Returns:
        包含执行结果的响应
    """
    try:
        logger.info(f"执行命令: {request.command}")
        
        result = await service.execute_command(
            command=request.command,
            arguments=request.arguments,
            working_directory=request.working_directory,
            environment=request.environment,
            timeout=request.timeout,
            input_data=request.input_data,
            auto_approve_safe=request.auto_approve_safe,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            action_name=request.action_name,
            metadata=request.metadata,
        )
        
        response = CommandExecuteResponse(
            action_id=result["action_id"],
            status=result["status"],
            result=result.get("result"),
            error_message=result.get("error_message"),
            duration_ms=result.get("duration_ms"),
            execution_record=result.get("execution_record"),
        )
        
        return DataResponse(
            success=True,
            message="命令执行完成" if result["status"] != "awaiting_confirmation" else "命令等待确认",
            data=response,
        )
        
    except ValueError as e:
        logger.warning(f"命令执行参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行命令失败: {str(e)}",
        )


@router.post("/{action_id}/confirm", response_model=DataResponse[dict])
async def confirm_execution(
    action_id: int,
    request: ActionConfirmRequest,
    service: ActionService = Depends(get_action_service),
) -> DataResponse[dict]:
    """
    确认执行
    
    确认或拒绝待执行的动作。
    
    Args:
        action_id: 动作 ID
        request: 确认请求
        service: 动作服务
    
    Returns:
        包含更新后动作信息的响应
    """
    try:
        logger.info(f"确认执行: action_id={action_id}, approved={request.approved}")
        
        result = await service.confirm_execution(
            action_id=action_id,
            approved=request.approved,
            confirmed_by=request.confirmed_by,
        )
        
        return DataResponse(
            success=True,
            message="动作已批准" if request.approved else "动作已拒绝",
            data=result,
        )
        
    except ValueError as e:
        logger.warning(f"确认执行参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"确认执行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认执行失败: {str(e)}",
        )


@router.get("/{action_id}/status", response_model=DataResponse[ActionStatusResponse])
async def get_action_status(
    action_id: int,
    service: ActionService = Depends(get_action_service),
) -> DataResponse[ActionStatusResponse]:
    """
    获取动作状态
    
    查询指定动作的执行状态和结果。
    
    Args:
        action_id: 动作 ID
        service: 动作服务
    
    Returns:
        包含动作状态信息的响应
    """
    try:
        result = await service.get_action_status(action_id)
        
        response = ActionStatusResponse(**result)
        
        return DataResponse(
            success=True,
            message="获取动作状态成功",
            data=response,
        )
        
    except ValueError as e:
        logger.warning(f"获取动作状态参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"获取动作状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取动作状态失败: {str(e)}",
        )


@router.get("/history", response_model=ActionHistoryListResponse)
async def get_action_history(
    conversation_id: Optional[int] = Query(default=None, description="对话 ID 过滤"),
    status: Optional[ActionStatus] = Query(default=None, description="状态过滤"),
    action_type: Optional[ActionType] = Query(default=None, description="类型过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=100, description="每页数量"),
    service: ActionService = Depends(get_action_service),
) -> ActionHistoryListResponse:
    """
    获取动作历史
    
    查询动作执行历史记录，支持分页和过滤。
    
    Args:
        conversation_id: 对话 ID 过滤
        status: 状态过滤
        action_type: 类型过滤
        page: 页码
        page_size: 每页数量
        service: 动作服务
    
    Returns:
        动作历史列表响应
    """
    try:
        offset = (page - 1) * page_size
        
        result = await service.get_action_history(
            conversation_id=conversation_id,
            status=status,
            action_type=action_type,
            limit=page_size,
            offset=offset,
        )
        
        return ActionHistoryListResponse(
            success=True,
            message="获取动作历史成功",
            data=result,
            total=len(result),  # 实际应该查询总数
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"获取动作历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取动作历史失败: {str(e)}",
        )


@router.get("/pending", response_model=PendingConfirmationsResponse)
async def get_pending_confirmations(
    service: ActionService = Depends(get_action_service),
) -> PendingConfirmationsResponse:
    """
    获取待确认动作列表
    
    查询所有等待用户确认的动作。
    
    Args:
        service: 动作服务
    
    Returns:
        待确认动作列表响应
    """
    try:
        result = await service.get_pending_confirmations()
        
        return PendingConfirmationsResponse(
            success=True,
            message="获取待确认动作成功",
            data=result,
            total=len(result),
        )
        
    except Exception as e:
        logger.error(f"获取待确认动作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取待确认动作失败: {str(e)}",
        )


@router.post("/{action_id}/cancel", response_model=DataResponse[dict])
async def cancel_action(
    action_id: int,
    service: ActionService = Depends(get_action_service),
) -> DataResponse[dict]:
    """
    取消动作
    
    取消待执行的动作。
    
    Args:
        action_id: 动作 ID
        service: 动作服务
    
    Returns:
        包含更新后动作信息的响应
    """
    try:
        logger.info(f"取消动作: action_id={action_id}")
        
        result = await service.cancel_action(action_id)
        
        return DataResponse(
            success=True,
            message="动作已取消",
            data=result,
        )
        
    except ValueError as e:
        logger.warning(f"取消动作参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"取消动作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消动作失败: {str(e)}",
        )


@router.post("/file", response_model=DataResponse[FileOperationResponse])
async def execute_file_operation(
    request: FileOperationRequest,
    service: ActionService = Depends(get_action_service),
) -> DataResponse[FileOperationResponse]:
    """
    执行文件操作
    
    执行文件读取、写入或删除操作。
    
    Args:
        request: 文件操作请求
        service: 动作服务
    
    Returns:
        包含操作结果的响应
    """
    try:
        logger.info(f"执行文件操作: {request.operation} {request.file_path}")
        
        result = await service.execute_file_operation(
            operation=request.operation,
            file_path=request.file_path,
            content=request.content,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
        )
        
        response = FileOperationResponse(
            action_id=result.get("action_id"),
            status=result["status"],
            result=result.get("result"),
            preview=result.get("preview"),
            message=result.get("message"),
        )
        
        return DataResponse(
            success=True,
            message="文件操作完成" if result["status"] != "awaiting_confirmation" else "操作等待确认",
            data=response,
        )
        
    except ValueError as e:
        logger.warning(f"文件操作参数错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"执行文件操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行文件操作失败: {str(e)}",
        )
