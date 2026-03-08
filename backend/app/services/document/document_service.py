"""
文档服务整合层
整合文档上传、解析、分块等功能，提供统一的文档处理接口
"""
import asyncio
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import logger
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.document_chunk import DocumentChunk
from app.services.document.chunker import ChunkConfig, ChunkStrategy, TextChunker
from app.services.document.pdf_processor import PDFProcessor
from app.services.document.text_processor import TextProcessor


class DocumentService:
    """
    文档服务类
    
    整合文档处理的完整流程：上传 -> 解析 -> 分块 -> 存储
    """
    
    # 支持的文件类型映射
    SUPPORTED_FILE_TYPES = {
        ".pdf": DocumentType.PDF,
        ".md": DocumentType.MARKDOWN,
        ".markdown": DocumentType.MARKDOWN,
        ".txt": DocumentType.TEXT,
        ".text": DocumentType.TEXT,
    }
    
    # 最大文件大小（50MB）
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(
        self,
        upload_dir: Optional[str] = None,
        chunk_config: Optional[ChunkConfig] = None,
    ):
        """
        初始化文档服务
        
        Args:
            upload_dir: 文件上传目录，默认为 data/uploads
            chunk_config: 分块配置
        """
        self.upload_dir = Path(upload_dir or "./data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunk_config = chunk_config or ChunkConfig(
            chunk_size=500,
            chunk_overlap=50,
            strategy=ChunkStrategy.HYBRID,
        )
        
        # 初始化处理器
        self.pdf_processor = PDFProcessor(preserve_structure=True)
        self.text_processor = TextProcessor(preserve_structure=True, detect_encoding=True)
        self.chunker = TextChunker(self.chunk_config)
        
        logger.info(f"文档服务初始化完成，上传目录: {self.upload_dir}")
    
    async def save_upload_file(
        self,
        file_content: bytes,
        filename: str,
    ) -> Tuple[Path, str, DocumentType]:
        """
        保存上传的文件
        
        Args:
            file_content: 文件内容（字节）
            filename: 原始文件名
            
        Returns:
            (保存路径, 文件哈希, 文件类型)
            
        Raises:
            ValueError: 文件验证失败
        """
        # 验证文件大小
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过限制 ({self.MAX_FILE_SIZE / 1024 / 1024}MB)")
        
        # 获取文件扩展名
        ext = Path(filename).suffix.lower()
        
        # 验证文件类型
        if ext not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(
                f"不支持的文件类型: {ext}。"
                f"支持的类型: {', '.join(self.SUPPORTED_FILE_TYPES.keys())}"
            )
        
        # 计算文件哈希
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 生成唯一文件名（使用哈希避免冲突）
        safe_filename = f"{file_hash[:16]}_{filename}"
        save_path = self.upload_dir / safe_filename
        
        # 保存文件
        with open(save_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"文件保存成功: {save_path}")
        
        return save_path, file_hash, self.SUPPORTED_FILE_TYPES[ext]
    
    async def process_document(
        self,
        document: Document,
        db: AsyncSession,
    ) -> bool:
        """
        处理文档（解析 + 分块 + 存储）
        
        Args:
            document: 文档模型实例
            db: 数据库会话
            
        Returns:
            处理是否成功
        """
        try:
            # 更新状态为处理中
            document.status = DocumentStatus.PROCESSING
            await db.commit()
            
            # 根据文件类型选择处理器
            if document.file_type == DocumentType.PDF:
                result = await self.pdf_processor.extract_text(document.file_path)
            else:
                result = await self.text_processor.extract_text(document.file_path)
            
            if not result.success:
                document.status = DocumentStatus.FAILED
                document.error_message = result.error_message
                await db.commit()
                return False
            
            # 对文本进行分块
            metadata = {
                "file_type": document.file_type.value,
                "encoding": getattr(result, "encoding", "utf-8"),
            }
            
            # 添加 PDF 特定元数据
            if document.file_type == DocumentType.PDF and hasattr(result, "metadata"):
                metadata["pdf_metadata"] = result.metadata
            
            chunks = self.chunker.chunk(result.full_text, metadata)
            
            # 存储分块到数据库
            await self._save_chunks(document, chunks, db)
            
            # 更新文档状态
            document.status = DocumentStatus.COMPLETED
            document.chunk_count = len(chunks)
            document.summary = result.full_text[:500] if result.full_text else None
            
            # 存储元数据
            document.metadata = json.dumps(metadata, ensure_ascii=False)
            
            await db.commit()
            
            logger.info(f"文档处理完成: {document.filename}, 分块数: {len(chunks)}")
            return True
            
        except Exception as e:
            logger.error(f"文档处理失败: {document.filename}, 错误: {str(e)}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await db.commit()
            return False
    
    async def _save_chunks(
        self,
        document: Document,
        chunks: List[Any],
        db: AsyncSession,
    ) -> None:
        """
        保存文档分块到数据库
        
        Args:
            document: 文档模型
            chunks: 分块列表
            db: 数据库会话
        """
        # 删除已有的分块（如果存在）
        await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
        
        # 创建新的分块记录
        for chunk in chunks:
            db_chunk = DocumentChunk(
                document_id=document.id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                chunk_hash=chunk.chunk_hash,
                token_count=chunk.token_estimate,
                char_count=chunk.char_count,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=json.dumps(chunk.metadata, ensure_ascii=False) if chunk.metadata else None,
            )
            db.add(db_chunk)
        
        await db.flush()
    
    async def create_document_record(
        self,
        filename: str,
        file_path: str,
        file_type: DocumentType,
        file_size: int,
        file_hash: str,
        db: AsyncSession,
        title: Optional[str] = None,
    ) -> Document:
        """
        创建文档数据库记录
        
        Args:
            filename: 文件名
            file_path: 文件路径
            file_type: 文件类型
            file_size: 文件大小
            file_hash: 文件哈希
            db: 数据库会话
            title: 文档标题
            
        Returns:
            创建的文档实例
        """
        document = Document(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            file_hash=file_hash,
            status=DocumentStatus.PENDING,
            title=title or Path(filename).stem,
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"创建文档记录: {document.id} - {filename}")
        return document
    
    async def get_document(
        self,
        document_id: int,
        db: AsyncSession,
    ) -> Optional[Document]:
        """
        获取文档详情
        
        Args:
            document_id: 文档 ID
            db: 数据库会话
            
        Returns:
            文档实例，如果不存在返回 None
        """
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def get_documents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: Optional[DocumentStatus] = None,
        file_type: Optional[DocumentType] = None,
    ) -> Tuple[List[Document], int]:
        """
        获取文档列表
        
        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 返回数量
            status: 状态过滤
            file_type: 文件类型过滤
            
        Returns:
            (文档列表, 总数)
        """
        # 构建查询
        query = select(Document)
        count_query = select(Document)
        
        if status:
            query = query.where(Document.status == status)
            count_query = count_query.where(Document.status == status)
        
        if file_type:
            query = query.where(Document.file_type == file_type)
            count_query = count_query.where(Document.file_type == file_type)
        
        # 排序和分页
        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        
        # 执行查询
        result = await db.execute(query)
        documents = list(result.scalars().all())
        
        # 获取总数
        from sqlalchemy import func
        count_result = await db.execute(select(func.count()).select_from(count_query))
        total = count_result.scalar() or 0
        
        return documents, total
    
    async def delete_document(
        self,
        document_id: int,
        db: AsyncSession,
    ) -> bool:
        """
        删除文档
        
        Args:
            document_id: 文档 ID
            db: 数据库会话
            
        Returns:
            删除是否成功
        """
        document = await self.get_document(document_id, db)
        
        if not document:
            return False
        
        # 删除文件
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"删除文件: {file_path}")
        except Exception as e:
            logger.warning(f"删除文件失败: {str(e)}")
        
        # 删除数据库记录（级联删除分块）
        await db.delete(document)
        await db.commit()
        
        logger.info(f"删除文档: {document_id}")
        return True
    
    async def get_document_chunks(
        self,
        document_id: int,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DocumentChunk]:
        """
        获取文档分块列表
        
        Args:
            document_id: 文档 ID
            db: 数据库会话
            skip: 跳过数量
            limit: 返回数量
            
        Returns:
            分块列表
        """
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def check_duplicate(
        self,
        file_hash: str,
        db: AsyncSession,
    ) -> Optional[Document]:
        """
        检查文件是否已存在（基于哈希去重）
        
        Args:
            file_hash: 文件哈希
            db: 数据库会话
            
        Returns:
            已存在的文档实例，如果不存在返回 None
        """
        result = await db.execute(
            select(Document).where(Document.file_hash == file_hash)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_file_type(filename: str) -> Optional[DocumentType]:
        """
        根据文件名获取文件类型
        
        Args:
            filename: 文件名
            
        Returns:
            文件类型，如果不支持返回 None
        """
        ext = Path(filename).suffix.lower()
        return DocumentService.SUPPORTED_FILE_TYPES.get(ext)
