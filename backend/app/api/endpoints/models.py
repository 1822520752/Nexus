"""
模型管理 API 端点
提供 AI 模型的完整 CRUD 操作、状态检测和测试接口
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.model_config import ModelConfig
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigListResponse,
    ModelConfigResponse,
    ModelConfigUpdate,
)
from app.services.model.model_service import ModelService

router = APIRouter()


# ==================== 依赖注入 ====================

def get_model_service(db: AsyncSession = Depends(get_db)) -> ModelService:
    """
    获取模型服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        ModelService 实例
    """
    return ModelService(db)


# ==================== 模型列表接口 ====================

@router.get("/", response_model=ModelConfigListResponse)
async def list_models(
    provider: Optional[str] = Query(None, description="按提供商筛选"),
    model_type: Optional[str] = Query(None, description="按模型类型筛选"),
    is_active: Optional[bool] = Query(None, description="按启用状态筛选"),
    include_inactive: bool = Query(False, description="是否包含未启用的模型"),
    service: ModelService = Depends(get_model_service),
) -> ModelConfigListResponse:
    """
    获取模型配置列表
    
    Args:
        provider: 按提供商筛选
        model_type: 按模型类型筛选
        is_active: 按启用状态筛选
        include_inactive: 是否包含未启用的模型
        service: 模型服务实例
        
    Returns:
        模型配置列表
    """
    models = await service.list_models(
        provider=provider,
        model_type=model_type,
        is_active=is_active,
        include_inactive=include_inactive,
    )
    
    return ModelConfigListResponse(
        items=[ModelConfigResponse.model_validate(m) for m in models],
        total=len(models),
    )


@router.get("/providers", response_model=Dict[str, Any])
async def get_supported_providers(
    service: ModelService = Depends(get_model_service),
) -> Dict[str, Any]:
    """
    获取支持的提供商列表
    
    Args:
        service: 模型服务实例
        
    Returns:
        提供商配置信息
    """
    providers = service.get_supported_providers()
    return {
        "providers": providers,
        "total": len(providers),
    }


@router.get("/providers/{provider}/models", response_model=List[Dict[str, Any]])
async def get_provider_models(
    provider: str,
    service: ModelService = Depends(get_model_service),
) -> List[Dict[str, Any]]:
    """
    获取指定提供商的可用模型列表
    
    Args:
        provider: 提供商名称
        service: 模型服务实例
        
    Returns:
        可用模型列表
        
    Raises:
        HTTPException: 提供商不支持时抛出 400
    """
    # 验证提供商
    provider_config = service.get_provider_config(provider)
    if not provider_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的提供商: {provider}",
        )
    
    models = await service.get_available_models(provider)
    return models


# ==================== 模型 CRUD 接口 ====================

@router.post("/", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelConfigCreate,
    service: ModelService = Depends(get_model_service),
) -> ModelConfig:
    """
    创建新的模型配置
    
    Args:
        model_data: 模型创建数据
        service: 模型服务实例
        
    Returns:
        创建的模型配置
        
    Raises:
        HTTPException: 参数验证失败时抛出 400
    """
    # 验证配置
    is_valid, error_msg = service.validate_model_config(
        provider=model_data.provider,
        name=model_data.name,
        api_key=model_data.api_key,
        base_url=model_data.base_url,
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    
    try:
        model = await service.create_model(
            name=model_data.name,
            provider=model_data.provider,
            api_key=model_data.api_key,
            base_url=model_data.base_url,
            model_type=model_data.model_type,
            is_default=model_data.is_default,
            max_tokens=model_data.max_tokens,
            temperature=model_data.temperature,
            context_window=model_data.context_window,
            config=model_data.config,
        )
        
        logger.info(f"创建模型配置成功: id={model.id}, name={model.name}")
        return model
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"创建模型配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建模型配置失败: {str(e)}",
        )


@router.get("/{model_id}", response_model=ModelConfigResponse)
async def get_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> ModelConfig:
    """
    获取单个模型配置详情
    
    Args:
        model_id: 模型配置 ID
        service: 模型服务实例
        
    Returns:
        模型配置详情
        
    Raises:
        HTTPException: 模型不存在时抛出 404
    """
    model = await service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型配置 {model_id} 不存在",
        )
    
    return model


@router.put("/{model_id}", response_model=ModelConfigResponse)
async def update_model(
    model_id: int,
    model_data: ModelConfigUpdate,
    service: ModelService = Depends(get_model_service),
) -> ModelConfig:
    """
    更新模型配置
    
    Args:
        model_id: 模型配置 ID
        model_data: 更新数据
        service: 模型服务实例
        
    Returns:
        更新后的模型配置
        
    Raises:
        HTTPException: 模型不存在时抛出 404
    """
    model = await service.update_model(
        model_id=model_id,
        name=model_data.name,
        api_key=model_data.api_key,
        base_url=model_data.base_url,
        is_default=model_data.is_default,
        is_active=model_data.is_active,
        max_tokens=model_data.max_tokens,
        temperature=model_data.temperature,
        context_window=model_data.context_window,
        config=model_data.config,
    )
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型配置 {model_id} 不存在",
        )
    
    logger.info(f"更新模型配置成功: id={model_id}")
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> None:
    """
    删除模型配置
    
    Args:
        model_id: 模型配置 ID
        service: 模型服务实例
        
    Raises:
        HTTPException: 模型不存在时抛出 404
    """
    success = await service.delete_model(model_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型配置 {model_id} 不存在",
        )
    
    logger.info(f"删除模型配置成功: id={model_id}")


# ==================== 默认模型接口 ====================

@router.post("/{model_id}/set-default", response_model=ModelConfigResponse)
async def set_default_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> ModelConfig:
    """
    设置默认模型
    
    Args:
        model_id: 模型配置 ID
        service: 模型服务实例
        
    Returns:
        更新后的模型配置
        
    Raises:
        HTTPException: 模型不存在时抛出 404
    """
    model = await service.set_default_model(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型配置 {model_id} 不存在",
        )
    
    logger.info(f"设置默认模型成功: id={model_id}, name={model.name}")
    return model


@router.get("/default", response_model=ModelConfigResponse)
async def get_default_model(
    service: ModelService = Depends(get_model_service),
) -> ModelConfig:
    """
    获取默认模型配置
    
    Args:
        service: 模型服务实例
        
    Returns:
        默认模型配置
        
    Raises:
        HTTPException: 没有默认模型时抛出 404
    """
    model = await service.get_default_model()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有可用的默认模型",
        )
    
    return model


# ==================== 模型状态接口 ====================

@router.get("/{model_id}/status", response_model=Dict[str, Any])
async def get_model_status(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> Dict[str, Any]:
    """
    获取模型状态
    
    Args:
        model_id: 模型配置 ID
        service: 模型服务实例
        
    Returns:
        模型状态信息
    """
    status_info = await service.check_model_status(model_id)
    return status_info


@router.post("/{model_id}/test", response_model=Dict[str, Any])
async def test_model_connection(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> Dict[str, Any]:
    """
    测试模型连接
    
    Args:
        model_id: 模型配置 ID
        service: 模型服务实例
        
    Returns:
        测试结果
    """
    result = await service.test_model_connection(model_id)
    return result


# ==================== 模型启用/禁用接口 ====================

@router.post("/{model_id}/toggle", response_model=ModelConfigResponse)
async def toggle_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> ModelConfig:
    """
    切换模型启用状态
    
    Args:
        model_id: 模型配置 ID
        service: 模型服务实例
        
    Returns:
        更新后的模型配置
        
    Raises:
        HTTPException: 模型不存在时抛出 404
    """
    model = await service.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型配置 {model_id} 不存在",
        )
    
    model = await service.update_model(
        model_id=model_id,
        is_active=not model.is_active,
    )
    
    logger.info(f"切换模型状态: id={model_id}, is_active={model.is_active}")
    return model
