"""
LLM 适配器工厂
使用工厂模式创建和管理模型适配器实例
"""
from typing import Any, Dict, Optional, Type

from loguru import logger

from app.services.llm.base import BaseLLMAdapter, LLMError
from app.services.llm.deepseek_adapter import DeepSeekAdapter
from app.services.llm.ollama_adapter import OllamaAdapter
from app.services.llm.openai_adapter import OpenAIAdapter


class LLMFactory:
    """
    LLM 适配器工厂类
    
    负责创建和管理不同提供商的 LLM 适配器实例。
    支持模型热切换、实例缓存和配置管理。
    
    使用示例:
        factory = LLMFactory()
        
        # 创建 OpenAI 适配器
        adapter = factory.create_adapter(
            provider="openai",
            model_name="gpt-4",
            api_key="sk-xxx",
        )
        
        # 使用适配器
        response = await adapter.chat([{"role": "user", "content": "Hello"}])
    """
    
    # 支持的提供商及其适配器类
    PROVIDERS: Dict[str, Type[BaseLLMAdapter]] = {
        "ollama": OllamaAdapter,
        "openai": OpenAIAdapter,
        "deepseek": DeepSeekAdapter,
    }
    
    # 提供商别名映射
    PROVIDER_ALIASES = {
        "local": "ollama",
        "ollama": "ollama",
        "gpt": "openai",
        "openai": "openai",
        "deepseek": "deepseek",
        "deep-seek": "deepseek",
    }
    
    def __init__(self):
        """
        初始化 LLM 工厂
        """
        # 适配器实例缓存
        # key: f"{provider}:{model_name}"
        # value: BaseLLMAdapter 实例
        self._instances: Dict[str, BaseLLMAdapter] = {}
        
        logger.info(f"LLM 工厂初始化完成，支持提供商: {list(self.PROVIDERS.keys())}")
    
    def create_adapter(
        self,
        provider: str,
        model_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> BaseLLMAdapter:
        """
        创建或获取 LLM 适配器实例
        
        如果相同配置的适配器已存在，则返回缓存的实例。
        
        Args:
            provider: 提供商名称（如 ollama, openai, deepseek）
            model_name: 模型名称
            api_key: API 密钥（可选，本地模型不需要）
            base_url: API 基础 URL（可选）
            **kwargs: 其他配置参数
            
        Returns:
            LLM 适配器实例
            
        Raises:
            LLMError: 不支持的提供商或配置错误
        """
        # 标准化提供商名称
        provider = self._normalize_provider(provider)
        
        # 检查提供商是否支持
        if provider not in self.PROVIDERS:
            raise LLMError(
                f"不支持的 LLM 提供商: {provider}，"
                f"支持的提供商: {list(self.PROVIDERS.keys())}"
            )
        
        # 生成缓存键
        cache_key = self._generate_cache_key(provider, model_name, api_key, base_url)
        
        # 检查缓存
        if cache_key in self._instances:
            logger.debug(f"返回缓存的适配器实例: {cache_key}")
            return self._instances[cache_key]
        
        # 创建新实例
        adapter_class = self.PROVIDERS[provider]
        
        try:
            adapter = adapter_class(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **kwargs,
            )
            
            # 缓存实例
            self._instances[cache_key] = adapter
            
            logger.info(f"创建新的 LLM 适配器: provider={provider}, model={model_name}")
            
            return adapter
            
        except Exception as e:
            logger.error(f"创建 LLM 适配器失败: {e}")
            raise LLMError(f"创建 LLM 适配器失败: {e}") from e
    
    def get_adapter(
        self,
        provider: str,
        model_name: str,
    ) -> Optional[BaseLLMAdapter]:
        """
        获取已缓存的适配器实例
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            
        Returns:
            缓存的适配器实例，如果不存在则返回 None
        """
        provider = self._normalize_provider(provider)
        cache_key = f"{provider}:{model_name}"
        
        return self._instances.get(cache_key)
    
    def remove_adapter(
        self,
        provider: str,
        model_name: str,
    ) -> bool:
        """
        移除缓存的适配器实例
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            
        Returns:
            是否成功移除
        """
        provider = self._normalize_provider(provider)
        cache_key = f"{provider}:{model_name}"
        
        if cache_key in self._instances:
            del self._instances[cache_key]
            logger.info(f"移除 LLM 适配器缓存: {cache_key}")
            return True
        
        return False
    
    async def close_adapter(
        self,
        provider: str,
        model_name: str,
    ) -> bool:
        """
        关闭并移除适配器实例
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            
        Returns:
            是否成功关闭
        """
        adapter = self.get_adapter(provider, model_name)
        
        if adapter:
            try:
                await adapter.close()
            except Exception as e:
                logger.warning(f"关闭适配器时出错: {e}")
            
            return self.remove_adapter(provider, model_name)
        
        return False
    
    async def close_all(self) -> None:
        """
        关闭所有适配器实例
        """
        for key, adapter in list(self._instances.items()):
            try:
                await adapter.close()
                logger.debug(f"关闭适配器: {key}")
            except Exception as e:
                logger.warning(f"关闭适配器 {key} 时出错: {e}")
        
        self._instances.clear()
        logger.info("已关闭所有 LLM 适配器")
    
    def list_instances(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有缓存的适配器实例
        
        Returns:
            实例信息字典
        """
        result = {}
        
        for key, adapter in self._instances.items():
            result[key] = {
                "model_name": adapter.model_name,
                "base_url": adapter.base_url,
                "max_tokens": adapter.max_tokens,
                "temperature": adapter.temperature,
            }
        
        return result
    
    def get_supported_providers(self) -> Dict[str, Any]:
        """
        获取支持的提供商列表
        
        Returns:
            提供商信息字典
        """
        return {
            "providers": list(self.PROVIDERS.keys()),
            "aliases": self.PROVIDER_ALIASES,
        }
    
    def _normalize_provider(self, provider: str) -> str:
        """
        标准化提供商名称
        
        Args:
            provider: 原始提供商名称
            
        Returns:
            标准化后的提供商名称
        """
        provider_lower = provider.lower().strip()
        return self.PROVIDER_ALIASES.get(provider_lower, provider_lower)
    
    def _generate_cache_key(
        self,
        provider: str,
        model_name: str,
        api_key: Optional[str],
        base_url: Optional[str],
    ) -> str:
        """
        生成缓存键
        
        Args:
            provider: 提供商名称
            model_name: 模型名称
            api_key: API 密钥
            base_url: 基础 URL
            
        Returns:
            缓存键字符串
        """
        # 对于本地模型（Ollama），不包含 API 密钥
        if provider == "ollama":
            return f"{provider}:{model_name}:{base_url or 'default'}"
        
        # 对于需要 API 密钥的提供商，包含密钥的哈希
        key_hash = hash(api_key) if api_key else "no_key"
        return f"{provider}:{model_name}:{key_hash}:{base_url or 'default'}"


# 全局工厂实例
_factory: Optional[LLMFactory] = None


def get_factory() -> LLMFactory:
    """
    获取全局 LLM 工厂实例
    
    Returns:
        LLMFactory 实例
    """
    global _factory
    if _factory is None:
        _factory = LLMFactory()
    return _factory


def create_adapter(
    provider: str,
    model_name: str,
    **kwargs,
) -> BaseLLMAdapter:
    """
    便捷函数：创建 LLM 适配器
    
    Args:
        provider: 提供商名称
        model_name: 模型名称
        **kwargs: 其他参数
        
    Returns:
        LLM 适配器实例
    """
    return get_factory().create_adapter(provider, model_name, **kwargs)


def create_from_config(config: Dict[str, Any]) -> BaseLLMAdapter:
    """
    从配置字典创建 LLM 适配器
    
    Args:
        config: 配置字典，包含 provider, model_name 等字段
        
    Returns:
        LLM 适配器实例
    """
    provider = config.get("provider")
    model_name = config.get("model_name") or config.get("name")
    
    if not provider or not model_name:
        raise LLMError("配置必须包含 provider 和 model_name 字段")
    
    # 提取其他配置
    kwargs = {
        k: v for k, v in config.items()
        if k not in ["provider", "model_name", "name"]
    }
    
    return create_adapter(provider, model_name, **kwargs)
