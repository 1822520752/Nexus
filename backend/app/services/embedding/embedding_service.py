"""
嵌入服务模块
提供统一的文本向量化接口，支持多种嵌入模型
"""
import hashlib
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings


class EmbeddingModelType(str, Enum):
    """
    嵌入模型类型枚举
    
    定义支持的嵌入模型类型
    """
    
    OPENAI_ADA002 = "text-embedding-ada-002"  # OpenAI text-embedding-ada-002
    OPENAI_3_SMALL = "text-embedding-3-small"  # OpenAI text-embedding-3-small
    OPENAI_3_LARGE = "text-embedding-3-large"  # OpenAI text-embedding-3-large
    OLLAMA_NOMIC = "nomic-embed-text"  # Ollama nomic-embed-text
    OLLAMA_MXBAI = "mxbai-embed-large"  # Ollama mxbai-embed-large
    LOCAL_SENTENCE = "sentence-transformers"  # 本地 sentence-transformers


class EmbeddingResult:
    """
    嵌入结果类
    
    封装文本嵌入的结果数据
    """
    
    def __init__(
        self,
        embedding: List[float],
        model: str,
        dimension: int,
        tokens_used: int = 0,
        cached: bool = False,
    ):
        """
        初始化嵌入结果
        
        Args:
            embedding: 向量数据
            model: 使用的模型名称
            dimension: 向量维度
            tokens_used: 使用的 Token 数量
            cached: 是否来自缓存
        """
        self.embedding = embedding
        self.model = model
        self.dimension = dimension
        self.tokens_used = tokens_used
        self.cached = cached
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            包含所有属性的字典
        """
        return {
            "embedding": self.embedding,
            "model": self.model,
            "dimension": self.dimension,
            "tokens_used": self.tokens_used,
            "cached": self.cached,
        }


class EmbeddingConfig:
    """
    嵌入服务配置类
    
    配置嵌入服务的参数
    """
    
    # 各模型的默认维度
    MODEL_DIMENSIONS = {
        EmbeddingModelType.OPENAI_ADA002: 1536,
        EmbeddingModelType.OPENAI_3_SMALL: 1536,
        EmbeddingModelType.OPENAI_3_LARGE: 3072,
        EmbeddingModelType.OLLAMA_NOMIC: 768,
        EmbeddingModelType.OLLAMA_MXBAI: 1024,
        EmbeddingModelType.LOCAL_SENTENCE: 384,
    }
    
    # 批量嵌入的最大大小
    MAX_BATCH_SIZE = 100
    
    def __init__(
        self,
        model_type: EmbeddingModelType = EmbeddingModelType.OPENAI_ADA002,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        dimension: Optional[int] = None,
        cache_enabled: bool = True,
        batch_size: int = 20,
    ):
        """
        初始化嵌入配置
        
        Args:
            model_type: 嵌入模型类型
            api_key: API 密钥
            base_url: API 基础 URL
            dimension: 向量维度（None 表示使用模型默认维度）
            cache_enabled: 是否启用缓存
            batch_size: 批量嵌入的批次大小
        """
        self.model_type = model_type
        self.api_key = api_key
        self.base_url = base_url
        self.dimension = dimension or self.MODEL_DIMENSIONS.get(model_type, 1536)
        self.cache_enabled = cache_enabled
        self.batch_size = min(batch_size, self.MAX_BATCH_SIZE)


class BaseEmbeddingProvider(ABC):
    """
    嵌入提供者抽象基类
    
    定义所有嵌入提供者必须实现的接口
    """
    
    @abstractmethod
    async def embed(self, text: str, **kwargs) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数
            
        Returns:
            嵌入向量
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 待向量化的文本列表
            **kwargs: 其他参数
            
        Returns:
            嵌入向量列表
        """
        pass
    
    @abstractmethod
    async def check_status(self) -> bool:
        """
        检查服务状态
        
        Returns:
            服务是否可用
        """
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI 嵌入提供者
    
    使用 OpenAI API 生成文本嵌入
    """
    
    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化 OpenAI 嵌入提供者
        
        Args:
            model: 嵌入模型名称
            api_key: OpenAI API 密钥
            base_url: API 基础 URL
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self._client = None
    
    def _get_client(self):
        """
        获取或创建 OpenAI 客户端
        
        Returns:
            OpenAI 异步客户端
        """
        if self._client is None:
            try:
                import openai
                
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                
                self._client = openai.AsyncOpenAI(**client_kwargs)
            except ImportError:
                raise ImportError("openai 包未安装，请运行: pip install openai")
        
        return self._client
    
    async def embed(self, text: str, **kwargs) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数
            
        Returns:
            嵌入向量
        """
        client = self._get_client()
        
        request_params = {
            "model": kwargs.get("model", self.model),
            "input": text,
        }
        
        if "dimensions" in kwargs:
            request_params["dimensions"] = kwargs["dimensions"]
        
        response = await client.embeddings.create(**request_params)
        
        if response.data and len(response.data) > 0:
            return response.data[0].embedding
        
        raise ValueError("OpenAI 嵌入返回空响应")
    
    async def embed_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 待向量化的文本列表
            **kwargs: 其他参数
            
        Returns:
            嵌入向量列表
        """
        client = self._get_client()
        
        request_params = {
            "model": kwargs.get("model", self.model),
            "input": texts,
        }
        
        if "dimensions" in kwargs:
            request_params["dimensions"] = kwargs["dimensions"]
        
        response = await client.embeddings.create(**request_params)
        
        # 按原始顺序返回嵌入
        embeddings = [None] * len(texts)
        for item in response.data:
            embeddings[item.index] = item.embedding
        
        return embeddings
    
    async def check_status(self) -> bool:
        """
        检查 OpenAI API 状态
        
        Returns:
            API 是否可用
        """
        try:
            client = self._get_client()
            models = await client.models.list()
            return bool(models)
        except Exception as e:
            logger.warning(f"OpenAI API 不可用: {e}")
            return False


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Ollama 嵌入提供者
    
    使用 Ollama 本地服务生成文本嵌入
    """
    
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: Optional[str] = None,
    ):
        """
        初始化 Ollama 嵌入提供者
        
        Args:
            model: 嵌入模型名称
            base_url: Ollama 服务地址
        """
        self.model = model
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self._client = None
    
    async def _get_client(self):
        """
        获取或创建 HTTP 客户端
        
        Returns:
            httpx.AsyncClient 实例
        """
        if self._client is None or self._client.is_closed:
            import httpx
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(120.0),
                headers={"Content-Type": "application/json"},
            )
        
        return self._client
    
    async def embed(self, text: str, **kwargs) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数
            
        Returns:
            嵌入向量
        """
        client = await self._get_client()
        
        payload = {
            "model": kwargs.get("model", self.model),
            "input": text,
        }
        
        response = await client.post("/api/embeddings", json=payload)
        
        if response.status_code != 200:
            raise ValueError(f"Ollama 嵌入 API 错误: {response.status_code}")
        
        result = response.json()
        
        if "embedding" in result:
            return result["embedding"]
        
        raise ValueError(f"无效的嵌入响应格式: {result}")
    
    async def embed_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 待向量化的文本列表
            **kwargs: 其他参数
            
        Returns:
            嵌入向量列表
        """
        # Ollama 不支持批量嵌入，逐个处理
        embeddings = []
        for text in texts:
            embedding = await self.embed(text, **kwargs)
            embeddings.append(embedding)
        
        return embeddings
    
    async def check_status(self) -> bool:
        """
        检查 Ollama 服务状态
        
        Returns:
            服务是否可用
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama 服务不可用: {e}")
            return False


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    本地嵌入提供者
    
    使用 sentence-transformers 本地模型生成文本嵌入
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化本地嵌入提供者
        
        Args:
            model_name: sentence-transformers 模型名称
        """
        self.model_name = model_name
        self._model = None
    
    def _get_model(self):
        """
        获取或加载模型
        
        Returns:
            sentence-transformers 模型实例
        """
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"加载本地嵌入模型: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers 包未安装，请运行: pip install sentence-transformers"
                )
        
        return self._model
    
    async def embed(self, text: str, **kwargs) -> List[float]:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 待向量化的文本
            **kwargs: 其他参数
            
        Returns:
            嵌入向量
        """
        model = self._get_model()
        
        # sentence-transformers 是同步的，在异步环境中运行
        import asyncio
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, convert_to_numpy=True).tolist()
        )
        
        return embedding
    
    async def embed_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 待向量化的文本列表
            **kwargs: 其他参数
            
        Returns:
            嵌入向量列表
        """
        model = self._get_model()
        
        import asyncio
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts, convert_to_numpy=True).tolist()
        )
        
        return embeddings
    
    async def check_status(self) -> bool:
        """
        检查模型状态
        
        Returns:
            模型是否可用
        """
        try:
            self._get_model()
            return True
        except Exception as e:
            logger.warning(f"本地嵌入模型不可用: {e}")
            return False


class EmbeddingCache:
    """
    嵌入缓存类
    
    缓存已生成的嵌入向量，避免重复计算
    """
    
    def __init__(self, max_size: int = 10000):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self._cache: Dict[str, List[float]] = {}
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """
        生成缓存键
        
        Args:
            text: 文本内容
            model: 模型名称
            
        Returns:
            缓存键
        """
        content = f"{model}:{text}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    
    def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        获取缓存的嵌入
        
        Args:
            text: 文本内容
            model: 模型名称
            
        Returns:
            缓存的嵌入向量，不存在则返回 None
        """
        key = self._get_cache_key(text, model)
        return self._cache.get(key)
    
    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """
        设置缓存
        
        Args:
            text: 文本内容
            model: 模型名称
            embedding: 嵌入向量
        """
        # 如果缓存已满，清除部分旧缓存
        if len(self._cache) >= self.max_size:
            # 简单策略：清除一半的缓存
            keys_to_remove = list(self._cache.keys())[:self.max_size // 2]
            for key in keys_to_remove:
                del self._cache[key]
        
        key = self._get_cache_key(text, model)
        self._cache[key] = embedding
    
    def clear(self) -> None:
        """
        清空缓存
        """
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
        }


class EmbeddingService:
    """
    嵌入服务类
    
    提供统一的文本向量化接口，支持多种嵌入模型
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        初始化嵌入服务
        
        Args:
            config: 嵌入配置
        """
        self.config = config or EmbeddingConfig()
        self._providers: Dict[EmbeddingModelType, BaseEmbeddingProvider] = {}
        self._cache = EmbeddingCache() if self.config.cache_enabled else None
        
        logger.info(
            f"初始化嵌入服务: model={self.config.model_type.value}, "
            f"dimension={self.config.dimension}"
        )
    
    def _get_provider(self, model_type: Optional[EmbeddingModelType] = None) -> BaseEmbeddingProvider:
        """
        获取嵌入提供者
        
        Args:
            model_type: 模型类型，None 表示使用默认配置
            
        Returns:
            嵌入提供者实例
        """
        model_type = model_type or self.config.model_type
        
        if model_type not in self._providers:
            self._providers[model_type] = self._create_provider(model_type)
        
        return self._providers[model_type]
    
    def _create_provider(self, model_type: EmbeddingModelType) -> BaseEmbeddingProvider:
        """
        创建嵌入提供者
        
        Args:
            model_type: 模型类型
            
        Returns:
            嵌入提供者实例
        """
        if model_type in [EmbeddingModelType.OPENAI_ADA002, 
                          EmbeddingModelType.OPENAI_3_SMALL,
                          EmbeddingModelType.OPENAI_3_LARGE]:
            return OpenAIEmbeddingProvider(
                model=model_type.value,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        
        elif model_type in [EmbeddingModelType.OLLAMA_NOMIC,
                            EmbeddingModelType.OLLAMA_MXBAI]:
            return OllamaEmbeddingProvider(
                model=model_type.value,
                base_url=self.config.base_url,
            )
        
        elif model_type == EmbeddingModelType.LOCAL_SENTENCE:
            return LocalEmbeddingProvider()
        
        else:
            raise ValueError(f"不支持的嵌入模型类型: {model_type}")
    
    async def embed(
        self,
        text: str,
        model_type: Optional[EmbeddingModelType] = None,
        **kwargs,
    ) -> EmbeddingResult:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 待向量化的文本
            model_type: 模型类型，None 表示使用默认配置
            **kwargs: 其他参数
            
        Returns:
            嵌入结果
        """
        model_type = model_type or self.config.model_type
        model_name = model_type.value
        
        # 检查缓存
        if self._cache:
            cached_embedding = self._cache.get(text, model_name)
            if cached_embedding is not None:
                return EmbeddingResult(
                    embedding=cached_embedding,
                    model=model_name,
                    dimension=len(cached_embedding),
                    cached=True,
                )
        
        # 调用提供者生成嵌入
        provider = self._get_provider(model_type)
        embedding = await provider.embed(text, **kwargs)
        
        # 存入缓存
        if self._cache:
            self._cache.set(text, model_name, embedding)
        
        return EmbeddingResult(
            embedding=embedding,
            model=model_name,
            dimension=len(embedding),
            tokens_used=len(text.split()),  # 简单估算
            cached=False,
        )
    
    async def embed_batch(
        self,
        texts: List[str],
        model_type: Optional[EmbeddingModelType] = None,
        **kwargs,
    ) -> List[EmbeddingResult]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 待向量化的文本列表
            model_type: 模型类型，None 表示使用默认配置
            **kwargs: 其他参数
            
        Returns:
            嵌入结果列表
        """
        if not texts:
            return []
        
        model_type = model_type or self.config.model_type
        model_name = model_type.value
        
        results = []
        texts_to_embed = []
        indices_to_embed = []
        
        # 检查缓存
        for i, text in enumerate(texts):
            if self._cache:
                cached_embedding = self._cache.get(text, model_name)
                if cached_embedding is not None:
                    results.append((i, EmbeddingResult(
                        embedding=cached_embedding,
                        model=model_name,
                        dimension=len(cached_embedding),
                        cached=True,
                    )))
                    continue
            
            texts_to_embed.append(text)
            indices_to_embed.append(i)
        
        # 批量生成嵌入
        if texts_to_embed:
            provider = self._get_provider(model_type)
            
            # 分批处理
            batch_size = self.config.batch_size
            for i in range(0, len(texts_to_embed), batch_size):
                batch_texts = texts_to_embed[i:i + batch_size]
                batch_indices = indices_to_embed[i:i + batch_size]
                
                embeddings = await provider.embed_batch(batch_texts, **kwargs)
                
                for j, (text, embedding) in enumerate(zip(batch_texts, embeddings)):
                    idx = batch_indices[j]
                    
                    # 存入缓存
                    if self._cache:
                        self._cache.set(text, model_name, embedding)
                    
                    results.append((idx, EmbeddingResult(
                        embedding=embedding,
                        model=model_name,
                        dimension=len(embedding),
                        tokens_used=len(text.split()),
                        cached=False,
                    )))
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        
        return [r[1] for r in results]
    
    async def check_status(self, model_type: Optional[EmbeddingModelType] = None) -> bool:
        """
        检查嵌入服务状态
        
        Args:
            model_type: 模型类型，None 表示使用默认配置
            
        Returns:
            服务是否可用
        """
        try:
            provider = self._get_provider(model_type)
            return await provider.check_status()
        except Exception as e:
            logger.error(f"检查嵌入服务状态失败: {e}")
            return False
    
    def get_dimension(self, model_type: Optional[EmbeddingModelType] = None) -> int:
        """
        获取模型维度
        
        Args:
            model_type: 模型类型，None 表示使用默认配置
            
        Returns:
            向量维度
        """
        model_type = model_type or self.config.model_type
        return EmbeddingConfig.MODEL_DIMENSIONS.get(model_type, 1536)
    
    def clear_cache(self) -> None:
        """
        清空嵌入缓存
        """
        if self._cache:
            self._cache.clear()
            logger.info("嵌入缓存已清空")
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息，未启用缓存则返回 None
        """
        if self._cache:
            return self._cache.get_stats()
        return None


# 创建全局嵌入服务实例
embedding_service = EmbeddingService()
