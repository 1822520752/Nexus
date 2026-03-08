"""
DeepSeek API 适配器
支持 DeepSeek 系列模型的 API 调用
"""
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger

from app.services.llm.base import (
    BaseLLMAdapter,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)


class DeepSeekAdapter(BaseLLMAdapter):
    """
    DeepSeek API 适配器
    
    支持 DeepSeek 提供的模型：
    - deepseek-chat: 通用对话模型
    - deepseek-coder: 代码专用模型
    
    DeepSeek API 兼容 OpenAI SDK 格式，因此可以复用大部分逻辑
    
    特性：
    - 支持流式响应
    - 支持长上下文（最高 64K）
    - 高性价比
    - 优秀的代码生成能力
    """
    
    # DeepSeek 默认配置
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_TIMEOUT = 60.0
    
    # 已知模型的上下文窗口大小
    MODEL_CONTEXT_WINDOWS = {
        "deepseek-chat": 64000,
        "deepseek-coder": 16000,
    }
    
    # 模型特性
    MODEL_FEATURES = {
        "deepseek-chat": {
            "supports_tools": True,
            "supports_vision": False,
            "description": "通用对话模型，支持长上下文",
        },
        "deepseek-coder": {
            "supports_tools": True,
            "supports_vision": False,
            "description": "代码专用模型，擅长代码生成和理解",
        },
    }
    
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        初始化 DeepSeek 适配器
        
        Args:
            model_name: 模型名称（如 deepseek-chat, deepseek-coder）
            api_key: DeepSeek API 密钥
            base_url: API 基础 URL（可选）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            **kwargs: 其他参数传递给基类
        """
        # 根据模型名称自动设置上下文窗口
        context_window = self._get_context_window(model_name)
        
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            context_window=context_window,
            **kwargs,
        )
        
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
        
        logger.info(
            f"初始化 DeepSeek 适配器: model={model_name}, "
            f"context_window={context_window}"
        )
    
    def _get_context_window(self, model_name: str) -> int:
        """
        根据模型名称获取上下文窗口大小
        
        Args:
            model_name: 模型名称
            
        Returns:
            上下文窗口大小
        """
        # 精确匹配
        if model_name in self.MODEL_CONTEXT_WINDOWS:
            return self.MODEL_CONTEXT_WINDOWS[model_name]
        
        # 前缀匹配
        for prefix, window in self.MODEL_CONTEXT_WINDOWS.items():
            if model_name.startswith(prefix):
                return window
        
        # 默认值
        return 16000
    
    def _get_client(self):
        """
        获取或创建 OpenAI 兼容客户端
        
        DeepSeek API 兼容 OpenAI SDK，因此可以直接使用 OpenAI 客户端
        
        Returns:
            OpenAI 异步客户端实例
        """
        if self._client is None:
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "openai 包未安装，请运行: pip install openai"
                )
            
            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
            
        return self._client
    
    async def close(self) -> None:
        """
        关闭客户端连接
        """
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.debug("DeepSeek 客户端已关闭")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """
        同步对话生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数，支持：
                - temperature: 温度参数
                - max_tokens: 最大生成 Token 数
                - top_p: Top-p 采样
                - stop: 停止序列
                - frequency_penalty: 频率惩罚
                - tools: 函数调用工具列表
                - tool_choice: 函数调用选择
                
        Returns:
            生成的回复文本
            
        Raises:
            LLMConnectionError: 连接错误
            LLMResponseError: 响应错误
            LLMTimeoutError: 超时错误
        """
        try:
            # 截断消息以适应上下文窗口
            truncated_messages = self._truncate_messages(
                messages,
                self.context_window - self.max_tokens
            )
            
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": truncated_messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            }
            
            # 添加可选参数
            optional_params = [
                "top_p", "stop", "frequency_penalty",
                "tools", "tool_choice", "response_format"
            ]
            for param in optional_params:
                if param in kwargs:
                    request_params[param] = kwargs[param]
            
            client = self._get_client()
            response = await client.chat.completions.create(**request_params)
            
            # 提取回复内容
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content or ""
            else:
                raise LLMResponseError("DeepSeek 返回空的响应")
                
        except Exception as e:
            raise self._handle_deepseek_error(e)
    
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
        try:
            # 截断消息以适应上下文窗口
            truncated_messages = self._truncate_messages(
                messages,
                self.context_window - self.max_tokens
            )
            
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": truncated_messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": True,
            }
            
            # 添加可选参数
            optional_params = [
                "top_p", "stop", "frequency_penalty",
                "tools", "tool_choice", "response_format"
            ]
            for param in optional_params:
                if param in kwargs:
                    request_params[param] = kwargs[param]
            
            client = self._get_client()
            stream = await client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except Exception as e:
            raise self._handle_deepseek_error(e)
    
    async def embed(
        self,
        text: str,
        **kwargs,
    ) -> List[float]:
        """
        文本向量化
        
        注意：DeepSeek 目前不提供独立的嵌入 API，
        建议使用其他嵌入服务（如 OpenAI 或本地模型）
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数
            
        Returns:
            文本的向量表示
            
        Raises:
            LLMError: DeepSeek 不支持嵌入功能
        """
        # DeepSeek 目前不提供嵌入 API
        # 可以考虑使用 OpenAI 的嵌入 API 或本地模型
        raise LLMError(
            "DeepSeek 目前不提供文本嵌入 API，"
            "建议使用 OpenAI text-embedding-ada-002 或本地嵌入模型"
        )
    
    async def check_status(self) -> bool:
        """
        检查 DeepSeek API 状态
        
        Returns:
            True 表示 API 可用，False 表示不可用
        """
        try:
            client = self._get_client()
            
            # 尝试一个简单的请求来验证 API
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            
            if response:
                logger.debug("DeepSeek API 状态正常")
                return True
            else:
                return False
                
        except Exception as e:
            logger.warning(f"DeepSeek API 不可用: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典
        """
        info = {
            "name": self.model_name,
            "provider": "deepseek",
            "base_url": self.base_url,
            "context_window": self.context_window,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "supports_streaming": True,
            "supports_embedding": False,
            "status": "unknown",
        }
        
        # 添加模型特性
        if self.model_name in self.MODEL_FEATURES:
            info["features"] = self.MODEL_FEATURES[self.model_name]
        
        # 检查状态
        try:
            is_available = await self.check_status()
            info["status"] = "available" if is_available else "unavailable"
        except Exception as e:
            info["status"] = "error"
            info["error"] = str(e)
        
        return info
    
    async def chat_with_reasoning(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        带推理过程的对话生成
        
        DeepSeek Coder 支持显示推理过程
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            包含回复和推理过程的字典
        """
        try:
            # 截断消息
            truncated_messages = self._truncate_messages(
                messages,
                self.context_window - self.max_tokens
            )
            
            request_params = {
                "model": self.model_name,
                "messages": truncated_messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            }
            
            client = self._get_client()
            response = await client.chat.completions.create(**request_params)
            
            result = {
                "content": "",
                "reasoning_content": None,
            }
            
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                result["content"] = message.content or ""
                
                # DeepSeek 可能返回推理过程
                if hasattr(message, "reasoning_content"):
                    result["reasoning_content"] = message.reasoning_content
            
            return result
            
        except Exception as e:
            raise self._handle_deepseek_error(e)
    
    def _handle_deepseek_error(self, error: Exception) -> LLMError:
        """
        处理 DeepSeek API 错误
        
        Args:
            error: 原始错误
            
        Returns:
            LLM 错误实例
        """
        try:
            import openai
        except ImportError:
            return LLMError(f"DeepSeek 错误: {error}")
        
        # 超时错误
        if isinstance(error, openai.APITimeoutError):
            logger.error(f"DeepSeek 请求超时: {error}")
            return LLMTimeoutError(f"DeepSeek 请求超时: {error}")
        
        # 连接错误
        if isinstance(error, openai.APIConnectionError):
            logger.error(f"DeepSeek 连接错误: {error}")
            return LLMConnectionError(f"DeepSeek 连接错误: {error}")
        
        # 速率限制
        if isinstance(error, openai.RateLimitError):
            logger.error(f"DeepSeek 速率限制: {error}")
            return LLMRateLimitError(f"DeepSeek 速率限制: {error}")
        
        # 认证错误
        if isinstance(error, openai.AuthenticationError):
            logger.error(f"DeepSeek 认证失败: {error}")
            return LLMConnectionError(f"DeepSeek 认证失败，请检查 API 密钥")
        
        # 服务器错误
        if isinstance(error, openai.InternalServerError):
            logger.error(f"DeepSeek 服务器错误: {error}")
            return LLMResponseError(f"DeepSeek 服务器错误: {error}")
        
        # API 错误
        if isinstance(error, openai.APIError):
            logger.error(f"DeepSeek API 错误: {error}")
            return LLMResponseError(f"DeepSeek API 错误: {error}")
        
        # 其他错误
        logger.error(f"DeepSeek 未知错误: {error}")
        return LLMError(f"DeepSeek 未知错误: {error}")
    
    def __del__(self):
        """
        析构函数
        """
        pass
