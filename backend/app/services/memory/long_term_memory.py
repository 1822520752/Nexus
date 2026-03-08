"""
长期记忆服务模块
实现跨会话记忆索引、记忆重要性评分算法、长期记忆检索接口和记忆遗忘机制
支持持久化存储和智能检索
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger


class MemoryCategory(str, Enum):
    """
    记忆分类枚举
    
    定义长期记忆的分类类型
    """
    FACT = "fact"  # 事实性知识
    PREFERENCE = "preference"  # 用户偏好
    EXPERIENCE = "experience"  # 经验性知识
    SKILL = "skill"  # 技能知识
    CONTEXT = "context"  # 上下文背景
    RELATIONSHIP = "relationship"  # 关系信息
    SCHEDULE = "schedule"  # 日程安排
    PROJECT = "project"  # 项目信息


class MemoryStatus(str, Enum):
    """
    记忆状态枚举
    
    定义记忆的生命周期状态
    """
    ACTIVE = "active"  # 活跃状态
    ARCHIVED = "archived"  # 已归档
    FORGOTTEN = "forgotten"  # 已遗忘
    CONSOLIDATED = "consolidated"  # 已巩固


@dataclass
class MemoryIndex:
    """
    记忆索引数据类
    
    存储记忆的索引信息，支持快速检索
    """
    memory_id: int
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    categories: List[MemoryCategory] = field(default_factory=list)
    session_ids: List[str] = field(default_factory=list)  # 关联的会话ID
    embedding_id: Optional[str] = None  # 向量嵌入ID
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含索引信息的字典
        """
        return {
            "memory_id": self.memory_id,
            "keywords": self.keywords,
            "entities": self.entities,
            "categories": [c.value for c in self.categories],
            "session_ids": self.session_ids,
            "embedding_id": self.embedding_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryIndex":
        """
        从字典创建索引
        
        Args:
            data: 包含索引数据的字典
            
        Returns:
            索引实例
        """
        categories = []
        for cat_str in data.get("categories", []):
            try:
                categories.append(MemoryCategory(cat_str))
            except ValueError:
                pass
        
        return cls(
            memory_id=data.get("memory_id", 0),
            keywords=data.get("keywords", []),
            entities=data.get("entities", []),
            categories=categories,
            session_ids=data.get("session_ids", []),
            embedding_id=data.get("embedding_id"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )


@dataclass
class LongTermMemoryItem:
    """
    长期记忆项数据类
    
    存储单个长期记忆条目
    """
    id: int
    content: str
    importance: float
    category: MemoryCategory = MemoryCategory.FACT
    status: MemoryStatus = MemoryStatus.ACTIVE
    
    # 索引信息
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    
    # 会话关联
    session_ids: List[str] = field(default_factory=list)
    conversation_count: int = 0
    
    # 时间信息
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_reinforced: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # 访问统计
    access_count: int = 0
    reinforcement_count: int = 0
    
    # 衰减参数
    decay_rate: float = 0.01  # 每日衰减率
    reinforcement_bonus: float = 0.1  # 每次巩固加成
    
    # 元数据
    source_type: str = "conversation"
    source_id: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含长期记忆项的字典
        """
        return {
            "id": self.id,
            "content": self.content,
            "importance": self.importance,
            "category": self.category.value,
            "status": self.status.value,
            "keywords": self.keywords,
            "entities": self.entities,
            "session_ids": self.session_ids,
            "conversation_count": self.conversation_count,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "last_reinforced": self.last_reinforced,
            "access_count": self.access_count,
            "reinforcement_count": self.reinforcement_count,
            "decay_rate": self.decay_rate,
            "reinforcement_bonus": self.reinforcement_bonus,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LongTermMemoryItem":
        """
        从字典创建长期记忆项
        
        Args:
            data: 包含记忆数据的字典
            
        Returns:
            长期记忆项实例
        """
        return cls(
            id=data.get("id", 0),
            content=data.get("content", ""),
            importance=data.get("importance", 0.5),
            category=MemoryCategory(data.get("category", "fact")),
            status=MemoryStatus(data.get("status", "active")),
            keywords=data.get("keywords", []),
            entities=data.get("entities", []),
            session_ids=data.get("session_ids", []),
            conversation_count=data.get("conversation_count", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            last_accessed=data.get("last_accessed", datetime.utcnow().isoformat()),
            last_reinforced=data.get("last_reinforced", datetime.utcnow().isoformat()),
            access_count=data.get("access_count", 0),
            reinforcement_count=data.get("reinforcement_count", 0),
            decay_rate=data.get("decay_rate", 0.01),
            reinforcement_bonus=data.get("reinforcement_bonus", 0.1),
            source_type=data.get("source_type", "conversation"),
            source_id=data.get("source_id"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


class ImportanceScorer:
    """
    重要性评分器类
    
    计算记忆的重要性评分，考虑多种因素
    """
    
    # 基础权重配置
    WEIGHTS = {
        "recency": 0.2,  # 新近度
        "frequency": 0.2,  # 访问频率
        "reinforcement": 0.25,  # 巩固次数
        "content_quality": 0.15,  # 内容质量
        "entity_richness": 0.1,  # 实体丰富度
        "category_priority": 0.1,  # 分类优先级
    }
    
    # 分类优先级
    CATEGORY_PRIORITY = {
        MemoryCategory.PREFERENCE: 0.9,  # 用户偏好最重要
        MemoryCategory.FACT: 0.8,  # 事实性知识
        MemoryCategory.RELATIONSHIP: 0.75,  # 关系信息
        MemoryCategory.PROJECT: 0.7,  # 项目信息
        MemoryCategory.SKILL: 0.65,  # 技能知识
        MemoryCategory.SCHEDULE: 0.6,  # 日程安排
        MemoryCategory.EXPERIENCE: 0.5,  # 经验性知识
        MemoryCategory.CONTEXT: 0.4,  # 上下文背景
    }
    
    @classmethod
    def calculate_importance(
        cls,
        item: LongTermMemoryItem,
        current_time: Optional[datetime] = None,
    ) -> float:
        """
        计算记忆的综合重要性评分
        
        Args:
            item: 长期记忆项
            current_time: 当前时间（用于测试）
            
        Returns:
            重要性评分（0-1）
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        scores = {}
        
        # 1. 新近度评分
        scores["recency"] = cls._calculate_recency_score(item, current_time)
        
        # 2. 访问频率评分
        scores["frequency"] = cls._calculate_frequency_score(item)
        
        # 3. 巩固次数评分
        scores["reinforcement"] = cls._calculate_reinforcement_score(item)
        
        # 4. 内容质量评分
        scores["content_quality"] = cls._calculate_content_quality_score(item)
        
        # 5. 实体丰富度评分
        scores["entity_richness"] = cls._calculate_entity_richness_score(item)
        
        # 6. 分类优先级评分
        scores["category_priority"] = cls.CATEGORY_PRIORITY.get(item.category, 0.5)
        
        # 加权求和
        total_score = sum(
            scores[key] * cls.WEIGHTS[key]
            for key in cls.WEIGHTS
        )
        
        return min(1.0, max(0.0, total_score))
    
    @classmethod
    def _calculate_recency_score(
        cls,
        item: LongTermMemoryItem,
        current_time: datetime,
    ) -> float:
        """
        计算新近度评分
        
        Args:
            item: 记忆项
            current_time: 当前时间
            
        Returns:
            新近度评分（0-1）
        """
        try:
            last_accessed = datetime.fromisoformat(item.last_accessed)
            days_since_access = (current_time - last_accessed).days
        except (ValueError, TypeError):
            days_since_access = 0
        
        # 指数衰减，半衰期为 30 天
        return max(0.1, 1.0 * (0.5 ** (days_since_access / 30)))
    
    @classmethod
    def _calculate_frequency_score(cls, item: LongTermMemoryItem) -> float:
        """
        计算访问频率评分
        
        Args:
            item: 记忆项
            
        Returns:
            频率评分（0-1）
        """
        # 使用对数函数平滑
        import math
        return min(1.0, math.log10(item.access_count + 1) / 2)
    
    @classmethod
    def _calculate_reinforcement_score(cls, item: LongTermMemoryItem) -> float:
        """
        计算巩固次数评分
        
        Args:
            item: 记忆项
            
        Returns:
            巩固评分（0-1）
        """
        import math
        return min(1.0, math.log10(item.reinforcement_count + 1) / 1.5)
    
    @classmethod
    def _calculate_content_quality_score(cls, item: LongTermMemoryItem) -> float:
        """
        计算内容质量评分
        
        Args:
            item: 记忆项
            
        Returns:
            内容质量评分（0-1）
        """
        score = 0.3  # 基础分
        
        # 内容长度
        content_len = len(item.content)
        if content_len > 50:
            score += 0.2
        if content_len > 200:
            score += 0.1
        
        # 关键词数量
        if len(item.keywords) >= 3:
            score += 0.2
        
        # 标签数量
        if len(item.tags) >= 2:
            score += 0.1
        
        # 元数据丰富度
        if item.metadata:
            score += 0.1
        
        return min(1.0, score)
    
    @classmethod
    def _calculate_entity_richness_score(cls, item: LongTermMemoryItem) -> float:
        """
        计算实体丰富度评分
        
        Args:
            item: 记忆项
            
        Returns:
            实体丰富度评分（0-1）
        """
        entity_count = len(item.entities)
        return min(1.0, entity_count / 5)


class MemoryForgetting:
    """
    记忆遗忘机制类
    
    实现基于艾宾浩斯遗忘曲线的记忆衰减
    """
    
    # 艾宾浩斯遗忘曲线参数
    EBBINGHAUS_A = 1.0  # 初始记忆强度
    EBBINGHAUS_B = 0.3  # 衰减速率
    EBBINGHAUS_C = 0.1  # 最小保留值
    
    # 遗忘阈值
    FORGET_THRESHOLD = 0.1  # 低于此值视为遗忘
    ARCHIVE_THRESHOLD = 0.3  # 低于此值归档
    
    @classmethod
    def calculate_retention(
        cls,
        item: LongTermMemoryItem,
        current_time: Optional[datetime] = None,
    ) -> float:
        """
        计算记忆保留率
        
        基于艾宾浩斯遗忘曲线：R = A * e^(-t/S) + C
        其中 t 为时间，S 为记忆强度（与巩固次数相关）
        
        Args:
            item: 长期记忆项
            current_time: 当前时间
            
        Returns:
            记忆保留率（0-1）
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        try:
            last_reinforced = datetime.fromisoformat(item.last_reinforced)
            days_elapsed = (current_time - last_reinforced).days
        except (ValueError, TypeError):
            days_elapsed = 0
        
        # 记忆强度与巩固次数相关
        strength = 10 + item.reinforcement_count * 5
        
        # 艾宾浩斯公式
        retention = cls.EBBINGHAUS_A * (2.718 ** (-days_elapsed / strength))
        retention = retention * (1 - cls.EBBINGHAUS_B) + cls.EBBINGHAUS_C
        
        # 巩固加成
        retention += item.reinforcement_count * item.reinforcement_bonus
        
        return min(1.0, max(0.0, retention))
    
    @classmethod
    def should_forget(
        cls,
        item: LongTermMemoryItem,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """
        判断记忆是否应该被遗忘
        
        Args:
            item: 长期记忆项
            current_time: 当前时间
            
        Returns:
            是否应该遗忘
        """
        retention = cls.calculate_retention(item, current_time)
        return retention < cls.FORGET_THRESHOLD
    
    @classmethod
    def should_archive(
        cls,
        item: LongTermMemoryItem,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """
        判断记忆是否应该被归档
        
        Args:
            item: 长期记忆项
            current_time: 当前时间
            
        Returns:
            是否应该归档
        """
        retention = cls.calculate_retention(item, current_time)
        return retention < cls.ARCHIVE_THRESHOLD and retention >= cls.FORGET_THRESHOLD
    
    @classmethod
    def apply_decay(
        cls,
        item: LongTermMemoryItem,
        current_time: Optional[datetime] = None,
    ) -> LongTermMemoryItem:
        """
        应用记忆衰减
        
        Args:
            item: 长期记忆项
            current_time: 当前时间
            
        Returns:
            更新后的记忆项
        """
        retention = cls.calculate_retention(item, current_time)
        item.importance = retention * item.importance
        
        # 更新状态
        if cls.should_forget(item, current_time):
            item.status = MemoryStatus.FORGOTTEN
        elif cls.should_archive(item, current_time):
            item.status = MemoryStatus.ARCHIVED
        
        return item


class CrossSessionIndex:
    """
    跨会话记忆索引类
    
    管理记忆与会话的关联关系
    """
    
    def __init__(self):
        """
        初始化跨会话索引
        """
        # 会话到记忆的映射
        self._session_to_memories: Dict[str, Set[int]] = {}
        
        # 记忆到会话的映射
        self._memory_to_sessions: Dict[int, Set[str]] = {}
        
        # 关键词索引
        self._keyword_index: Dict[str, Set[int]] = {}
        
        # 实体索引
        self._entity_index: Dict[str, Set[int]] = {}
        
        # 分类索引
        self._category_index: Dict[MemoryCategory, Set[int]] = {}
        
        logger.info("初始化跨会话记忆索引")
    
    def index_memory(
        self,
        memory_id: int,
        session_id: str,
        keywords: List[str],
        entities: List[str],
        categories: List[MemoryCategory],
    ) -> None:
        """
        索引记忆
        
        Args:
            memory_id: 记忆 ID
            session_id: 会话 ID
            keywords: 关键词列表
            entities: 实体列表
            categories: 分类列表
        """
        # 会话关联
        if session_id not in self._session_to_memories:
            self._session_to_memories[session_id] = set()
        self._session_to_memories[session_id].add(memory_id)
        
        if memory_id not in self._memory_to_sessions:
            self._memory_to_sessions[memory_id] = set()
        self._memory_to_sessions[memory_id].add(session_id)
        
        # 关键词索引
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self._keyword_index:
                self._keyword_index[keyword_lower] = set()
            self._keyword_index[keyword_lower].add(memory_id)
        
        # 实体索引
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower not in self._entity_index:
                self._entity_index[entity_lower] = set()
            self._entity_index[entity_lower].add(memory_id)
        
        # 分类索引
        for category in categories:
            if category not in self._category_index:
                self._category_index[category] = set()
            self._category_index[category].add(memory_id)
    
    def remove_memory(self, memory_id: int) -> None:
        """
        移除记忆索引
        
        Args:
            memory_id: 记忆 ID
        """
        # 移除会话关联
        if memory_id in self._memory_to_sessions:
            for session_id in self._memory_to_sessions[memory_id]:
                if session_id in self._session_to_memories:
                    self._session_to_memories[session_id].discard(memory_id)
            del self._memory_to_sessions[memory_id]
        
        # 移除关键词索引
        for keyword in list(self._keyword_index.keys()):
            self._keyword_index[keyword].discard(memory_id)
            if not self._keyword_index[keyword]:
                del self._keyword_index[keyword]
        
        # 移除实体索引
        for entity in list(self._entity_index.keys()):
            self._entity_index[entity].discard(memory_id)
            if not self._entity_index[entity]:
                del self._entity_index[entity]
        
        # 移除分类索引
        for category in self._category_index:
            self._category_index[category].discard(memory_id)
    
    def get_memories_by_session(self, session_id: str) -> Set[int]:
        """
        获取会话关联的记忆
        
        Args:
            session_id: 会话 ID
            
        Returns:
            记忆 ID 集合
        """
        return self._session_to_memories.get(session_id, set()).copy()
    
    def get_sessions_by_memory(self, memory_id: int) -> Set[str]:
        """
        获取记忆关联的会话
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            会话 ID 集合
        """
        return self._memory_to_sessions.get(memory_id, set()).copy()
    
    def search_by_keywords(
        self,
        keywords: List[str],
        match_all: bool = False,
    ) -> Set[int]:
        """
        通过关键词搜索记忆
        
        Args:
            keywords: 关键词列表
            match_all: 是否需要全部匹配
            
        Returns:
            记忆 ID 集合
        """
        if not keywords:
            return set()
        
        keyword_sets = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self._keyword_index:
                keyword_sets.append(self._keyword_index[keyword_lower])
        
        if not keyword_sets:
            return set()
        
        if match_all:
            result = keyword_sets[0]
            for s in keyword_sets[1:]:
                result = result.intersection(s)
            return result
        else:
            result = set()
            for s in keyword_sets:
                result = result.union(s)
            return result
    
    def search_by_entities(
        self,
        entities: List[str],
        match_all: bool = False,
    ) -> Set[int]:
        """
        通过实体搜索记忆
        
        Args:
            entities: 实体列表
            match_all: 是否需要全部匹配
            
        Returns:
            记忆 ID 集合
        """
        if not entities:
            return set()
        
        entity_sets = []
        for entity in entities:
            entity_lower = entity.lower()
            if entity_lower in self._entity_index:
                entity_sets.append(self._entity_index[entity_lower])
        
        if not entity_sets:
            return set()
        
        if match_all:
            result = entity_sets[0]
            for s in entity_sets[1:]:
                result = result.intersection(s)
            return result
        else:
            result = set()
            for s in entity_sets:
                result = result.union(s)
            return result
    
    def search_by_category(self, category: MemoryCategory) -> Set[int]:
        """
        通过分类搜索记忆
        
        Args:
            category: 记忆分类
            
        Returns:
            记忆 ID 集合
        """
        return self._category_index.get(category, set()).copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_sessions": len(self._session_to_memories),
            "total_memories_indexed": len(self._memory_to_sessions),
            "total_keywords": len(self._keyword_index),
            "total_entities": len(self._entity_index),
            "category_distribution": {
                cat.value: len(ids)
                for cat, ids in self._category_index.items()
            },
        }
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出索引状态
        
        Returns:
            状态字典
        """
        return {
            "session_to_memories": {
                k: list(v) for k, v in self._session_to_memories.items()
            },
            "memory_to_sessions": {
                k: list(v) for k, v in self._memory_to_sessions.items()
            },
            "keyword_index": {
                k: list(v) for k, v in self._keyword_index.items()
            },
            "entity_index": {
                k: list(v) for k, v in self._entity_index.items()
            },
            "category_index": {
                cat.value: list(ids)
                for cat, ids in self._category_index.items()
            },
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        导入索引状态
        
        Args:
            state: 状态字典
        """
        self._session_to_memories = {
            k: set(v) for k, v in state.get("session_to_memories", {}).items()
        }
        self._memory_to_sessions = {
            k: set(v) for k, v in state.get("memory_to_sessions", {}).items()
        }
        self._keyword_index = {
            k: set(v) for k, v in state.get("keyword_index", {}).items()
        }
        self._entity_index = {
            k: set(v) for k, v in state.get("entity_index", {}).items()
        }
        
        self._category_index = {}
        for cat_str, ids in state.get("category_index", {}).items():
            try:
                category = MemoryCategory(cat_str)
                self._category_index[category] = set(ids)
            except ValueError:
                pass


class LongTermMemory:
    """
    长期记忆类
    
    管理持久化的重要信息存储和检索
    支持跨会话索引、重要性评分和遗忘机制
    """
    
    # 默认最大记忆数量
    DEFAULT_MAX_MEMORIES = 10000
    
    # 巩固阈值（重要性超过此值时进行巩固）
    CONSOLIDATION_THRESHOLD = 0.7
    
    # 自动清理间隔（天）
    AUTO_CLEANUP_INTERVAL = 7
    
    def __init__(
        self,
        max_memories: int = DEFAULT_MAX_MEMORIES,
        enable_auto_consolidation: bool = True,
    ):
        """
        初始化长期记忆
        
        Args:
            max_memories: 最大记忆数量
            enable_auto_consolidation: 是否启用自动巩固
        """
        self.max_memories = max_memories
        self.enable_auto_consolidation = enable_auto_consolidation
        
        # 记忆存储
        self._memories: Dict[int, LongTermMemoryItem] = {}
        self._next_id = 1
        
        # 跨会话索引
        self._index = CrossSessionIndex()
        
        # 最后清理时间
        self._last_cleanup = datetime.utcnow()
        
        logger.info(
            f"初始化长期记忆: max_memories={max_memories}, "
            f"enable_auto_consolidation={enable_auto_consolidation}"
        )
    
    @property
    def memory_count(self) -> int:
        """
        获取记忆数量
        
        Returns:
            记忆数量
        """
        return len(self._memories)
    
    @property
    def index(self) -> CrossSessionIndex:
        """
        获取跨会话索引
        
        Returns:
            跨会话索引实例
        """
        return self._index
    
    async def add_memory(
        self,
        content: str,
        session_id: str,
        category: MemoryCategory = MemoryCategory.FACT,
        keywords: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        source_type: str = "conversation",
        source_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LongTermMemoryItem:
        """
        添加长期记忆
        
        Args:
            content: 记忆内容
            session_id: 会话 ID
            category: 记忆分类
            keywords: 关键词列表
            entities: 实体列表
            tags: 标签列表
            source_type: 来源类型
            source_id: 来源 ID
            metadata: 元数据
            
        Returns:
            创建的长期记忆项
        """
        # 提取关键词和实体（如果未提供）
        if keywords is None:
            keywords = self._extract_keywords(content)
        if entities is None:
            entities = self._extract_entities(content)
        
        # 创建记忆项
        item = LongTermMemoryItem(
            id=self._next_id,
            content=content,
            importance=0.5,  # 初始重要性
            category=category,
            keywords=keywords,
            entities=entities,
            session_ids=[session_id],
            tags=tags or [],
            source_type=source_type,
            source_id=source_id,
            metadata=metadata or {},
        )
        
        # 计算初始重要性
        item.importance = ImportanceScorer.calculate_importance(item)
        
        # 存储记忆
        self._memories[item.id] = item
        self._next_id += 1
        
        # 更新索引
        self._index.index_memory(
            memory_id=item.id,
            session_id=session_id,
            keywords=keywords,
            entities=entities,
            categories=[category],
        )
        
        logger.debug(
            f"添加长期记忆: id={item.id}, category={category.value}, "
            f"importance={item.importance:.2f}"
        )
        
        return item
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        Args:
            text: 源文本
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 提取中文关键词（2-4字的词组）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        keywords.extend(chinese_words)
        
        # 提取英文单词
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        keywords.extend(english_words)
        
        # 去重并限制数量
        return list(dict.fromkeys(keywords))[:20]
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        从文本中提取实体
        
        Args:
            text: 源文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 提取引号中的内容
        quoted = re.findall(r'[""「」『』【】]([^""「」『』【】]+)[""「」『』【】]', text)
        entities.extend(quoted)
        
        # 提取专有名词（大写开头的英文）
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized)
        
        # 提取人名模式
        names = re.findall(r'([一-龥]{2,4})(?:说|表示|认为|指出)', text)
        entities.extend(names)
        
        # 去重并限制数量
        return list(dict.fromkeys(entities))[:15]
    
    async def get_memory(self, memory_id: int) -> Optional[LongTermMemoryItem]:
        """
        获取长期记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            记忆项，不存在则返回 None
        """
        item = self._memories.get(memory_id)
        if item:
            # 更新访问统计
            item.access_count += 1
            item.last_accessed = datetime.utcnow().isoformat()
            
            # 重新计算重要性
            item.importance = ImportanceScorer.calculate_importance(item)
        
        return item
    
    async def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        category: Optional[MemoryCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[LongTermMemoryItem]:
        """
        更新长期记忆
        
        Args:
            memory_id: 记忆 ID
            content: 新内容
            importance: 新重要性
            category: 新分类
            tags: 新标签
            
        Returns:
            更新后的记忆项，不存在则返回 None
        """
        item = self._memories.get(memory_id)
        if not item:
            return None
        
        if content is not None:
            item.content = content
            # 重新提取关键词和实体
            item.keywords = self._extract_keywords(content)
            item.entities = self._extract_entities(content)
        
        if importance is not None:
            item.importance = importance
        
        if category is not None:
            item.category = category
        
        if tags is not None:
            item.tags = tags
        
        item.last_accessed = datetime.utcnow().isoformat()
        
        return item
    
    async def reinforce_memory(self, memory_id: int) -> Optional[LongTermMemoryItem]:
        """
        巩固记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            巩固后的记忆项，不存在则返回 None
        """
        item = self._memories.get(memory_id)
        if not item:
            return None
        
        # 增加巩固次数
        item.reinforcement_count += 1
        item.last_reinforced = datetime.utcnow().isoformat()
        
        # 更新状态
        if item.status == MemoryStatus.ARCHIVED:
            item.status = MemoryStatus.ACTIVE
        elif item.reinforcement_count >= 3:
            item.status = MemoryStatus.CONSOLIDATED
        
        # 重新计算重要性
        item.importance = ImportanceScorer.calculate_importance(item)
        
        logger.debug(
            f"巩固记忆: id={memory_id}, reinforcement_count={item.reinforcement_count}, "
            f"status={item.status.value}"
        )
        
        return item
    
    async def search_memories(
        self,
        query: str,
        top_k: int = 10,
        categories: Optional[List[MemoryCategory]] = None,
        min_importance: float = 0.0,
        status: Optional[MemoryStatus] = None,
    ) -> List[LongTermMemoryItem]:
        """
        搜索长期记忆
        
        Args:
            query: 搜索关键词
            top_k: 返回数量
            categories: 分类过滤
            min_importance: 最小重要性
            status: 状态过滤
            
        Returns:
            匹配的记忆列表
        """
        # 提取查询关键词
        query_keywords = self._extract_keywords(query)
        query_entities = self._extract_entities(query)
        
        # 通过索引搜索
        keyword_results = self._index.search_by_keywords(query_keywords)
        entity_results = self._index.search_by_entities(query_entities)
        
        # 合并结果
        candidate_ids = keyword_results.union(entity_results)
        
        # 如果没有索引结果，进行全文搜索
        if not candidate_ids:
            query_lower = query.lower()
            for memory_id, item in self._memories.items():
                if query_lower in item.content.lower():
                    candidate_ids.add(memory_id)
        
        # 过滤和评分
        results = []
        for memory_id in candidate_ids:
            item = self._memories.get(memory_id)
            if not item:
                continue
            
            # 分类过滤
            if categories and item.category not in categories:
                continue
            
            # 重要性过滤
            if item.importance < min_importance:
                continue
            
            # 状态过滤
            if status and item.status != status:
                continue
            
            # 计算匹配分数
            score = self._calculate_match_score(item, query_keywords, query_entities)
            results.append((item, score))
        
        # 按分数排序
        results.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
        
        return [item for item, _ in results[:top_k]]
    
    def _calculate_match_score(
        self,
        item: LongTermMemoryItem,
        query_keywords: List[str],
        query_entities: List[str],
    ) -> float:
        """
        计算匹配分数
        
        Args:
            item: 记忆项
            query_keywords: 查询关键词
            query_entities: 查询实体
            
        Returns:
            匹配分数（0-1）
        """
        score = 0.0
        
        # 关键词匹配
        if query_keywords:
            keyword_matches = sum(
                1 for kw in query_keywords
                if kw.lower() in [k.lower() for k in item.keywords]
            )
            score += keyword_matches / len(query_keywords) * 0.5
        
        # 实体匹配
        if query_entities:
            entity_matches = sum(
                1 for e in query_entities
                if e.lower() in [ent.lower() for ent in item.entities]
            )
            score += entity_matches / len(query_entities) * 0.3
        
        # 内容包含
        content_lower = item.content.lower()
        for kw in query_keywords:
            if kw.lower() in content_lower:
                score += 0.1
        
        return min(1.0, score)
    
    async def get_memories_by_session(
        self,
        session_id: str,
        top_k: int = 20,
    ) -> List[LongTermMemoryItem]:
        """
        获取会话关联的记忆
        
        Args:
            session_id: 会话 ID
            top_k: 返回数量
            
        Returns:
            记忆列表
        """
        memory_ids = self._index.get_memories_by_session(session_id)
        
        results = []
        for memory_id in memory_ids:
            item = self._memories.get(memory_id)
            if item:
                results.append(item)
        
        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results[:top_k]
    
    async def get_memories_by_category(
        self,
        category: MemoryCategory,
        top_k: int = 20,
    ) -> List[LongTermMemoryItem]:
        """
        获取指定分类的记忆
        
        Args:
            category: 记忆分类
            top_k: 返回数量
            
        Returns:
            记忆列表
        """
        memory_ids = self._index.search_by_category(category)
        
        results = []
        for memory_id in memory_ids:
            item = self._memories.get(memory_id)
            if item:
                results.append(item)
        
        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        
        return results[:top_k]
    
    async def apply_forgetting(
        self,
        force: bool = False,
    ) -> Dict[str, int]:
        """
        应用遗忘机制
        
        Args:
            force: 是否强制执行（忽略时间间隔）
            
        Returns:
            处理结果统计
        """
        now = datetime.utcnow()
        
        # 检查是否需要执行
        if not force:
            days_since_cleanup = (now - self._last_cleanup).days
            if days_since_cleanup < self.AUTO_CLEANUP_INTERVAL:
                return {"skipped": 1}
        
        self._last_cleanup = now
        
        stats = {
            "forgotten": 0,
            "archived": 0,
            "removed": 0,
        }
        
        # 遍历所有记忆
        for memory_id, item in list(self._memories.items()):
            # 应用衰减
            MemoryForgetting.apply_decay(item, now)
            
            # 统计状态变化
            if item.status == MemoryStatus.FORGOTTEN:
                stats["forgotten"] += 1
                # 移除遗忘的记忆
                del self._memories[memory_id]
                self._index.remove_memory(memory_id)
                stats["removed"] += 1
            
            elif item.status == MemoryStatus.ARCHIVED:
                stats["archived"] += 1
        
        logger.info(
            f"遗忘机制执行完成: forgotten={stats['forgotten']}, "
            f"archived={stats['archived']}, removed={stats['removed']}"
        )
        
        return stats
    
    async def auto_consolidate(self) -> int:
        """
        自动巩固高重要性记忆
        
        Returns:
            巩固的记忆数量
        """
        if not self.enable_auto_consolidation:
            return 0
        
        consolidated_count = 0
        
        for item in self._memories.values():
            if (item.importance >= self.CONSOLIDATION_THRESHOLD and
                item.status == MemoryStatus.ACTIVE and
                item.reinforcement_count < 3):
                
                item.reinforcement_count += 1
                item.last_reinforced = datetime.utcnow().isoformat()
                
                if item.reinforcement_count >= 3:
                    item.status = MemoryStatus.CONSOLIDATED
                
                consolidated_count += 1
        
        if consolidated_count > 0:
            logger.info(f"自动巩固完成: 巩固了 {consolidated_count} 条记忆")
        
        return consolidated_count
    
    async def cleanup_overflow(self) -> int:
        """
        清理超出容量的记忆
        
        Returns:
            清理的记忆数量
        """
        if len(self._memories) <= self.max_memories:
            return 0
        
        # 计算需要移除的数量
        remove_count = len(self._memories) - self.max_memories
        
        # 按重要性排序
        sorted_memories = sorted(
            self._memories.items(),
            key=lambda x: (x[1].status == MemoryStatus.CONSOLIDATED, x[1].importance),
        )
        
        # 移除最低重要性的记忆
        for i in range(remove_count):
            memory_id = sorted_memories[i][0]
            del self._memories[memory_id]
            self._index.remove_memory(memory_id)
        
        logger.info(f"清理超出容量的记忆: 移除了 {remove_count} 条记忆")
        
        return remove_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        # 状态分布
        status_dist: Dict[str, int] = {}
        for status in MemoryStatus:
            status_dist[status.value] = 0
        
        # 分类分布
        category_dist: Dict[str, int] = {}
        for category in MemoryCategory:
            category_dist[category.value] = 0
        
        # 重要性分布
        importance_dist = {"high": 0, "medium": 0, "low": 0}
        
        for item in self._memories.values():
            status_dist[item.status.value] += 1
            category_dist[item.category.value] += 1
            
            if item.importance >= 0.7:
                importance_dist["high"] += 1
            elif item.importance >= 0.4:
                importance_dist["medium"] += 1
            else:
                importance_dist["low"] += 1
        
        return {
            "total_memories": len(self._memories),
            "max_memories": self.max_memories,
            "status_distribution": status_dist,
            "category_distribution": category_dist,
            "importance_distribution": importance_dist,
            "index_stats": self._index.get_stats(),
            "last_cleanup": self._last_cleanup.isoformat(),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出状态
        
        Returns:
            状态字典
        """
        return {
            "memories": [item.to_dict() for item in self._memories.values()],
            "index": self._index.export_state(),
            "next_id": self._next_id,
            "last_cleanup": self._last_cleanup.isoformat(),
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        导入状态
        
        Args:
            state: 状态字典
        """
        self._memories.clear()
        
        for item_data in state.get("memories", []):
            item = LongTermMemoryItem.from_dict(item_data)
            self._memories[item.id] = item
        
        self._index.import_state(state.get("index", {}))
        self._next_id = state.get("next_id", 1)
        
        if "last_cleanup" in state:
            self._last_cleanup = datetime.fromisoformat(state["last_cleanup"])
