"""
OpenAI API 适配器
支持 OpenAI GPT 系列模型的 API 调用
"""
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger

from app.services.llm.base import (
    BaseLLMAdapter,
    LLMConnectionError,
    LLMError,
    LLMModelNotFoundError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)

# 延迟导入 OpenAI，以便在没有安装时提供友好的错误提示
_openai_module = None


def _get_openai_module():
    """
    延迟加载 OpenAI 模块
    
    Returns:
        OpenAI 模块
        
    Raises:
        ImportError: 当 openai 包未安装时
    """
    global _openai_module
    if _openai_module is None:
        try:
            import openai
            _openai_module = openai
        except ImportError:
            raise ImportError(
                "openai 包未安装，请运行: pip install openai"
            )
    return _openai_module


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI API 适配器
    
    支持 OpenAI 提供的 GPT 系列模型：
    - GPT-4 / GPT-4-turbo / GPT-4o
    - GPT-3.5-turbo
    - text-embedding-ada-002 / text-embedding-3-small / text-embedding-3-large
    
    特性：
    - 支持流式响应
    - 支持函数调用
    - 支持视觉模型（GPT-4-vision）
    - 自动重试和错误处理
    """
    
    # OpenAI 默认配置
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
    DEFAULT_TIMEOUT = 60.0
    
    # 已知模型的上下文窗口大小
    MODEL_CONTEXT_WINDOWS = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "gpt-4-turbo-preview": 128000,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-3.5-turbo": 16385,
        "gpt-3.5-turbo-16k": 16385,
    }
    
    # 嵌入模型维度
    EMBEDDING_DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }
    
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        embedding_model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        初始化 OpenAI 适配器
        
        Args:
            model_name: 模型名称（如 gpt-4, gpt-3.5-turbo 等）
            api_key: OpenAI API 密钥
            base_url: API 基础 URL（可选，用于代理或自定义端点）
            embedding_model: 嵌入模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            **kwargs: 其他参数传递给基类
        """
        # 根据模型名称自动设置上下文窗口
        context_window = self._get_context_window(model_name)
        
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            context_window=context_window,
            **kwargs,
        )
        
        self.embedding_model = embedding_model or self.DEFAULT_EMBEDDING_MODEL
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None
        
        logger.info(
            f"初始化 OpenAI 适配器: model={model_name}, "
            f"context_window={context_window}, embedding_model={self.embedding_model}"
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
        return 8192
    
    def _get_client(self):
        """
        获取或创建 OpenAI 客户端
        
        Returns:
            OpenAI 异步客户端实例
        """
        if self._client is None:
            openai = _get_openai_module()
            
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout,
                "max_retries": self.max_retries,
            }
            
            # 设置自定义 base_url（用于代理）
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            self._client = openai.AsyncOpenAI(**client_kwargs)
            
        return self._client
    
    async def close(self) -> None:
        """
        关闭 OpenAI 客户端连接
        """
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.debug("OpenAI 客户端已关闭")
    
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
                - presence_penalty: 存在惩罚
                - frequency_penalty: 频率惩罚
                - tools: 函数调用工具列表
                - tool_choice: 函数调用选择
                
        Returns:
            生成的回复文本
            
        Raises:
            LLMConnectionError: 连接错误
            LLMResponseError: 响应错误
            LLMTimeoutError: 超时错误
            LLMRateLimitError: 速率限制错误
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
                "top_p", "stop", "presence_penalty", "frequency_penalty",
                "tools", "tool_choice", "response_format", "seed"
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
                raise LLMResponseError("OpenAI 返回空的响应")
                
        except Exception as e:
            raise self._handle_openai_error(e)
    
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
                "top_p", "stop", "presence_penalty", "frequency_penalty",
                "tools", "tool_choice", "response_format", "seed"
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
            raise self._handle_openai_error(e)
    
    async def embed(
        self,
        text: str,
        **kwargs,
    ) -> List[float]:
        """
        文本向量化
        
        使用 OpenAI 嵌入模型生成文本向量
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数，支持：
                - embedding_model: 指定嵌入模型
                - dimensions: 输出维度（仅 text-embedding-3 系列支持）
                
        Returns:
            文本的向量表示
            
        Raises:
            LLMConnectionError: 连接错误
            LLMResponseError: 响应错误
            LLMTimeoutError: 超时错误
        """
        try:
            embedding_model = kwargs.get("embedding_model", self.embedding_model)
            
            request_params = {
                "model": embedding_model,
                "input": text,
            }
            
            # text-embedding-3 系列支持自定义维度
            if "dimensions" in kwargs:
                request_params["dimensions"] = kwargs["dimensions"]
            
            client = self._get_client()
            response = await client.embeddings.create(**request_params)
            
            if response.data and len(response.data) > 0:
                return response.data[0].embedding
            else:
                raise LLMResponseError("OpenAI 嵌入返回空响应")
                
        except Exception as e:
            raise self._handle_openai_error(e)
    
    async def embed_batch(
        self,
        texts: List[str],
        **kwargs,
    ) -> List[List[float]]:
        """
        批量文本向量化
        
        Args:
            texts: 待向量化的文本列表
            **kwargs: 其他参数
            
        Returns:
            文本向量列表
        """
        try:
            embedding_model = kwargs.get("embedding_model", self.embedding_model)
            
            request_params = {
                "model": embedding_model,
                "input": texts,
            }
            
            if "dimensions" in kwargs:
                request_params["dimensions"] = kwargs["dimensions"]
            
            client = self._get_client()
            response = await client.embeddings.create(**request_params)
            
            # 按原始顺序返回嵌入
            embeddings = [None] * len(texts)
            for item in response.data:
                embeddings[item.index] = item.embedding
            
            return embeddings
            
        except Exception as e:
            raise self._handle_openai_error(e)
    
    async def check_status(self) -> bool:
        """
        检查 OpenAI API 状态
        
        Returns:
            True 表示 API 可用，False 表示不可用
        """
        try:
            client = self._get_client()
            
            # 尝试列出模型来验证 API 密钥
            models = await client.models.list()
            
            if models:
                logger.debug("OpenAI API 状态正常")
                return True
            else:
                logger.warning("OpenAI API 返回空模型列表")
                return False
                
        except Exception as e:
            logger.warning(f"OpenAI API 不可用: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典
        """
        info = {
            "name": self.model_name,
            "provider": "openai",
            "base_url": self.base_url or self.DEFAULT_BASE_URL,
            "context_window": self.context_window,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "supports_streaming": True,
            "supports_embedding": True,
            "embedding_model": self.embedding_model,
            "embedding_dimensions": self.EMBEDDING_DIMENSIONS.get(
                self.embedding_model, 1536
            ),
            "status": "unknown",
        }
        
        try:
            client = self._get_client()
            
            # 尝试获取模型详情
            try:
                model = await client.models.retrieve(self.model_name)
                info["status"] = "available"
                info["model_details"] = {
                    "id": model.id,
                    "owned_by": model.owned_by,
                }
            except Exception:
                # 模型可能不存在或无权限访问
                info["status"] = "unknown"
                
        except Exception as e:
            info["status"] = "error"
            info["error"] = str(e)
        
        return info
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        列出可用的 OpenAI 模型
        
        Returns:
            模型列表
        """
        try:
            client = self._get_client()
            models = await client.models.list()
            
            return [
                {
                    "id": model.id,
                    "owned_by": model.owned_by,
                }
                for model in models.data
            ]
            
        except Exception as e:
            logger.error(f"获取 OpenAI 模型列表错误: {e}")
            return []
    
    def _handle_openai_error(self, error: Exception) -> LLMError:
        """
        处理 OpenAI API 错误，转换为统一的 LLM 错误类型
        
        Args:
            error: 原始错误
            
        Returns:
            LLM 错误实例
        """
        openai = _get_openai_module()
        
        # 超时错误
        if isinstance(error, openai.APITimeoutError):
            logger.error(f"OpenAI 请求超时: {error}")
            return LLMTimeoutError(f"OpenAI 请求超时: {error}")
        
        # 连接错误
        if isinstance(error, openai.APIConnectionError):
            logger.error(f"OpenAI 连接错误: {error}")
            return LLMConnectionError(f"OpenAI 连接错误: {error}")
        
        # 速率限制
        if isinstance(error, openai.RateLimitError):
            logger.error(f"OpenAI 速率限制: {error}")
            return LLMRateLimitError(f"OpenAI 速率限制: {error}")
        
        # 模型不存在
        if isinstance(error, openai.NotFoundError):
            logger.error(f"OpenAI 模型不存在: {error}")
            return LLMModelNotFoundError(f"OpenAI 模型不存在: {error}")
        
        # 认证错误
        if isinstance(error, openai.AuthenticationError):
            logger.error(f"OpenAI 认证失败: {error}")
            return LLMConnectionError(f"OpenAI 认证失败，请检查 API 密钥")
        
        # 服务器错误
        if isinstance(error, openai.InternalServerError):
            logger.error(f"OpenAI 服务器错误: {error}")
            return LLMResponseError(f"OpenAI 服务器错误: {error}")
        
        # API 错误
        if isinstance(error, openai.APIError):
            logger.error(f"OpenAI API 错误: {error}")
            return LLMResponseError(f"OpenAI API 错误: {error}")
        
        # 其他错误
        logger.error(f"OpenAI 未知错误: {error}")
        return LLMError(f"OpenAI 未知错误: {error}")
    
    def __del__(self):
        """
        析构函数
        """
        pass
