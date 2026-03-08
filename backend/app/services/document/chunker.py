"""
文本分块算法模块
实现智能文本分块策略，支持段落分块、语义边界分块和重叠窗口
"""
import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from app.core.logger import logger


class ChunkStrategy(str, Enum):
    """
    分块策略枚举
    
    定义不同的文本分块策略
    """
    
    PARAGRAPH = "paragraph"  # 按段落分块
    SEMANTIC = "semantic"  # 按语义边界分块
    FIXED = "fixed"  # 固定大小分块
    HYBRID = "hybrid"  # 混合策略


@dataclass
class ChunkConfig:
    """
    分块配置类
    
    定义文本分块的可配置参数
    """
    
    # 分块大小（字符数）
    chunk_size: int = 500
    
    # 重叠大小（字符数）
    chunk_overlap: int = 50
    
    # 最小分块大小
    min_chunk_size: int = 100
    
    # 最大分块大小
    max_chunk_size: int = 1000
    
    # 分块策略
    strategy: ChunkStrategy = ChunkStrategy.HYBRID
    
    # 是否保留标题结构
    preserve_headers: bool = True
    
    # 段落分隔符正则
    paragraph_separator: str = r"\n\s*\n"
    
    # 句子分隔符正则
    sentence_separator: str = r"[。！？.!?]"


@dataclass
class TextChunk:
    """
    文本分块数据类
    
    存储单个文本分块的信息
    """
    
    # 分块内容
    content: str
    
    # 分块索引
    chunk_index: int
    
    # 起始字符位置
    start_char: int
    
    # 结束字符位置
    end_char: int
    
    # 分块哈希
    chunk_hash: str = field(default="")
    
    # 元数据（包含页码、标题等）
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后计算哈希"""
        if not self.chunk_hash:
            self.chunk_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """
        计算分块内容的哈希值
        
        Returns:
            SHA256 哈希字符串
        """
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]
    
    @property
    def char_count(self) -> int:
        """
        获取字符数
        
        Returns:
            分块内容的字符数
        """
        return len(self.content)
    
    @property
    def token_estimate(self) -> int:
        """
        估算 Token 数量
        
        使用简单的启发式方法估算 Token 数量
        中文约 1.5 字符/token，英文约 4 字符/token
        
        Returns:
            估算的 Token 数量
        """
        # 简单估算：中文字符数 / 1.5 + 英文单词数
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", self.content))
        other_chars = len(self.content) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)


class TextChunker:
    """
    文本分块器
    
    实现多种智能文本分块策略
    """
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        初始化文本分块器
        
        Args:
            config: 分块配置，如果为 None 则使用默认配置
        """
        self.config = config or ChunkConfig()
        logger.info(f"初始化文本分块器，策略: {self.config.strategy.value}")
    
    def chunk(self, text: str, metadata: Optional[dict] = None) -> List[TextChunk]:
        """
        对文本进行分块
        
        根据配置的策略选择合适的分块方法
        
        Args:
            text: 待分块的文本内容
            metadata: 附加元数据
            
        Returns:
            文本分块列表
        """
        if not text or not text.strip():
            logger.warning("文本内容为空，返回空分块列表")
            return []
        
        base_metadata = metadata or {}
        
        # 根据策略选择分块方法
        if self.config.strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(text)
        elif self.config.strategy == ChunkStrategy.SEMANTIC:
            chunks = self._chunk_by_semantic(text)
        elif self.config.strategy == ChunkStrategy.FIXED:
            chunks = self._chunk_fixed(text)
        else:  # HYBRID
            chunks = self._chunk_hybrid(text)
        
        # 添加元数据并创建 TextChunk 对象
        result = []
        for i, (content, start, end, chunk_meta) in enumerate(chunks):
            combined_meta = {**base_metadata, **chunk_meta}
            chunk = TextChunk(
                content=content,
                chunk_index=i,
                start_char=start,
                end_char=end,
                metadata=combined_meta,
            )
            result.append(chunk)
        
        logger.info(f"文本分块完成，共 {len(result)} 个分块")
        return result
    
    def _chunk_by_paragraph(self, text: str) -> List[tuple]:
        """
        按段落分块
        
        将文本按段落分隔，然后合并到合适的大小
        
        Args:
            text: 待分块的文本
            
        Returns:
            分块元组列表 (content, start, end, metadata)
        """
        # 分割段落
        paragraphs = re.split(self.config.paragraph_separator, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        current_start = 0
        char_pos = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # 如果单个段落超过最大大小，需要进一步分割
            if para_size > self.config.max_chunk_size:
                # 先保存当前累积的分块
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append((
                        chunk_text,
                        current_start,
                        char_pos,
                        {"type": "paragraph"},
                    ))
                    current_chunk = []
                    current_size = 0
                
                # 分割大段落
                sub_chunks = self._split_large_paragraph(para, char_pos)
                chunks.extend(sub_chunks)
                current_start = char_pos + para_size + 2  # +2 for paragraph separator
            else:
                # 检查是否需要开始新分块
                if current_size + para_size > self.config.chunk_size and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append((
                        chunk_text,
                        current_start,
                        char_pos,
                        {"type": "paragraph"},
                    ))
                    current_chunk = []
                    current_size = 0
                    current_start = char_pos
                
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for separator
            
            char_pos += para_size + 2  # 更新字符位置
        
        # 处理最后一个分块
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append((
                chunk_text,
                current_start,
                char_pos,
                {"type": "paragraph"},
            ))
        
        return chunks
    
    def _chunk_by_semantic(self, text: str) -> List[tuple]:
        """
        按语义边界分块
        
        尝试在句子边界处分割，保持语义完整性
        
        Args:
            text: 待分块的文本
            
        Returns:
            分块元组列表 (content, start, end, metadata)
        """
        # 找到所有句子边界
        sentence_ends = list(re.finditer(self.config.sentence_separator, text))
        
        chunks = []
        current_start = 0
        current_size = 0
        last_boundary = 0
        
        for match in sentence_ends:
            boundary = match.end()
            segment_size = boundary - current_start
            
            if segment_size >= self.config.chunk_size:
                # 达到分块大小，在此边界分割
                chunk_text = text[current_start:boundary].strip()
                if len(chunk_text) >= self.config.min_chunk_size:
                    chunks.append((
                        chunk_text,
                        current_start,
                        boundary,
                        {"type": "semantic"},
                    ))
                current_start = boundary
                current_size = 0
            else:
                current_size = segment_size
            
            last_boundary = boundary
        
        # 处理剩余文本
        if current_start < len(text):
            remaining = text[current_start:].strip()
            if len(remaining) >= self.config.min_chunk_size:
                chunks.append((
                    remaining,
                    current_start,
                    len(text),
                    {"type": "semantic"},
                ))
        
        return chunks
    
    def _chunk_fixed(self, text: str) -> List[tuple]:
        """
        固定大小分块
        
        按固定字符数分块，支持重叠窗口
        
        Args:
            text: 待分块的文本
            
        Returns:
            分块元组列表 (content, start, end, metadata)
        """
        chunks = []
        text_len = len(text)
        start = 0
        chunk_index = 0
        
        while start < text_len:
            end = min(start + self.config.chunk_size, text_len)
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append((
                    chunk_text,
                    start,
                    end,
                    {"type": "fixed", "chunk_index": chunk_index},
                ))
            
            # 计算下一个起始位置（考虑重叠）
            start = end - self.config.chunk_overlap
            if start >= text_len:
                break
            chunk_index += 1
        
        return chunks
    
    def _chunk_hybrid(self, text: str) -> List[tuple]:
        """
        混合策略分块
        
        结合段落和语义边界，优先保持段落完整性
        
        Args:
            text: 待分块的文本
            
        Returns:
            分块元组列表 (content, start, end, metadata)
        """
        # 首先尝试按段落分块
        paragraphs = re.split(self.config.paragraph_separator, text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk_parts = []
        current_size = 0
        current_start = 0
        char_pos = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # 大段落需要进一步分割
            if para_size > self.config.max_chunk_size:
                # 先保存当前累积的内容
                if current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunks.append((
                        chunk_text,
                        current_start,
                        char_pos,
                        {"type": "hybrid"},
                    ))
                    current_chunk_parts = []
                    current_size = 0
                
                # 按语义边界分割大段落
                sub_chunks = self._split_by_semantic_boundary(
                    para, char_pos, self.config.max_chunk_size
                )
                chunks.extend(sub_chunks)
                current_start = char_pos + para_size + 2
                char_pos = current_start
            else:
                # 检查是否需要开始新分块
                new_size = current_size + para_size + 2
                if new_size > self.config.chunk_size and current_chunk_parts:
                    # 保存当前分块
                    chunk_text = "\n\n".join(current_chunk_parts)
                    chunks.append((
                        chunk_text,
                        current_start,
                        char_pos,
                        {"type": "hybrid"},
                    ))
                    
                    # 开始新分块，保留重叠内容
                    if self.config.chunk_overlap > 0 and len(current_chunk_parts) > 1:
                        # 保留最后一个段落作为重叠
                        overlap_para = current_chunk_parts[-1]
                        current_chunk_parts = [overlap_para, para]
                        current_size = len(overlap_para) + para_size + 2
                        current_start = char_pos - len(overlap_para) - 2
                    else:
                        current_chunk_parts = [para]
                        current_size = para_size
                        current_start = char_pos
                else:
                    current_chunk_parts.append(para)
                    current_size = new_size
                
                char_pos += para_size + 2
        
        # 处理最后一个分块
        if current_chunk_parts:
            chunk_text = "\n\n".join(current_chunk_parts)
            chunks.append((
                chunk_text,
                current_start,
                char_pos,
                {"type": "hybrid"},
            ))
        
        return self._apply_overlap(chunks)
    
    def _split_large_paragraph(self, text: str, start_pos: int) -> List[tuple]:
        """
        分割大段落
        
        将超过最大大小限制的段落按语义边界分割
        
        Args:
            text: 段落文本
            start_pos: 起始位置
            
        Returns:
            分块元组列表
        """
        return self._split_by_semantic_boundary(text, start_pos, self.config.max_chunk_size)
    
    def _split_by_semantic_boundary(
        self, text: str, start_pos: int, max_size: int
    ) -> List[tuple]:
        """
        按语义边界分割文本
        
        Args:
            text: 待分割的文本
            start_pos: 起始位置
            max_size: 最大分块大小
            
        Returns:
            分块元组列表
        """
        chunks = []
        text_len = len(text)
        current_start = 0
        
        while current_start < text_len:
            # 计算当前分块的结束位置
            end = min(current_start + max_size, text_len)
            
            # 如果不是文本末尾，尝试在句子边界处分割
            if end < text_len:
                # 在结束位置附近寻找句子边界
                search_start = max(current_start + max_size - 100, current_start)
                search_text = text[search_start:end + 50]
                
                # 寻找最后一个句子结束符
                last_sentence_end = -1
                for match in re.finditer(self.config.sentence_separator, search_text):
                    last_sentence_end = match.end()
                
                if last_sentence_end > 0:
                    end = search_start + last_sentence_end
            
            chunk_text = text[current_start:end].strip()
            if chunk_text:
                chunks.append((
                    chunk_text,
                    start_pos + current_start,
                    start_pos + end,
                    {"type": "semantic_split"},
                ))
            
            # 添加重叠
            current_start = end - self.config.chunk_overlap
            if current_start <= chunks[-1][1] - start_pos if chunks else 0:
                current_start = end
        
        return chunks
    
    def _apply_overlap(self, chunks: List[tuple]) -> List[tuple]:
        """
        应用重叠窗口到分块列表
        
        Args:
            chunks: 原始分块列表
            
        Returns:
            应用重叠后的分块列表
        """
        if self.config.chunk_overlap <= 0 or len(chunks) <= 1:
            return chunks
        
        result = []
        for i, (content, start, end, meta) in enumerate(chunks):
            if i > 0 and self.config.chunk_overlap > 0:
                # 从前一个分块获取重叠内容
                prev_content = chunks[i - 1][0]
                overlap_size = min(self.config.chunk_overlap, len(prev_content))
                
                # 从前一个分块的末尾获取重叠文本
                # 尝试在句子边界处分割
                overlap_text = prev_content[-overlap_size:]
                
                # 检查是否已经有重叠（避免重复）
                if not content.startswith(overlap_text[-50:]):
                    # 添加重叠内容
                    new_content = overlap_text + content
                    new_start = start - overlap_size
                    result.append((new_content, new_start, end, meta))
                else:
                    result.append((content, start, end, meta))
            else:
                result.append((content, start, end, meta))
        
        return result
