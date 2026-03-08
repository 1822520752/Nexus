"""
Ollama 本地模型适配器
支持本地部署的 Ollama 模型服务
"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from loguru import logger

from app.services.llm.base import (
    BaseLLMAdapter,
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
)


class OllamaAdapter(BaseLLMAdapter):
    """
    Ollama 本地模型适配器
    
    支持 Ollama 提供的本地 LLM 服务，包括：
    - Llama 2 / Llama 3
    - Mistral
    - Qwen
    - 其他 Ollama 支持的模型
    
    默认连接地址: http://localhost:11434
    """
    
    # Ollama 默认配置
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
    DEFAULT_TIMEOUT = 120.0  # Ollama 本地模型可能较慢
    
    def __init__(
        self,
        model_name: str,
        base_url: Optional[str] = None,
        embedding_model: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        **kwargs,
    ):
        """
        初始化 Ollama 适配器
        
        Args:
            model_name: 模型名称（如 llama2, mistral, qwen 等）
            base_url: Ollama 服务地址，默认 http://localhost:11434
            embedding_model: 嵌入模型名称，默认 nomic-embed-text
            timeout: 请求超时时间（秒）
            **kwargs: 其他参数传递给基类
        """
        super().__init__(
            model_name=model_name,
            base_url=base_url or self.DEFAULT_BASE_URL,
            **kwargs,
        )
        
        self.embedding_model = embedding_model or self.DEFAULT_EMBEDDING_MODEL
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(
            f"初始化 Ollama 适配器: model={model_name}, "
            f"base_url={self.base_url}, embedding_model={self.embedding_model}"
        )
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        获取或创建 HTTP 客户端
        
        Returns:
            httpx.AsyncClient 实例
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._client
    
    async def close(self) -> None:
        """
        关闭 HTTP 客户端连接
        """
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.debug("Ollama HTTP 客户端已关闭")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """
        同步对话生成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
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
            
            # 构建 Ollama API 请求
            payload = {
                "model": self.model_name,
                "messages": truncated_messages,
                "stream": False,
                "options": {
                    "num_predict": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature),
                },
            }
            
            # 添加其他选项
            for key in ["top_p", "top_k", "seed", "stop"]:
                if key in kwargs:
                    payload["options"][key] = kwargs[key]
            
            client = await self._get_client()
            response = await client.post(
                "/api/chat",
                json=payload,
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API 错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LLMResponseError(error_msg)
            
            result = response.json()
            
            # 提取回复内容
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"]
            else:
                raise LLMResponseError(f"无效的响应格式: {result}")
                
        except httpx.TimeoutException as e:
            logger.error(f"Ollama 请求超时: {e}")
            raise LLMTimeoutError(f"Ollama 请求超时: {e}") from e
        except httpx.ConnectError as e:
            logger.error(f"Ollama 连接错误: {e}")
            raise LLMConnectionError(
                f"无法连接到 Ollama 服务 ({self.base_url})，请确保 Ollama 正在运行"
            ) from e
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Ollama 对话生成错误: {e}")
            raise LLMError(f"Ollama 对话生成错误: {e}") from e
    
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
            
            # 构建流式请求
            payload = {
                "model": self.model_name,
                "messages": truncated_messages,
                "stream": True,
                "options": {
                    "num_predict": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature),
                },
            }
            
            # 添加其他选项
            for key in ["top_p", "top_k", "seed", "stop"]:
                if key in kwargs:
                    payload["options"][key] = kwargs[key]
            
            client = await self._get_client()
            
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_msg = f"Ollama API 错误: {response.status_code} - {error_text}"
                    logger.error(error_msg)
                    raise LLMResponseError(error_msg)
                
                buffer = ""
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            if content:
                                yield content
                        
                        # 检查是否完成
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"解析 JSON 行失败: {line}, 错误: {e}")
                        continue
                        
        except httpx.TimeoutException as e:
            logger.error(f"Ollama 流式请求超时: {e}")
            raise LLMTimeoutError(f"Ollama 流式请求超时: {e}") from e
        except httpx.ConnectError as e:
            logger.error(f"Ollama 连接错误: {e}")
            raise LLMConnectionError(
                f"无法连接到 Ollama 服务 ({self.base_url})，请确保 Ollama 正在运行"
            ) from e
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Ollama 流式对话生成错误: {e}")
            raise LLMError(f"Ollama 流式对话生成错误: {e}") from e
    
    async def embed(
        self,
        text: str,
        **kwargs,
    ) -> List[float]:
        """
        文本向量化
        
        使用 Ollama 的嵌入模型生成文本向量
        
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
        try:
            payload = {
                "model": kwargs.get("embedding_model", self.embedding_model),
                "input": text,
            }
            
            client = await self._get_client()
            response = await client.post(
                "/api/embeddings",
                json=payload,
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama 嵌入 API 错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LLMResponseError(error_msg)
            
            result = response.json()
            
            if "embedding" in result:
                return result["embedding"]
            else:
                raise LLMResponseError(f"无效的嵌入响应格式: {result}")
                
        except httpx.TimeoutException as e:
            logger.error(f"Ollama 嵌入请求超时: {e}")
            raise LLMTimeoutError(f"Ollama 嵌入请求超时: {e}") from e
        except httpx.ConnectError as e:
            logger.error(f"Ollama 连接错误: {e}")
            raise LLMConnectionError(
                f"无法连接到 Ollama 服务 ({self.base_url})，请确保 Ollama 正在运行"
            ) from e
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Ollama 文本向量化错误: {e}")
            raise LLMError(f"Ollama 文本向量化错误: {e}") from e
    
    async def check_status(self) -> bool:
        """
        检查 Ollama 服务状态
        
        Returns:
            True 表示服务正常，False 表示服务不可用
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            
            if response.status_code == 200:
                logger.debug("Ollama 服务状态正常")
                return True
            else:
                logger.warning(f"Ollama 服务状态异常: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Ollama 服务不可用: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典
        """
        # 基础信息
        info = {
            "name": self.model_name,
            "provider": "ollama",
            "base_url": self.base_url,
            "context_window": self.context_window,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "supports_streaming": True,
            "supports_embedding": True,
            "embedding_model": self.embedding_model,
            "status": "unknown",
        }
        
        try:
            # 获取可用模型列表
            client = await self._get_client()
            response = await client.get("/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                # 查找当前模型
                for model in models:
                    if model.get("name", "").startswith(self.model_name):
                        info["status"] = "available"
                        info["model_details"] = {
                            "size": model.get("size"),
                            "modified_at": model.get("modified_at"),
                            "digest": model.get("digest"),
                        }
                        break
                else:
                    info["status"] = "not_found"
                    info["available_models"] = [m.get("name") for m in models]
            else:
                info["status"] = "error"
                
        except Exception as e:
            info["status"] = "error"
            info["error"] = str(e)
        
        return info
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        列出 Ollama 中所有可用的模型
        
        Returns:
            模型列表
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            else:
                logger.error(f"获取模型列表失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"获取 Ollama 模型列表错误: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """
        拉取（下载）模型
        
        Args:
            model_name: 要拉取的模型名称
            
        Returns:
            是否成功
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/pull",
                json={"name": model_name, "stream": False},
                timeout=httpx.Timeout(600.0),  # 拉取模型可能需要较长时间
            )
            
            if response.status_code == 200:
                logger.info(f"成功拉取模型: {model_name}")
                return True
            else:
                logger.error(f"拉取模型失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"拉取 Ollama 模型错误: {e}")
            return False
    
    def __del__(self):
        """
        析构函数，确保关闭连接
        """
        # 注意：在异步环境中，__del__ 可能不会正确调用 close()
        # 建议在使用完毕后显式调用 await adapter.close()
        pass
