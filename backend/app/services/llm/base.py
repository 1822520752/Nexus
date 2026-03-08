"""
AI 模型适配器抽象基类
定义统一的 LLM 接口规范，支持多种 AI 模型提供商
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger


class BaseLLMAdapter(ABC):
    """
    LLM 适配器抽象基类
    
    定义所有 AI 模型适配器必须实现的接口
    支持对话生成、流式对话、文本向量化和状态检查
    """
    
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        context_window: int = 8192,
        **kwargs,
    ):
        """
        初始化 LLM 适配器
        
        Args:
            model_name: 模型名称
            api_key: API 密钥（可选，本地模型不需要）
            base_url: API 基础 URL（可选）
            max_tokens: 最大生成 Token 数
            temperature: 温度参数，控制随机性
            context_window: 上下文窗口大小
            **kwargs: 其他配置参数
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.context_window = context_window
        self.extra_config = kwargs
        
        logger.info(
            f"初始化 LLM 适配器: model={model_name}, "
            f"max_tokens={max_tokens}, temperature={temperature}"
        )
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """
        同步对话生成
        
        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 其他参数（如 temperature, max_tokens 等）
            
        Returns:
            生成的回复文本
            
        Raises:
            LLMConnectionError: 连接错误
            LLMResponseError: 响应错误
            LLMTimeoutError: 超时错误
        """
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            生成的文本片段
            
        Raises:
            LLMConnectionError: 连接错误
            LLMResponseError: 响应错误
            LLMTimeoutError: 超时错误
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        text: str,
        **kwargs,
    ) -> List[float]:
        """
        文本向量化
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数
            
        Returns:
            文本的向量表示
            
        Raises:
            LLMConnectionError: 连接错误
            LLMResponseError: 响应错误
            LLMTimeoutError: 超时错误
        """
        pass
    
    @abstractmethod
    async def check_status(self) -> bool:
        """
        检查模型服务状态
        
        Returns:
            True 表示服务正常，False 表示服务不可用
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典，如：
            {
                "name": "模型名称",
                "provider": "提供商",
                "context_window": 上下文窗口大小,
                "max_tokens": 最大生成 Token 数,
                "supports_streaming": 是否支持流式,
                "supports_embedding": 是否支持嵌入,
            }
        """
        pass
    
    def _count_tokens(self, text: str) -> int:
        """
        计算 Token 数量（估算）
        
        使用简单的启发式方法估算 Token 数量：
        - 英文：约 4 个字符 = 1 个 Token
        - 中文：约 1.5 个字符 = 1 个 Token
        
        Args:
            text: 待计算的文本
            
        Returns:
            估算的 Token 数量
        """
        if not text:
            return 0
        
        # 统计中文字符数量
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        # 非中文字符
        other_chars = len(text) - chinese_chars
        
        # 中文约 1.5 字符 = 1 Token，英文约 4 字符 = 1 Token
        tokens = int(chinese_chars / 1.5) + int(other_chars / 4)
        
        return max(1, tokens)
    
    def _count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算消息列表的总 Token 数量
        
        Args:
            messages: 消息列表
            
        Returns:
            总 Token 数量
        """
        total_tokens = 0
        for message in messages:
            # 每条消息有约 4 个 Token 的格式开销
            total_tokens += 4
            content = message.get("content", "")
            total_tokens += self._count_tokens(content)
            role = message.get("role", "")
            total_tokens += self._count_tokens(role)
        
        return total_tokens
    
    def _truncate_messages(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        preserve_system: bool = True,
    ) -> List[Dict[str, str]]:
        """
        截断消息列表以适应上下文窗口
        
        从最早的消息开始截断，可选择保留系统消息
        
        Args:
            messages: 原始消息列表
            max_tokens: 最大 Token 数量
            preserve_system: 是否保留系统消息
            
        Returns:
            截断后的消息列表
        """
        if not messages:
            return messages
        
        # 分离系统消息和其他消息
        system_messages = []
        other_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # 计算系统消息的 Token 数
        system_tokens = self._count_messages_tokens(system_messages)
        available_tokens = max_tokens - system_tokens - 100  # 保留 100 Token 余量
        
        if available_tokens <= 0:
            logger.warning("系统消息已超过上下文窗口限制")
            if preserve_system:
                return system_messages[-1:] if system_messages else []
            return []
        
        # 从最新的消息开始保留
        truncated_messages = list(system_messages) if preserve_system else []
        current_tokens = system_tokens if preserve_system else 0
        
        # 逆序遍历，保留最新的消息
        for msg in reversed(other_messages):
            msg_tokens = self._count_messages_tokens([msg])
            if current_tokens + msg_tokens <= available_tokens:
                truncated_messages.insert(
                    -1 if preserve_system and system_messages else len(truncated_messages),
                    msg
                )
                current_tokens += msg_tokens
            else:
                break
        
        # 重新排序：系统消息在前，其他消息按时间顺序
        result = []
        if preserve_system:
            result.extend(system_messages)
        
        # 添加非系统消息（按原始顺序）
        for msg in messages:
            if msg.get("role") != "system" and msg in truncated_messages:
                result.append(msg)
        
        logger.debug(
            f"消息截断完成: 原始 {len(messages)} 条 -> {len(result)} 条, "
            f"Token: {self._count_messages_tokens(messages)} -> {self._count_messages_tokens(result)}"
        )
        
        return result
    
    def _build_request_params(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        构建请求参数
        
        合并默认参数和用户提供的参数
        
        Args:
            messages: 消息列表
            **kwargs: 用户提供的参数
            
        Returns:
            完整的请求参数字典
        """
        params = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        # 合并其他参数
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value
        
        return params
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(model={self.model_name})>"


# ==================== 异常类定义 ====================

class LLMError(Exception):
    """LLM 相关错误的基类"""
    pass


class LLMConnectionError(LLMError):
    """LLM 连接错误"""
    pass


class LLMResponseError(LLMError):
    """LLM 响应错误"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 超时错误"""
    pass


class LLMRateLimitError(LLMError):
    """LLM 速率限制错误"""
    pass


class LLMModelNotFoundError(LLMError):
    """LLM 模型未找到错误"""
    pass
