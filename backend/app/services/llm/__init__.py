"""
LLM 服务模块
提供统一的 AI 模型适配器接口
"""
from app.services.llm.base import (
    BaseLLMAdapter,
    LLMConnectionError,
    LLMError,
    LLMModelNotFoundError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.services.llm.deepseek_adapter import DeepSeekAdapter
from app.services.llm.llm_factory import (
    LLMFactory,
    create_adapter,
    create_from_config,
    get_factory,
)
from app.services.llm.ollama_adapter import OllamaAdapter
from app.services.llm.openai_adapter import OpenAIAdapter

# 模块公开的接口
__all__ = [
    # 基类和异常
    "BaseLLMAdapter",
    "LLMError",
    "LLMConnectionError",
    "LLMResponseError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMModelNotFoundError",
    # 适配器
    "OllamaAdapter",
    "OpenAIAdapter",
    "DeepSeekAdapter",
    # 工厂
    "LLMFactory",
    "get_factory",
    "create_adapter",
    "create_from_config",
]
