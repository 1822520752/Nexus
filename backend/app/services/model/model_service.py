"""
模型配置管理服务
提供模型配置的 CRUD 操作、API Key 加密存储、状态检测和监控功能
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value, encrypt_value
from app.models.model_config import ModelConfig
from app.services.llm.base import LLMError
from app.services.llm.llm_factory import LLMFactory, get_factory


class ModelService:
    """
    模型配置管理服务类
    
    提供以下功能：
    - 模型配置的 CRUD 操作
    - API Key 加密存储
    - 默认模型设置
    - 模型配置验证
    - 模型状态检测和监控
    - 模型列表获取（本地/云端）
    """
    
    # 支持的提供商配置
    SUPPORTED_PROVIDERS = {
        "ollama": {
            "name": "Ollama",
            "description": "本地部署的 Ollama 模型服务",
            "requires_api_key": False,
            "default_base_url": "http://localhost:11434",
            "supports_local": True,
        },
        "openai": {
            "name": "OpenAI",
            "description": "OpenAI GPT 系列模型",
            "requires_api_key": True,
            "default_base_url": "https://api.openai.com/v1",
            "supports_local": False,
        },
        "deepseek": {
            "name": "DeepSeek",
            "description": "DeepSeek AI 模型",
            "requires_api_key": True,
            "default_base_url": "https://api.deepseek.com/v1",
            "supports_local": False,
        },
        "anthropic": {
            "name": "Anthropic",
            "description": "Anthropic Claude 系列模型",
            "requires_api_key": True,
            "default_base_url": "https://api.anthropic.com/v1",
            "supports_local": False,
        },
        "custom": {
            "name": "自定义",
            "description": "自定义 OpenAI 兼容 API",
            "requires_api_key": True,
            "default_base_url": "",
            "supports_local": False,
        },
    }
    
    # 模型状态缓存（内存缓存，避免频繁请求）
    _status_cache: Dict[int, Dict[str, Any]] = {}
    _cache_ttl: int = 60  # 缓存有效期（秒）
    
    def __init__(self, db: AsyncSession):
        """
        初始化模型服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self._llm_factory: Optional[LLMFactory] = None
    
    @property
    def llm_factory(self) -> LLMFactory:
        """
        获取 LLM 工厂实例
        
        Returns:
            LLMFactory 实例
        """
        if self._llm_factory is None:
            self._llm_factory = get_factory()
        return self._llm_factory
    
    # ==================== CRUD 操作 ====================
    
    async def create_model(
        self,
        name: str,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_type: str = "chat",
        is_default: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        context_window: int = 8192,
        config: Optional[Dict[str, Any]] = None,
    ) -> ModelConfig:
        """
        创建新的模型配置
        
        Args:
            name: 模型名称
            provider: 提供商（ollama, openai, deepseek, anthropic, custom）
            api_key: API 密钥（将自动加密存储）
            base_url: API 基础 URL
            model_type: 模型类型（chat, embedding, image, audio）
            is_default: 是否设为默认模型
            max_tokens: 最大 Token 数
            temperature: 温度参数
            context_window: 上下文窗口大小
            config: 其他配置
            
        Returns:
            创建的模型配置实例
            
        Raises:
            ValueError: 参数验证失败
        """
        # 验证提供商
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的提供商: {provider}，支持的提供商: {list(self.SUPPORTED_PROVIDERS.keys())}")
        
        provider_config = self.SUPPORTED_PROVIDERS[provider]
        
        # 验证 API Key
        if provider_config["requires_api_key"] and not api_key:
            raise ValueError(f"提供商 {provider} 需要提供 API Key")
        
        # 设置默认 base_url
        if not base_url and provider_config["default_base_url"]:
            base_url = provider_config["default_base_url"]
        
        # 如果设为默认，先取消其他默认模型
        if is_default:
            await self._clear_default_models()
        
        # 创建模型配置
        model = ModelConfig(
            name=name,
            provider=provider,
            model_type=model_type,
            base_url=base_url,
            is_default=is_default,
            is_active=True,
            max_tokens=max_tokens,
            temperature=temperature,
            context_window=context_window,
            config=json.dumps(config) if config else None,
        )
        
        # 加密存储 API Key
        if api_key:
            model.api_key = api_key  # 通过 setter 自动加密
        
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        
        logger.info(f"创建模型配置成功: id={model.id}, name={name}, provider={provider}")
        
        return model
    
    async def get_model_by_id(self, model_id: int) -> Optional[ModelConfig]:
        """
        根据 ID 获取模型配置
        
        Args:
            model_id: 模型配置 ID
            
        Returns:
            模型配置实例，不存在则返回 None
        """
        query = select(ModelConfig).where(ModelConfig.id == model_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_model_by_name(self, name: str) -> Optional[ModelConfig]:
        """
        根据名称获取模型配置
        
        Args:
            name: 模型名称
            
        Returns:
            模型配置实例，不存在则返回 None
        """
        query = select(ModelConfig).where(ModelConfig.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_models(
        self,
        provider: Optional[str] = None,
        model_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_inactive: bool = False,
    ) -> List[ModelConfig]:
        """
        获取模型配置列表
        
        Args:
            provider: 按提供商筛选
            model_type: 按模型类型筛选
            is_active: 按启用状态筛选
            include_inactive: 是否包含未启用的模型
            
        Returns:
            模型配置列表
        """
        query = select(ModelConfig)
        
        # 应用筛选条件
        if provider:
            query = query.where(ModelConfig.provider == provider)
        if model_type:
            query = query.where(ModelConfig.model_type == model_type)
        if is_active is not None:
            query = query.where(ModelConfig.is_active == is_active)
        elif not include_inactive:
            query = query.where(ModelConfig.is_active == True)
        
        # 按默认模型优先，然后按创建时间降序
        query = query.order_by(ModelConfig.is_default.desc(), ModelConfig.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def update_model(
        self,
        model_id: int,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        is_default: Optional[bool] = None,
        is_active: Optional[bool] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        context_window: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModelConfig]:
        """
        更新模型配置
        
        Args:
            model_id: 模型配置 ID
            name: 新的模型名称
            api_key: 新的 API 密钥（将自动加密存储）
            base_url: 新的 API 基础 URL
            is_default: 是否设为默认模型
            is_active: 是否启用
            max_tokens: 最大 Token 数
            temperature: 温度参数
            context_window: 上下文窗口大小
            config: 其他配置
            
        Returns:
            更新后的模型配置实例，不存在则返回 None
        """
        model = await self.get_model_by_id(model_id)
        if not model:
            return None
        
        # 如果设为默认，先取消其他默认模型
        if is_default:
            await self._clear_default_models()
        
        # 更新字段
        if name is not None:
            model.name = name
        if api_key is not None:
            model.api_key = api_key  # 通过 setter 自动加密
        if base_url is not None:
            model.base_url = base_url
        if is_default is not None:
            model.is_default = is_default
        if is_active is not None:
            model.is_active = is_active
        if max_tokens is not None:
            model.max_tokens = max_tokens
        if temperature is not None:
            model.temperature = temperature
        if context_window is not None:
            model.context_window = context_window
        if config is not None:
            model.config = json.dumps(config)
        
        await self.db.flush()
        await self.db.refresh(model)
        
        logger.info(f"更新模型配置成功: id={model_id}")
        
        return model
    
    async def delete_model(self, model_id: int) -> bool:
        """
        删除模型配置
        
        Args:
            model_id: 模型配置 ID
            
        Returns:
            是否删除成功
        """
        model = await self.get_model_by_id(model_id)
        if not model:
            return False
        
        await self.db.delete(model)
        await self.db.flush()
        
        logger.info(f"删除模型配置成功: id={model_id}")
        
        return True
    
    async def set_default_model(self, model_id: int) -> Optional[ModelConfig]:
        """
        设置默认模型
        
        Args:
            model_id: 模型配置 ID
            
        Returns:
            更新后的模型配置实例，不存在则返回 None
        """
        model = await self.get_model_by_id(model_id)
        if not model:
            return None
        
        # 取消其他默认模型
        await self._clear_default_models()
        
        # 设置当前模型为默认
        model.is_default = True
        await self.db.flush()
        await self.db.refresh(model)
        
        logger.info(f"设置默认模型成功: id={model_id}, name={model.name}")
        
        return model
    
    async def get_default_model(self) -> Optional[ModelConfig]:
        """
        获取默认模型配置
        
        Returns:
            默认模型配置实例，不存在则返回 None
        """
        query = select(ModelConfig).where(
            ModelConfig.is_default == True,
            ModelConfig.is_active == True,
        )
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()
        
        # 如果没有默认模型，返回第一个启用的模型
        if not model:
            query = select(ModelConfig).where(ModelConfig.is_active == True).limit(1)
            result = await self.db.execute(query)
            model = result.scalar_one_or_none()
        
        return model
    
    async def _clear_default_models(self) -> None:
        """
        清除所有默认模型标记
        """
        stmt = update(ModelConfig).values(is_default=False)
        await self.db.execute(stmt)
    
    # ==================== 模型状态检测 ====================
    
    async def check_model_status(self, model_id: int) -> Dict[str, Any]:
        """
        检测模型状态
        
        Args:
            model_id: 模型配置 ID
            
        Returns:
            包含状态信息的字典
        """
        model = await self.get_model_by_id(model_id)
        if not model:
            return {
                "status": "not_found",
                "available": False,
                "message": "模型配置不存在",
            }
        
        # 检查缓存
        cache_key = model_id
        if cache_key in self._status_cache:
            cached = self._status_cache[cache_key]
            cache_time = cached.get("timestamp", 0)
            if datetime.now().timestamp() - cache_time < self._cache_ttl:
                return cached.get("data", {})
        
        # 执行状态检测
        status_info = await self._do_status_check(model)
        
        # 更新缓存
        self._status_cache[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "data": status_info,
        }
        
        return status_info
    
    async def _do_status_check(self, model: ModelConfig) -> Dict[str, Any]:
        """
        执行实际的状态检测
        
        Args:
            model: 模型配置实例
            
        Returns:
            状态信息字典
        """
        try:
            # 创建适配器进行状态检测
            adapter = self.llm_factory.create_adapter(
                provider=model.provider,
                model_name=model.name,
                api_key=model.api_key,
                base_url=model.base_url,
                max_tokens=model.max_tokens,
                temperature=model.temperature,
                context_window=model.context_window,
            )
            
            # 检查状态
            is_available = await adapter.check_status()
            
            if is_available:
                # 获取模型信息
                model_info = await adapter.get_model_info()
                return {
                    "status": "available",
                    "available": True,
                    "message": "模型服务正常",
                    "model_info": model_info,
                    "checked_at": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "unavailable",
                    "available": False,
                    "message": "模型服务不可用",
                    "checked_at": datetime.now().isoformat(),
                }
                
        except LLMError as e:
            return {
                "status": "error",
                "available": False,
                "message": f"模型连接错误: {str(e)}",
                "error": str(e),
                "checked_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"检测模型状态失败: {e}")
            return {
                "status": "error",
                "available": False,
                "message": f"检测失败: {str(e)}",
                "error": str(e),
                "checked_at": datetime.now().isoformat(),
            }
    
    async def test_model_connection(self, model_id: int) -> Dict[str, Any]:
        """
        测试模型连接
        
        Args:
            model_id: 模型配置 ID
            
        Returns:
            测试结果字典
        """
        model = await self.get_model_by_id(model_id)
        if not model:
            return {
                "success": False,
                "message": "模型配置不存在",
            }
        
        try:
            # 创建适配器
            adapter = self.llm_factory.create_adapter(
                provider=model.provider,
                model_name=model.name,
                api_key=model.api_key,
                base_url=model.base_url,
                max_tokens=model.max_tokens,
                temperature=model.temperature,
                context_window=model.context_window,
            )
            
            # 发送测试消息
            test_message = [{"role": "user", "content": "Hello, this is a connection test. Please respond with 'OK'."}]
            response = await adapter.chat(test_message, max_tokens=50)
            
            return {
                "success": True,
                "message": "连接测试成功",
                "response": response[:200] if response else None,  # 截取前200字符
                "tested_at": datetime.now().isoformat(),
            }
            
        except LLMError as e:
            return {
                "success": False,
                "message": f"连接测试失败: {str(e)}",
                "error": str(e),
                "tested_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"测试模型连接失败: {e}")
            return {
                "success": False,
                "message": f"测试失败: {str(e)}",
                "error": str(e),
                "tested_at": datetime.now().isoformat(),
            }
    
    # ==================== 获取模型列表 ====================
    
    async def get_available_models(self, provider: str) -> List[Dict[str, Any]]:
        """
        获取指定提供商的可用模型列表
        
        Args:
            provider: 提供商名称
            
        Returns:
            可用模型列表
        """
        if provider == "ollama":
            return await self._get_ollama_models()
        elif provider == "openai":
            return await self._get_openai_models()
        elif provider == "deepseek":
            return self._get_deepseek_models()
        else:
            return []
    
    async def _get_ollama_models(self) -> List[Dict[str, Any]]:
        """
        获取 Ollama 可用模型列表
        
        Returns:
            Ollama 模型列表
        """
        try:
            from app.services.llm.ollama_adapter import OllamaAdapter
            
            # 创建临时适配器获取模型列表
            adapter = OllamaAdapter(model_name="temp")
            models = await adapter.list_models()
            
            return [
                {
                    "name": model.get("name"),
                    "size": model.get("size"),
                    "modified_at": model.get("modified_at"),
                    "digest": model.get("digest"),
                }
                for model in models
            ]
        except Exception as e:
            logger.warning(f"获取 Ollama 模型列表失败: {e}")
            return []
    
    async def _get_openai_models(self) -> List[Dict[str, Any]]:
        """
        获取 OpenAI 可用模型列表
        
        Returns:
            OpenAI 模型列表
        """
        # 返回常用模型列表（实际 API 需要有效的 API Key）
        return [
            {"name": "gpt-4", "description": "GPT-4 最强大的模型"},
            {"name": "gpt-4-turbo", "description": "GPT-4 Turbo 更快更便宜"},
            {"name": "gpt-4o", "description": "GPT-4 Omni 多模态模型"},
            {"name": "gpt-4o-mini", "description": "GPT-4 Omni Mini 轻量版"},
            {"name": "gpt-3.5-turbo", "description": "GPT-3.5 Turbo 快速经济"},
        ]
    
    def _get_deepseek_models(self) -> List[Dict[str, Any]]:
        """
        获取 DeepSeek 可用模型列表
        
        Returns:
            DeepSeek 模型列表
        """
        return [
            {"name": "deepseek-chat", "description": "DeepSeek Chat 对话模型"},
            {"name": "deepseek-coder", "description": "DeepSeek Coder 代码模型"},
        ]
    
    # ==================== 配置验证 ====================
    
    def validate_model_config(
        self,
        provider: str,
        name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        验证模型配置
        
        Args:
            provider: 提供商
            name: 模型名称
            api_key: API 密钥
            base_url: API 基础 URL
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查提供商
        if provider not in self.SUPPORTED_PROVIDERS:
            return False, f"不支持的提供商: {provider}"
        
        provider_config = self.SUPPORTED_PROVIDERS[provider]
        
        # 检查 API Key
        if provider_config["requires_api_key"] and not api_key:
            return False, f"提供商 {provider} 需要提供 API Key"
        
        # 检查模型名称
        if not name or not name.strip():
            return False, "模型名称不能为空"
        
        return True, None
    
    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        获取提供商配置信息
        
        Args:
            provider: 提供商名称
            
        Returns:
            提供商配置信息
        """
        return self.SUPPORTED_PROVIDERS.get(provider)
    
    def get_supported_providers(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有支持的提供商列表
        
        Returns:
            提供商配置字典
        """
        return self.SUPPORTED_PROVIDERS.copy()
    
    # ==================== 辅助方法 ====================
    
    def clear_status_cache(self, model_id: Optional[int] = None) -> None:
        """
        清除状态缓存
        
        Args:
            model_id: 指定模型 ID，为 None 则清除所有缓存
        """
        if model_id is not None:
            self._status_cache.pop(model_id, None)
        else:
            self._status_cache.clear()


# 创建服务实例的工厂函数
def get_model_service(db: AsyncSession) -> ModelService:
    """
    获取模型服务实例
    
    Args:
        db: 异步数据库会话
        
    Returns:
        ModelService 实例
    """
    return ModelService(db)


# 全局模型服务实例（用于简单场景）
_model_service: Optional[ModelService] = None


def model_service(db: AsyncSession) -> ModelService:
    """
    获取模型服务实例的便捷函数
    
    Args:
        db: 异步数据库会话
        
    Returns:
        ModelService 实例
    """
    return ModelService(db)
