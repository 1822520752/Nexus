"""
文档管理 API 端点
提供文档上传、查询、删除等接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.document import DocumentStatus, DocumentType
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.document.document_service import DocumentService

# 创建路由器
router = APIRouter(prefix="/documents", tags=["文档管理"])

# 创建文档服务实例
document_service = DocumentService()


@router.post(
    "/upload",
    response_model=List[DocumentUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="上传文档",
    description="支持多文件上传，支持的文件类型：PDF、Markdown、TXT",
)
async def upload_documents(
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    db: AsyncSession = Depends(get_db),
) -> List[DocumentUploadResponse]:
    """
    上传文档
    
    支持多文件上传，文件类型验证（pdf/md/txt）
    
    Args:
        files: 上传的文件列表
        db: 数据库会话
        
    Returns:
        上传响应列表
        
    Raises:
        HTTPException: 上传失败时抛出
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要上传的文件",
        )
    
    results = []
    
    for file in files:
        try:
            # 读取文件内容
            content = await file.read()
            
            # 验证文件类型
            file_type = document_service.get_file_type(file.filename or "unknown")
            if file_type is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的文件类型: {file.filename}",
                )
            
            # 保存文件
            save_path, file_hash, doc_type = await document_service.save_upload_file(
                content,
                file.filename or "unknown",
            )
            
            # 检查是否重复
            existing_doc = await document_service.check_duplicate(file_hash, db)
            if existing_doc:
                results.append(DocumentUploadResponse(
                    id=existing_doc.id,
                    filename=file.filename or "unknown",
                    status=existing_doc.status,
                    message="文件已存在，跳过上传",
                ))
                continue
            
            # 创建文档记录
            document = await document_service.create_document_record(
                filename=file.filename or "unknown",
                file_path=str(save_path),
                file_type=doc_type,
                file_size=len(content),
                file_hash=file_hash,
                db=db,
            )
            
            # 异步处理文档（解析 + 分块）
            # 在后台执行，不阻塞响应
            import asyncio
            asyncio.create_task(
                _process_document_background(document.id, str(save_path))
            )
            
            results.append(DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                status=document.status,
                message="文档上传成功，正在处理中",
            ))
            
            logger.info(f"文件上传成功: {file.filename}, ID: {document.id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {file.filename}, 错误: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件上传失败: {str(e)}",
            )
    
    return results


async def _process_document_background(document_id: int, file_path: str) -> None:
    """
    后台处理文档任务
    
    Args:
        document_id: 文档 ID
        file_path: 文件路径
    """
    from app.core.database import get_db_context
    
    try:
        async with get_db_context() as db:
            document = await document_service.get_document(document_id, db)
            if document:
                await document_service.process_document(document, db)
                logger.info(f"后台文档处理完成: {document_id}")
    except Exception as e:
        logger.error(f"后台文档处理失败: {document_id}, 错误: {str(e)}")


@router.get(
    "",
    response_model=PaginatedResponse[DocumentResponse],
    summary="获取文档列表",
    description="分页获取文档列表，支持按状态和类型过滤",
)
async def get_documents(
    skip: int = Query(default=0, ge=0, description="跳过数量"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量"),
    status: Optional[DocumentStatus] = Query(default=None, description="状态过滤"),
    file_type: Optional[DocumentType] = Query(default=None, description="文件类型过滤"),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DocumentResponse]:
    """
    获取文档列表
    
    支持分页和过滤
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        status: 状态过滤
        file_type: 文件类型过滤
        db: 数据库会话
        
    Returns:
        分页文档列表
    """
    documents, total = await document_service.get_documents(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        file_type=file_type,
    )
    
    return PaginatedResponse(
        items=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="获取文档详情",
    description="获取指定文档的详细信息，包括分块内容",
)
async def get_document_detail(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """
    获取文档详情
    
    包含文档信息和分块列表
    
    Args:
        document_id: 文档 ID
        db: 数据库会话
        
    Returns:
        文档详情
        
    Raises:
        HTTPException: 文档不存在时抛出
    """
    document = await document_service.get_document(document_id, db)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )
    
    return DocumentDetailResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文档",
    description="删除指定文档及其分块",
)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    删除文档
    
    删除文档文件和数据库记录
    
    Args:
        document_id: 文档 ID
        db: 数据库会话
        
    Raises:
        HTTPException: 文档不存在时抛出
    """
    success = await document_service.delete_document(document_id, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )
    
    logger.info(f"文档删除成功: {document_id}")


@router.get(
    "/{document_id}/chunks",
    summary="获取文档分块",
    description="获取指定文档的分块列表",
)
async def get_document_chunks(
    document_id: int,
    skip: int = Query(default=0, ge=0, description="跳过数量"),
    limit: int = Query(default=100, ge=1, le=500, description="返回数量"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取文档分块列表
    
    Args:
        document_id: 文档 ID
        skip: 跳过数量
        limit: 返回数量
        db: 数据库会话
        
    Returns:
        分块列表
        
    Raises:
        HTTPException: 文档不存在时抛出
    """
    # 检查文档是否存在
    document = await document_service.get_document(document_id, db)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )
    
    chunks = await document_service.get_document_chunks(
        document_id=document_id,
        db=db,
        skip=skip,
        limit=limit,
    )
    
    return {
        "document_id": document_id,
        "total_chunks": document.chunk_count,
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "char_count": chunk.char_count,
                "token_count": chunk.token_count,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
            for chunk in chunks
        ],
    }


@router.post(
    "/{document_id}/reprocess",
    summary="重新处理文档",
    description="重新解析和分块指定文档",
)
async def reprocess_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    重新处理文档
    
    重新执行解析和分块操作
    
    Args:
        document_id: 文档 ID
        db: 数据库会话
        
    Returns:
        处理结果
        
    Raises:
        HTTPException: 文档不存在时抛出
    """
    document = await document_service.get_document(document_id, db)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {document_id}",
        )
    
    # 重置状态
    document.status = DocumentStatus.PENDING
    await db.commit()
    
    # 处理文档
    success = await document_service.process_document(document, db)
    
    if success:
        return {
            "message": "文档重新处理成功",
            "document_id": document_id,
            "status": document.status.value,
            "chunk_count": document.chunk_count,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {document.error_message}",
        )
