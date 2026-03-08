"""
动作注册表
提供动作注册、发现和元数据管理
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime

from app.core.logger import logger


class ActionCategory(str, Enum):
    """
    动作类别枚举
    
    定义动作的分类
    """
    
    FILE = "file"               # 文件操作
    NOTE = "note"               # 笔记操作
    SYSTEM = "system"           # 系统操作
    SCRIPT = "script"           # 脚本执行
    NETWORK = "network"         # 网络操作
    DATABASE = "database"       # 数据库操作
    CUSTOM = "custom"           # 自定义操作


@dataclass
class ActionParameter:
    """
    动作参数定义
    
    描述动作的输入参数
    """
    
    name: str                                   # 参数名称
    type: str                                   # 参数类型 (str, int, bool, list, dict 等)
    description: str                            # 参数描述
    required: bool = True                       # 是否必需
    default: Any = None                         # 默认值
    choices: Optional[List[str]] = None         # 可选值列表
    min_value: Optional[Union[int, float]] = None  # 最小值
    max_value: Optional[Union[int, float]] = None  # 最大值
    pattern: Optional[str] = None               # 正则表达式验证模式
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含参数信息的字典
        """
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "choices": self.choices,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "pattern": self.pattern,
        }


@dataclass
class ActionMetadata:
    """
    动作元数据
    
    描述动作的完整信息
    """
    
    name: str                                   # 动作名称（唯一标识）
    display_name: str                           # 显示名称
    description: str                            # 动作描述
    category: ActionCategory                    # 动作类别
    parameters: List[ActionParameter] = field(default_factory=list)  # 参数列表
    returns: str = ""                           # 返回值描述
    examples: List[Dict[str, Any]] = field(default_factory=list)     # 使用示例
    tags: List[str] = field(default_factory=list)                    # 标签
    version: str = "1.0.0"                      # 版本号
    author: str = "Nexus"                       # 作者
    requires_confirmation: bool = False         # 是否需要确认
    is_dangerous: bool = False                  # 是否危险操作
    is_enabled: bool = True                     # 是否启用
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含元数据的字典
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.to_dict() for p in self.parameters],
            "returns": self.returns,
            "examples": self.examples,
            "tags": self.tags,
            "version": self.version,
            "author": self.author,
            "requires_confirmation": self.requires_confirmation,
            "is_dangerous": self.is_dangerous,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ActionResult:
    """
    动作执行结果
    
    包含动作执行的完整结果信息
    """
    
    success: bool                               # 是否成功
    data: Any = None                            # 返回数据
    message: str = ""                           # 结果消息
    error: Optional[str] = None                 # 错误信息
    duration_ms: int = 0                        # 执行耗时（毫秒）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含结果的字典
        """
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


# 动作执行函数类型
ActionExecutor = Callable[..., ActionResult]


class ActionRegistry:
    """
    动作注册表
    
    管理所有预定义动作的注册、发现和执行
    """
    
    def __init__(self):
        """
        初始化动作注册表
        """
        self._actions: Dict[str, ActionMetadata] = {}
        self._executors: Dict[str, ActionExecutor] = {}
        self._categories: Dict[ActionCategory, List[str]] = {
            cat: [] for cat in ActionCategory
        }
        
        logger.info("动作注册表初始化完成")
    
    def register(
        self,
        name: str,
        display_name: str,
        description: str,
        category: ActionCategory,
        executor: ActionExecutor,
        parameters: Optional[List[ActionParameter]] = None,
        returns: str = "",
        examples: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        requires_confirmation: bool = False,
        is_dangerous: bool = False,
    ) -> None:
        """
        注册动作
        
        Args:
            name: 动作名称（唯一标识）
            display_name: 显示名称
            description: 动作描述
            category: 动作类别
            executor: 执行函数
            parameters: 参数列表
            returns: 返回值描述
            examples: 使用示例
            tags: 标签
            requires_confirmation: 是否需要确认
            is_dangerous: 是否危险操作
        """
        if name in self._actions:
            logger.warning(f"动作已存在，将覆盖: {name}")
        
        # 创建元数据
        metadata = ActionMetadata(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            parameters=parameters or [],
            returns=returns,
            examples=examples or [],
            tags=tags or [],
            requires_confirmation=requires_confirmation,
            is_dangerous=is_dangerous,
        )
        
        # 注册动作
        self._actions[name] = metadata
        self._executors[name] = executor
        
        # 添加到类别索引
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        logger.info(f"注册动作: {name} ({category.value})")
    
    def unregister(self, name: str) -> bool:
        """
        注销动作
        
        Args:
            name: 动作名称
        
        Returns:
            是否成功注销
        """
        if name not in self._actions:
            logger.warning(f"动作不存在: {name}")
            return False
        
        metadata = self._actions.pop(name)
        self._executors.pop(name, None)
        
        # 从类别索引移除
        if metadata.category in self._categories:
            try:
                self._categories[metadata.category].remove(name)
            except ValueError:
                pass
        
        logger.info(f"注销动作: {name}")
        return True
    
    def get_action(self, name: str) -> Optional[ActionMetadata]:
        """
        获取动作元数据
        
        Args:
            name: 动作名称
        
        Returns:
            动作元数据，不存在则返回 None
        """
        return self._actions.get(name)
    
    def get_executor(self, name: str) -> Optional[ActionExecutor]:
        """
        获取动作执行函数
        
        Args:
            name: 动作名称
        
        Returns:
            执行函数，不存在则返回 None
        """
        return self._executors.get(name)
    
    def list_actions(
        self,
        category: Optional[ActionCategory] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ) -> List[ActionMetadata]:
        """
        列出动作
        
        Args:
            category: 按类别过滤
            tags: 按标签过滤
            enabled_only: 只返回启用的动作
        
        Returns:
            动作元数据列表
        """
        actions = list(self._actions.values())
        
        # 过滤类别
        if category:
            actions = [a for a in actions if a.category == category]
        
        # 过滤标签
        if tags:
            actions = [a for a in actions if any(t in a.tags for t in tags)]
        
        # 过滤启用状态
        if enabled_only:
            actions = [a for a in actions if a.is_enabled]
        
        return actions
    
    def list_by_category(self, category: ActionCategory) -> List[ActionMetadata]:
        """
        按类别列出动作
        
        Args:
            category: 动作类别
        
        Returns:
            该类别的动作列表
        """
        action_names = self._categories.get(category, [])
        return [self._actions[name] for name in action_names if name in self._actions]
    
    def search(self, query: str) -> List[ActionMetadata]:
        """
        搜索动作
        
        Args:
            query: 搜索关键词
        
        Returns:
            匹配的动作列表
        """
        query_lower = query.lower()
        results = []
        
        for metadata in self._actions.values():
            # 搜索名称、描述和标签
            if (
                query_lower in metadata.name.lower()
                or query_lower in metadata.display_name.lower()
                or query_lower in metadata.description.lower()
                or any(query_lower in tag.lower() for tag in metadata.tags)
            ):
                results.append(metadata)
        
        return results
    
    def execute(self, name: str, **kwargs) -> ActionResult:
        """
        执行动作
        
        Args:
            name: 动作名称
            **kwargs: 动作参数
        
        Returns:
            执行结果
        
        Raises:
            ValueError: 动作不存在或参数验证失败
        """
        import time
        
        # 检查动作是否存在
        if name not in self._actions:
            raise ValueError(f"动作不存在: {name}")
        
        metadata = self._actions[name]
        executor = self._executors[name]
        
        # 检查是否启用
        if not metadata.is_enabled:
            raise ValueError(f"动作已禁用: {name}")
        
        # 验证参数
        self._validate_parameters(metadata, kwargs)
        
        logger.info(f"执行动作: {name}, 参数: {kwargs}")
        
        start_time = time.time()
        
        try:
            # 执行动作
            result = executor(**kwargs)
            
            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            result.duration_ms = duration_ms
            
            logger.info(f"动作执行完成: {name}, 耗时: {duration_ms}ms, 成功: {result.success}")
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"动作执行失败: {str(e)}"
            
            logger.error(f"{error_msg}, 动作: {name}")
            
            return ActionResult(
                success=False,
                error=error_msg,
                duration_ms=duration_ms,
            )
    
    async def execute_async(self, name: str, **kwargs) -> ActionResult:
        """
        异步执行动作
        
        Args:
            name: 动作名称
            **kwargs: 动作参数
        
        Returns:
            执行结果
        """
        import asyncio
        import time
        
        # 检查动作是否存在
        if name not in self._actions:
            raise ValueError(f"动作不存在: {name}")
        
        metadata = self._actions[name]
        executor = self._executors[name]
        
        # 检查是否启用
        if not metadata.is_enabled:
            raise ValueError(f"动作已禁用: {name}")
        
        # 验证参数
        self._validate_parameters(metadata, kwargs)
        
        logger.info(f"异步执行动作: {name}, 参数: {kwargs}")
        
        start_time = time.time()
        
        try:
            # 执行动作（支持同步和异步函数）
            import inspect
            if inspect.iscoroutinefunction(executor):
                result = await executor(**kwargs)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: executor(**kwargs)
                )
            
            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            result.duration_ms = duration_ms
            
            logger.info(f"异步动作执行完成: {name}, 耗时: {duration_ms}ms, 成功: {result.success}")
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"异步动作执行失败: {str(e)}"
            
            logger.error(f"{error_msg}, 动作: {name}")
            
            return ActionResult(
                success=False,
                error=error_msg,
                duration_ms=duration_ms,
            )
    
    def _validate_parameters(
        self,
        metadata: ActionMetadata,
        kwargs: Dict[str, Any],
    ) -> None:
        """
        验证参数
        
        Args:
            metadata: 动作元数据
            kwargs: 参数字典
        
        Raises:
            ValueError: 参数验证失败
        """
        import re
        
        for param in metadata.parameters:
            value = kwargs.get(param.name)
            
            # 检查必需参数
            if param.required and value is None:
                raise ValueError(f"缺少必需参数: {param.name}")
            
            # 如果没有值且有默认值，跳过验证
            if value is None and param.default is not None:
                continue
            
            # 如果没有值且非必需，跳过验证
            if value is None and not param.required:
                continue
            
            # 类型验证
            if value is not None:
                type_validators = {
                    "str": lambda v: isinstance(v, str),
                    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
                    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
                    "bool": lambda v: isinstance(v, bool),
                    "list": lambda v: isinstance(v, list),
                    "dict": lambda v: isinstance(v, dict),
                }
                
                validator = type_validators.get(param.type)
                if validator and not validator(value):
                    raise ValueError(
                        f"参数类型错误: {param.name}, 期望 {param.type}, 实际 {type(value).__name__}"
                    )
            
            # 可选值验证
            if param.choices and value not in param.choices:
                raise ValueError(
                    f"参数值无效: {param.name}, 可选值: {param.choices}, 实际: {value}"
                )
            
            # 范围验证
            if isinstance(value, (int, float)):
                if param.min_value is not None and value < param.min_value:
                    raise ValueError(
                        f"参数值过小: {param.name}, 最小值: {param.min_value}, 实际: {value}"
                    )
                if param.max_value is not None and value > param.max_value:
                    raise ValueError(
                        f"参数值过大: {param.name}, 最大值: {param.max_value}, 实际: {value}"
                    )
            
            # 正则表达式验证
            if param.pattern and isinstance(value, str):
                if not re.match(param.pattern, value):
                    raise ValueError(
                        f"参数格式错误: {param.name}, 模式: {param.pattern}"
                    )
    
    def enable_action(self, name: str) -> bool:
        """
        启用动作
        
        Args:
            name: 动作名称
        
        Returns:
            是否成功
        """
        if name not in self._actions:
            return False
        
        self._actions[name].is_enabled = True
        logger.info(f"启用动作: {name}")
        return True
    
    def disable_action(self, name: str) -> bool:
        """
        禁用动作
        
        Args:
            name: 动作名称
        
        Returns:
            是否成功
        """
        if name not in self._actions:
            return False
        
        self._actions[name].is_enabled = False
        logger.info(f"禁用动作: {name}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取注册表统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_actions": len(self._actions),
            "enabled_actions": sum(1 for a in self._actions.values() if a.is_enabled),
            "disabled_actions": sum(1 for a in self._actions.values() if not a.is_enabled),
            "dangerous_actions": sum(1 for a in self._actions.values() if a.is_dangerous),
            "by_category": {
                cat.value: len(actions) for cat, actions in self._categories.items()
            },
        }


# 创建全局动作注册表实例
action_registry = ActionRegistry()


def action_decorator(
    name: str,
    display_name: str,
    description: str,
    category: ActionCategory,
    parameters: Optional[List[ActionParameter]] = None,
    returns: str = "",
    examples: Optional[List[Dict[str, Any]]] = None,
    tags: Optional[List[str]] = None,
    requires_confirmation: bool = False,
    is_dangerous: bool = False,
):
    """
    动作注册装饰器
    
    用于将函数注册为动作
    
    Args:
        name: 动作名称
        display_name: 显示名称
        description: 描述
        category: 类别
        parameters: 参数列表
        returns: 返回值描述
        examples: 示例
        tags: 标签
        requires_confirmation: 是否需要确认
        is_dangerous: 是否危险
    
    Returns:
        装饰器函数
    """
    def decorator(func: ActionExecutor) -> ActionExecutor:
        action_registry.register(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            executor=func,
            parameters=parameters,
            returns=returns,
            examples=examples,
            tags=tags,
            requires_confirmation=requires_confirmation,
            is_dangerous=is_dangerous,
        )
        return func
    
    return decorator
