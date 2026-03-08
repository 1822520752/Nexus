"""
PDF 文档处理器
使用 PyMuPDF 提取 PDF 文本内容，支持多页 PDF 和保留文本结构
"""
import asyncio
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import logger

# 延迟导入 PyMuPDF，避免未安装时报错
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF 未安装，PDF 处理功能将不可用。请运行: pip install pymupdf")


@dataclass
class PDFPageContent:
    """
    PDF 页面内容数据类
    
    存储单个 PDF 页面的提取内容
    """
    
    # 页码（从 1 开始）
    page_number: int
    
    # 页面文本内容
    text: str
    
    # 页面元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 页面宽度
    width: float = 0.0
    
    # 页面高度
    height: float = 0.0
    
    # 文本块列表
    text_blocks: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PDFExtractionResult:
    """
    PDF 提取结果数据类
    
    存储整个 PDF 的提取结果
    """
    
    # 完整文本内容
    full_text: str
    
    # 各页内容
    pages: List[PDFPageContent]
    
    # 文档元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 总页数
    total_pages: int = 0
    
    # 总字符数
    total_chars: int = 0
    
    # 提取是否成功
    success: bool = True
    
    # 错误信息
    error_message: str = ""


class PDFProcessor:
    """
    PDF 文档处理器
    
    使用 PyMuPDF 提取 PDF 文本，支持多页处理和结构保留
    """
    
    # 支持的 PDF 文件扩展名
    SUPPORTED_EXTENSIONS = {".pdf"}
    
    def __init__(self, preserve_structure: bool = True, extract_images: bool = False):
        """
        初始化 PDF 处理器
        
        Args:
            preserve_structure: 是否保留文本结构（段落、标题等）
            extract_images: 是否提取图片（暂不支持 OCR）
        """
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF 未安装，无法使用 PDF 处理功能")
        
        self.preserve_structure = preserve_structure
        self.extract_images = extract_images
        logger.info("PDF 处理器初始化完成")
    
    async def extract_text(self, file_path: str) -> PDFExtractionResult:
        """
        异步提取 PDF 文本内容
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            PDF 提取结果
        """
        # 在线程池中执行同步的 PDF 处理
        return await asyncio.to_thread(self._extract_text_sync, file_path)
    
    def _extract_text_sync(self, file_path: str) -> PDFExtractionResult:
        """
        同步提取 PDF 文本内容
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            PDF 提取结果
        """
        path = Path(file_path)
        
        # 验证文件
        if not path.exists():
            return PDFExtractionResult(
                full_text="",
                pages=[],
                success=False,
                error_message=f"文件不存在: {file_path}",
            )
        
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return PDFExtractionResult(
                full_text="",
                pages=[],
                success=False,
                error_message=f"不支持的文件类型: {path.suffix}",
            )
        
        try:
            # 打开 PDF 文件
            doc = fitz.open(file_path)
            
            pages = []
            all_text = []
            
            # 提取文档元数据
            doc_metadata = self._extract_metadata(doc)
            
            # 遍历所有页面
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_content = self._extract_page_content(page, page_num + 1)
                pages.append(page_content)
                all_text.append(page_content.text)
            
            # 关闭文档
            doc.close()
            
            # 合并所有文本
            full_text = "\n\n".join(all_text)
            
            logger.info(f"PDF 提取完成: {file_path}, 共 {len(pages)} 页, {len(full_text)} 字符")
            
            return PDFExtractionResult(
                full_text=full_text,
                pages=pages,
                metadata=doc_metadata,
                total_pages=len(pages),
                total_chars=len(full_text),
                success=True,
            )
            
        except Exception as e:
            logger.error(f"PDF 提取失败: {file_path}, 错误: {str(e)}")
            return PDFExtractionResult(
                full_text="",
                pages=[],
                success=False,
                error_message=str(e),
            )
    
    def _extract_page_content(self, page: "fitz.Page", page_number: int) -> PDFPageContent:
        """
        提取单个页面的内容
        
        Args:
            page: PyMuPDF 页面对象
            page_number: 页码
            
        Returns:
            页面内容
        """
        # 获取页面尺寸
        rect = page.rect
        width, height = rect.width, rect.height
        
        # 提取文本
        if self.preserve_structure:
            # 使用 "blocks" 模式保留结构
            text_blocks = page.get_text("blocks")
            text = self._format_blocks(text_blocks)
            
            # 转换文本块为可序列化格式
            formatted_blocks = [
                {
                    "bbox": list(block[:4]),
                    "text": block[4],
                    "block_no": block[5] if len(block) > 5 else 0,
                }
                for block in text_blocks
            ]
        else:
            # 使用简单文本模式
            text = page.get_text("text")
            formatted_blocks = []
        
        # 提取页面元数据
        page_metadata = {
            "page_number": page_number,
            "width": width,
            "height": height,
        }
        
        return PDFPageContent(
            page_number=page_number,
            text=text.strip(),
            metadata=page_metadata,
            width=width,
            height=height,
            text_blocks=formatted_blocks,
        )
    
    def _format_blocks(self, blocks: List[tuple]) -> str:
        """
        格式化文本块为可读文本
        
        Args:
            blocks: PyMuPDF 返回的文本块列表
            
        Returns:
            格式化后的文本
        """
        # 按位置排序（从上到下，从左到右）
        sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        
        lines = []
        prev_y1 = 0
        
        for block in sorted_blocks:
            # block 格式: (x0, y0, x1, y1, text, block_no, block_type)
            text = block[4].strip()
            if not text:
                continue
            
            y0 = block[1]
            
            # 检测段落分隔（垂直间距较大）
            if prev_y1 > 0 and (y0 - prev_y1) > 20:
                lines.append("")  # 添加空行表示段落分隔
            
            lines.append(text)
            prev_y1 = block[3]  # y1
        
        return "\n".join(lines)
    
    def _extract_metadata(self, doc: "fitz.Document") -> Dict[str, Any]:
        """
        提取 PDF 文档元数据
        
        Args:
            doc: PyMuPDF 文档对象
            
        Returns:
            文档元数据字典
        """
        metadata = doc.metadata or {}
        
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": len(doc),
        }
    
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        计算文件的 SHA256 哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            哈希字符串
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # 分块读取以处理大文件
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def is_pdf(file_path: str) -> bool:
        """
        检查文件是否为 PDF
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为 PDF 文件
        """
        path = Path(file_path)
        return path.suffix.lower() == ".pdf"
    
    async def extract_with_page_info(self, file_path: str) -> List[Dict[str, Any]]:
        """
        提取 PDF 内容并返回带页面信息的结构化数据
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            包含页面信息的字典列表
        """
        result = await self.extract_text(file_path)
        
        if not result.success:
            return []
        
        return [
            {
                "page_number": page.page_number,
                "text": page.text,
                "char_count": len(page.text),
                "metadata": page.metadata,
            }
            for page in result.pages
        ]
