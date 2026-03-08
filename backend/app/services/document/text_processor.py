"""
文本文档处理器
处理 Markdown 和 TXT 纯文本文档，支持编码检测和结构保留
"""
import asyncio
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.logger import logger

# 延迟导入编码检测库
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    logger.warning("chardet 未安装，编码检测功能将受限。请运行: pip install chardet")


@dataclass
class TextSection:
    """
    文本段落数据类
    
    存储文档中的一个段落（如 Markdown 的章节）
    """
    
    # 段落标题
    title: str
    
    # 段落级别（Markdown 标题级别，1-6）
    level: int
    
    # 段落内容
    content: str
    
    # 起始位置
    start_pos: int
    
    # 结束位置
    end_pos: int
    
    # 段落元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TextExtractionResult:
    """
    文本提取结果数据类
    
    存储文本文档的提取结果
    """
    
    # 完整文本内容
    full_text: str
    
    # 文档段落列表
    sections: List[TextSection]
    
    # 文档元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 检测到的编码
    encoding: str = "utf-8"
    
    # 总字符数
    total_chars: int = 0
    
    # 提取是否成功
    success: bool = True
    
    # 错误信息
    error_message: str = ""


class TextProcessor:
    """
    文本文档处理器
    
    处理 Markdown 和 TXT 纯文本文件，支持编码检测和结构解析
    """
    
    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".text"}
    
    # Markdown 标题正则
    MARKDOWN_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", re.MULTILINE)
    
    # 常见编码列表（按优先级排序）
    COMMON_ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "big5", "latin-1"]
    
    def __init__(self, preserve_structure: bool = True, detect_encoding: bool = True):
        """
        初始化文本处理器
        
        Args:
            preserve_structure: 是否保留文档结构（标题层级）
            detect_encoding: 是否自动检测文件编码
        """
        self.preserve_structure = preserve_structure
        self.detect_encoding = detect_encoding and CHARDET_AVAILABLE
        logger.info(f"文本处理器初始化完成，编码检测: {'启用' if self.detect_encoding else '禁用'}")
    
    async def extract_text(self, file_path: str) -> TextExtractionResult:
        """
        异步提取文本文档内容
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文本提取结果
        """
        # 在线程池中执行同步的文本处理
        return await asyncio.to_thread(self._extract_text_sync, file_path)
    
    def _extract_text_sync(self, file_path: str) -> TextExtractionResult:
        """
        同步提取文本文档内容
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文本提取结果
        """
        path = Path(file_path)
        
        # 验证文件
        if not path.exists():
            return TextExtractionResult(
                full_text="",
                sections=[],
                success=False,
                error_message=f"文件不存在: {file_path}",
            )
        
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return TextExtractionResult(
                full_text="",
                sections=[],
                success=False,
                error_message=f"不支持的文件类型: {path.suffix}",
            )
        
        try:
            # 读取文件并检测编码
            content, encoding = self._read_file_with_encoding(file_path)
            
            # 提取文档结构
            if self.preserve_structure and path.suffix.lower() in {".md", ".markdown"}:
                sections = self._parse_markdown_structure(content)
            else:
                sections = self._parse_plain_text_structure(content)
            
            # 提取元数据
            metadata = self._extract_metadata(content, path)
            
            logger.info(
                f"文本提取完成: {file_path}, 编码: {encoding}, "
                f"{len(content)} 字符, {len(sections)} 个段落"
            )
            
            return TextExtractionResult(
                full_text=content,
                sections=sections,
                metadata=metadata,
                encoding=encoding,
                total_chars=len(content),
                success=True,
            )
            
        except Exception as e:
            logger.error(f"文本提取失败: {file_path}, 错误: {str(e)}")
            return TextExtractionResult(
                full_text="",
                sections=[],
                success=False,
                error_message=str(e),
            )
    
    def _read_file_with_encoding(self, file_path: str) -> Tuple[str, str]:
        """
        使用自动检测的编码读取文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            (文件内容, 使用的编码)
        """
        # 首先尝试自动检测编码
        if self.detect_encoding:
            detected_encoding = self._detect_encoding(file_path)
            if detected_encoding:
                try:
                    with open(file_path, "r", encoding=detected_encoding) as f:
                        content = f.read()
                    return content, detected_encoding
                except UnicodeDecodeError:
                    logger.warning(f"检测到的编码 {detected_encoding} 解码失败，尝试其他编码")
        
        # 尝试常见编码
        for encoding in self.COMMON_ENCODINGS:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                logger.info(f"使用编码 {encoding} 成功读取文件")
                return content, encoding
            except UnicodeDecodeError:
                continue
        
        # 最后尝试二进制模式读取并忽略错误
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        logger.warning(f"无法确定文件编码，使用 UTF-8 并忽略错误")
        return content, "utf-8"
    
    def _detect_encoding(self, file_path: str) -> Optional[str]:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的编码名称，如果检测失败返回 None
        """
        if not CHARDET_AVAILABLE:
            return None
        
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(10000)  # 读取前 10000 字节用于检测
            
            result = chardet.detect(raw_data)
            confidence = result.get("confidence", 0)
            encoding = result.get("encoding")
            
            if confidence > 0.7 and encoding:
                logger.info(f"检测到编码: {encoding} (置信度: {confidence:.2f})")
                return encoding.lower()
            
            return None
        except Exception as e:
            logger.warning(f"编码检测失败: {str(e)}")
            return None
    
    def _parse_markdown_structure(self, content: str) -> List[TextSection]:
        """
        解析 Markdown 文档结构
        
        Args:
            content: Markdown 文本内容
            
        Returns:
            段落列表
        """
        sections = []
        
        # 查找所有标题
        headers = list(self.MARKDOWN_HEADER_PATTERN.finditer(content))
        
        if not headers:
            # 没有标题，作为单个段落
            return [TextSection(
                title="",
                level=0,
                content=content.strip(),
                start_pos=0,
                end_pos=len(content),
                metadata={"type": "plain"},
            )]
        
        # 提取每个标题对应的内容
        for i, match in enumerate(headers):
            level = len(match.group(1))
            title = match.group(2).strip()
            start_pos = match.start()
            
            # 内容结束位置是下一个标题的开始位置或文档末尾
            if i + 1 < len(headers):
                end_pos = headers[i + 1].start()
            else:
                end_pos = len(content)
            
            # 提取内容（去掉标题行）
            section_content = content[start_pos:end_pos].strip()
            
            sections.append(TextSection(
                title=title,
                level=level,
                content=section_content,
                start_pos=start_pos,
                end_pos=end_pos,
                metadata={"type": "markdown", "header_level": level},
            ))
        
        return sections
    
    def _parse_plain_text_structure(self, content: str) -> List[TextSection]:
        """
        解析纯文本文档结构
        
        按段落（空行分隔）分割文本
        
        Args:
            content: 纯文本内容
            
        Returns:
            段落列表
        """
        sections = []
        
        # 按空行分割段落
        paragraphs = re.split(r"\n\s*\n", content)
        current_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 查找段落在原文中的位置
            start_pos = content.find(para, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(para)
            
            # 尝试检测是否为标题（短行、全大写等）
            is_title = len(para) < 100 and (
                para.isupper() or
                re.match(r"^[A-Z][^.!?]*$", para) is not None
            )
            
            sections.append(TextSection(
                title=para if is_title else "",
                level=1 if is_title else 0,
                content=para,
                start_pos=start_pos,
                end_pos=end_pos,
                metadata={"type": "paragraph"},
            ))
            
            current_pos = end_pos
        
        return sections
    
    def _extract_metadata(self, content: str, path: Path) -> Dict[str, Any]:
        """
        提取文档元数据
        
        Args:
            content: 文档内容
            path: 文件路径
            
        Returns:
            元数据字典
        """
        metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "file_type": "markdown" if path.suffix.lower() in {".md", ".markdown"} else "text",
        }
        
        # 尝试从 Markdown 提取 YAML front matter
        if path.suffix.lower() in {".md", ".markdown"}:
            front_matter = self._extract_front_matter(content)
            if front_matter:
                metadata["front_matter"] = front_matter
        
        # 统计信息
        lines = content.split("\n")
        metadata["line_count"] = len(lines)
        metadata["word_count"] = len(content.split())
        metadata["char_count"] = len(content)
        
        return metadata
    
    def _extract_front_matter(self, content: str) -> Optional[Dict[str, Any]]:
        """
        提取 Markdown YAML front matter
        
        Args:
            content: Markdown 内容
            
        Returns:
            front matter 字典，如果不存在返回 None
        """
        # 检查是否以 --- 开头
        if not content.startswith("---"):
            return None
        
        # 查找结束的 ---
        end_match = re.search(r"\n---\s*\n", content[3:])
        if not end_match:
            return None
        
        front_matter_text = content[3:end_match.start() + 3].strip()
        
        # 简单解析 YAML（不使用 yaml 库）
        result = {}
        for line in front_matter_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().strip('"\'')
        
        return result if result else None
    
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
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """
        检查文件是否为支持的文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为文本文件
        """
        path = Path(file_path)
        return path.suffix.lower() in TextProcessor.SUPPORTED_EXTENSIONS
    
    async def extract_with_structure(self, file_path: str) -> List[Dict[str, Any]]:
        """
        提取文本内容并返回带结构信息的列表
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            包含结构信息的字典列表
        """
        result = await self.extract_text(file_path)
        
        if not result.success:
            return []
        
        return [
            {
                "title": section.title,
                "level": section.level,
                "content": section.content,
                "start_pos": section.start_pos,
                "end_pos": section.end_pos,
                "metadata": section.metadata,
            }
            for section in result.sections
        ]
    
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        - 移除多余的空白字符
        - 规范化换行符
        - 移除控制字符
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除控制字符（保留换行和制表符）
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        
        # 规范化换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 移除行尾空白
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)
        
        # 移除连续多个空行（保留最多两个）
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        return text.strip()
