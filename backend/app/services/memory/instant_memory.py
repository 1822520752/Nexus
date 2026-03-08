"""
瞬时记忆服务模块
实现滑动窗口上下文管理，支持 100K tokens 的上下文窗口
提供上下文压缩、摘要和 Token 计数功能
"""
import json
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


@dataclass
class MessageContext:
    """
    消息上下文数据类
    
    存储单条消息的完整上下文信息
    """
    role: str  # user, assistant, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含消息上下文的字典
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageContext":
        """
        从字典创建消息上下文
        
        Args:
            data: 包含消息数据的字典
            
        Returns:
            消息上下文实例
        """
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ContextSummary:
    """
    上下文摘要数据类
    
    存储压缩后的上下文摘要信息
    """
    summary_text: str
    original_token_count: int
    compressed_token_count: int
    key_points: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含摘要信息的字典
        """
        return {
            "summary_text": self.summary_text,
            "original_token_count": self.original_token_count,
            "compressed_token_count": self.compressed_token_count,
            "key_points": self.key_points,
            "entities": self.entities,
            "created_at": self.created_at,
        }


class TokenCounter:
    """
    Token 计数器类
    
    提供文本 Token 数量估算功能
    支持多种估算策略
    """
    
    # 平均每个 Token 对应的字符数（英文约 4 字符，中文约 1.5 字符）
    AVG_CHARS_PER_TOKEN_EN = 4.0
    AVG_CHARS_PER_TOKEN_ZH = 1.5
    
    @classmethod
    def count_tokens(cls, text: str, method: str = "hybrid") -> int:
        """
        计算 Token 数量
        
        Args:
            text: 待计算的文本
            method: 计算方法 (simple, chinese, hybrid)
            
        Returns:
            Token 数量估算值
        """
        if not text:
            return 0
        
        if method == "simple":
            # 简单估算：按空格分词
            return len(text.split())
        
        elif method == "chinese":
            # 中文优化估算
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / cls.AVG_CHARS_PER_TOKEN_ZH + 
                      other_chars / cls.AVG_CHARS_PER_TOKEN_EN)
        
        else:  # hybrid
            # 混合估算：考虑中英文混合情况
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            total_chars = len(text)
            
            if chinese_chars > total_chars * 0.3:
                # 中文为主
                return int(total_chars / cls.AVG_CHARS_PER_TOKEN_ZH)
            else:
                # 英文为主
                return int(total_chars / cls.AVG_CHARS_PER_TOKEN_EN)
    
    @classmethod
    def count_messages_tokens(cls, messages: List[MessageContext]) -> int:
        """
        计算消息列表的总 Token 数
        
        Args:
            messages: 消息列表
            
        Returns:
            总 Token 数量
        """
        total = 0
        for msg in messages:
            total += msg.token_count if msg.token_count > 0 else cls.count_tokens(msg.content)
            # 每条消息额外添加 4 个 token（角色标记等）
            total += 4
        return total


class ContextCompressor:
    """
    上下文压缩器类
    
    提供上下文压缩和摘要生成功能
    """
    
    # 压缩目标比例
    COMPRESSION_RATIO = 0.3
    
    # 关键信息提取模式
    KEY_PATTERNS = [
        r'重要[：:]\s*(.+)',
        r'关键[：:]\s*(.+)',
        r'注意[：:]\s*(.+)',
        r'结论[：:]\s*(.+)',
        r'总结[：:]\s*(.+)',
    ]
    
    @classmethod
    def extract_key_points(cls, text: str) -> List[str]:
        """
        提取关键信息点
        
        Args:
            text: 源文本
            
        Returns:
            关键信息点列表
        """
        key_points = []
        for pattern in cls.KEY_PATTERNS:
            matches = re.findall(pattern, text)
            key_points.extend(matches)
        
        # 去重并限制数量
        return list(dict.fromkeys(key_points))[:10]
    
    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """
        提取实体（人名、地名、组织名等）
        
        Args:
            text: 源文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 提取引号中的内容
        quoted = re.findall(r'[""「」『』]([^""「」『』]+)[""「」『』]', text)
        entities.extend(quoted)
        
        # 提取大写开头的英文词组
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized)
        
        # 去重并限制数量
        return list(dict.fromkeys(entities))[:20]
    
    @classmethod
    def compress_messages(
        cls,
        messages: List[MessageContext],
        target_tokens: int,
    ) -> Tuple[str, ContextSummary]:
        """
        压缩消息列表为摘要
        
        Args:
            messages: 待压缩的消息列表
            target_tokens: 目标 Token 数量
            
        Returns:
            压缩后的摘要文本和摘要对象
        """
        if not messages:
            return "", ContextSummary(
                summary_text="",
                original_token_count=0,
                compressed_token_count=0,
            )
        
        # 合并所有消息
        full_text = "\n".join([
            f"[{msg.role}]: {msg.content}" 
            for msg in messages
        ])
        
        original_tokens = TokenCounter.count_tokens(full_text)
        
        # 提取关键信息
        key_points = cls.extract_key_points(full_text)
        entities = cls.extract_entities(full_text)
        
        # 生成摘要
        summary_parts = []
        
        # 添加对话概要
        summary_parts.append(f"对话共 {len(messages)} 条消息，原始 {original_tokens} tokens")
        
        # 添加关键信息
        if key_points:
            summary_parts.append("关键信息：" + "；".join(key_points[:5]))
        
        # 添加实体信息
        if entities:
            summary_parts.append("涉及实体：" + "、".join(entities[:10]))
        
        # 添加消息摘要
        for msg in messages[-5:]:  # 保留最近 5 条消息的简要
            content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"[{msg.role}]: {content_preview}")
        
        summary_text = "\n".join(summary_parts)
        compressed_tokens = TokenCounter.count_tokens(summary_text)
        
        summary = ContextSummary(
            summary_text=summary_text,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            key_points=key_points,
            entities=entities,
        )
        
        return summary_text, summary


class InstantMemory:
    """
    瞬时记忆类
    
    实现滑动窗口上下文管理，支持 100K tokens 的上下文窗口
    提供自动压缩和摘要功能
    """
    
    # 默认最大 Token 数量（100K）
    DEFAULT_MAX_TOKENS = 100000
    
    # 压缩触发阈值（达到 80% 时触发压缩）
    COMPRESSION_THRESHOLD = 0.8
    
    # 保留的最近消息数量（压缩时保留）
    PRESERVED_MESSAGES = 10
    
    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        conversation_id: Optional[str] = None,
    ):
        """
        初始化瞬时记忆
        
        Args:
            max_tokens: 最大 Token 数量
            conversation_id: 对话 ID
        """
        self.max_tokens = max_tokens
        self.conversation_id = conversation_id
        
        # 消息队列（使用 deque 实现滑动窗口）
        self._messages: deque = deque()
        
        # 摘要历史
        self._summaries: List[ContextSummary] = []
        
        # 当前 Token 计数
        self._current_tokens = 0
        
        # 压缩后的摘要文本
        self._compressed_summary: Optional[str] = None
        
        logger.info(
            f"初始化瞬时记忆: max_tokens={max_tokens}, "
            f"conversation_id={conversation_id}"
        )
    
    @property
    def current_tokens(self) -> int:
        """
        获取当前 Token 数量
        
        Returns:
            当前 Token 数量
        """
        return self._current_tokens
    
    @property
    def message_count(self) -> int:
        """
        获取消息数量
        
        Returns:
            消息数量
        """
        return len(self._messages)
    
    @property
    def usage_ratio(self) -> float:
        """
        获取使用率
        
        Returns:
            当前使用率（0-1）
        """
        return self._current_tokens / self.max_tokens
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageContext:
        """
        添加消息到上下文
        
        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
            metadata: 元数据
            
        Returns:
            创建的消息上下文对象
        """
        # 计算 Token 数量
        token_count = TokenCounter.count_tokens(content)
        
        # 创建消息上下文
        message = MessageContext(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {},
        )
        
        # 添加到队列
        self._messages.append(message)
        self._current_tokens += token_count + 4  # 加上消息格式开销
        
        # 检查是否需要压缩
        if self.usage_ratio >= self.COMPRESSION_THRESHOLD:
            self._auto_compress()
        
        logger.debug(
            f"添加消息: role={role}, tokens={token_count}, "
            f"total_tokens={self._current_tokens}, ratio={self.usage_ratio:.2%}"
        )
        
        return message
    
    def _auto_compress(self) -> None:
        """
        自动压缩上下文
        """
        if len(self._messages) <= self.PRESERVED_MESSAGES:
            return
        
        # 获取需要压缩的消息（保留最近的）
        messages_to_compress = list(self._messages)[:-self.PRESERVED_MESSAGES]
        
        if not messages_to_compress:
            return
        
        # 计算压缩目标
        target_tokens = int(self.max_tokens * 0.3)
        
        # 执行压缩
        summary_text, summary = ContextCompressor.compress_messages(
            messages_to_compress,
            target_tokens,
        )
        
        # 更新摘要
        self._summaries.append(summary)
        self._compressed_summary = summary_text
        
        # 移除已压缩的消息
        for _ in range(len(messages_to_compress)):
            removed_msg = self._messages.popleft()
            self._current_tokens -= removed_msg.token_count + 4
        
        # 添加摘要的 Token 计数
        summary_tokens = TokenCounter.count_tokens(summary_text)
        self._current_tokens += summary_tokens
        
        logger.info(
            f"自动压缩完成: 压缩 {len(messages_to_compress)} 条消息, "
            f"节省 {summary.original_token_count - summary.compressed_token_count} tokens"
        )
    
    def get_context(
        self,
        include_summary: bool = True,
        max_messages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取当前上下文
        
        Args:
            include_summary: 是否包含压缩摘要
            max_messages: 最大返回消息数量
            
        Returns:
            消息列表（字典格式）
        """
        messages = []
        
        # 添加压缩摘要
        if include_summary and self._compressed_summary:
            messages.append({
                "role": "system",
                "content": f"[历史对话摘要]\n{self._compressed_summary}",
                "is_summary": True,
            })
        
        # 添加消息
        msg_list = list(self._messages)
        if max_messages:
            msg_list = msg_list[-max_messages:]
        
        for msg in msg_list:
            messages.append(msg.to_dict())
        
        return messages
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """
        获取适用于 LLM API 的消息格式
        
        Returns:
            LLM API 格式的消息列表
        """
        messages = []
        
        # 添加压缩摘要作为系统消息
        if self._compressed_summary:
            messages.append({
                "role": "system",
                "content": f"[历史对话摘要]\n{self._compressed_summary}",
            })
        
        # 添加消息
        for msg in self._messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        return messages
    
    def clear(self) -> None:
        """
        清空上下文
        """
        self._messages.clear()
        self._summaries.clear()
        self._current_tokens = 0
        self._compressed_summary = None
        
        logger.info(f"清空瞬时记忆: conversation_id={self.conversation_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "conversation_id": self.conversation_id,
            "message_count": self.message_count,
            "current_tokens": self._current_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": self.usage_ratio,
            "summary_count": len(self._summaries),
            "has_compressed_summary": self._compressed_summary is not None,
        }
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出状态（用于持久化）
        
        Returns:
            状态字典
        """
        return {
            "conversation_id": self.conversation_id,
            "max_tokens": self.max_tokens,
            "messages": [msg.to_dict() for msg in self._messages],
            "summaries": [s.to_dict() for s in self._summaries],
            "current_tokens": self._current_tokens,
            "compressed_summary": self._compressed_summary,
        }
    
    @classmethod
    def import_state(cls, state: Dict[str, Any]) -> "InstantMemory":
        """
        从状态恢复实例
        
        Args:
            state: 状态字典
            
        Returns:
            瞬时记忆实例
        """
        instance = cls(
            max_tokens=state.get("max_tokens", cls.DEFAULT_MAX_TOKENS),
            conversation_id=state.get("conversation_id"),
        )
        
        # 恢复消息
        for msg_data in state.get("messages", []):
            msg = MessageContext.from_dict(msg_data)
            instance._messages.append(msg)
        
        # 恢复摘要
        for summary_data in state.get("summaries", []):
            summary = ContextSummary(
                summary_text=summary_data.get("summary_text", ""),
                original_token_count=summary_data.get("original_token_count", 0),
                compressed_token_count=summary_data.get("compressed_token_count", 0),
                key_points=summary_data.get("key_points", []),
                entities=summary_data.get("entities", []),
                created_at=summary_data.get("created_at", ""),
            )
            instance._summaries.append(summary)
        
        instance._current_tokens = state.get("current_tokens", 0)
        instance._compressed_summary = state.get("compressed_summary")
        
        return instance


class InstantMemoryManager:
    """
    瞬时记忆管理器
    
    管理多个对话的瞬时记忆实例
    """
    
    def __init__(self, default_max_tokens: int = InstantMemory.DEFAULT_MAX_TOKENS):
        """
        初始化管理器
        
        Args:
            default_max_tokens: 默认最大 Token 数量
        """
        self.default_max_tokens = default_max_tokens
        self._memories: Dict[str, InstantMemory] = {}
        
        logger.info(f"初始化瞬时记忆管理器: default_max_tokens={default_max_tokens}")
    
    def get_memory(self, conversation_id: str) -> InstantMemory:
        """
        获取或创建对话的瞬时记忆
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            瞬时记忆实例
        """
        if conversation_id not in self._memories:
            self._memories[conversation_id] = InstantMemory(
                max_tokens=self.default_max_tokens,
                conversation_id=conversation_id,
            )
        
        return self._memories[conversation_id]
    
    def remove_memory(self, conversation_id: str) -> bool:
        """
        移除对话的瞬时记忆
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            是否成功移除
        """
        if conversation_id in self._memories:
            del self._memories[conversation_id]
            logger.info(f"移除瞬时记忆: conversation_id={conversation_id}")
            return True
        return False
    
    def clear_all(self) -> None:
        """
        清空所有瞬时记忆
        """
        self._memories.clear()
        logger.info("清空所有瞬时记忆")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有对话的统计信息
        
        Returns:
            对话 ID 到统计信息的映射
        """
        return {
            conv_id: memory.get_stats()
            for conv_id, memory in self._memories.items()
        }
    
    def export_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        导出所有状态
        
        Returns:
            对话 ID 到状态的映射
        """
        return {
            conv_id: memory.export_state()
            for conv_id, memory in self._memories.items()
        }
