"""
工作记忆服务模块
实现知识图谱数据结构、重要信息自动提取和向量数据库存储
支持分钟级记忆更新机制
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger


class EntityType(str, Enum):
    """
    实体类型枚举
    
    定义知识图谱中支持的实体类型
    """
    PERSON = "person"  # 人物
    ORGANIZATION = "organization"  # 组织
    LOCATION = "location"  # 地点
    CONCEPT = "concept"  # 概念
    EVENT = "event"  # 事件
    TOPIC = "topic"  # 主题
    PRODUCT = "product"  # 产品
    DATE = "date"  # 日期
    OTHER = "other"  # 其他


class RelationType(str, Enum):
    """
    关系类型枚举
    
    定义知识图谱中支持的关系类型
    """
    RELATED_TO = "related_to"  # 相关
    PART_OF = "part_of"  # 部分
    HAS_ATTRIBUTE = "has_attribute"  # 具有属性
    CAUSED_BY = "caused_by"  # 由...引起
    FOLLOWS = "follows"  # 跟随
    PRECEDES = "precedes"  # 先于
    LOCATED_AT = "located_at"  # 位于
    BELONGS_TO = "belongs_to"  # 属于
    MENTIONED_WITH = "mentioned_with"  # 一起提及
    SIMILAR_TO = "similar_to"  # 相似


@dataclass
class KnowledgeEntity:
    """
    知识实体数据类
    
    存储知识图谱中的实体信息
    """
    id: str
    name: str
    entity_type: EntityType
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    mention_count: int = 0
    first_mentioned: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_mentioned: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source_ids: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含实体信息的字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "aliases": self.aliases,
            "description": self.description,
            "properties": self.properties,
            "importance": self.importance,
            "mention_count": self.mention_count,
            "first_mentioned": self.first_mentioned,
            "last_mentioned": self.last_mentioned,
            "source_ids": self.source_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEntity":
        """
        从字典创建实体
        
        Args:
            data: 包含实体数据的字典
            
        Returns:
            实体实例
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            entity_type=EntityType(data.get("entity_type", "other")),
            aliases=data.get("aliases", []),
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            importance=data.get("importance", 0.5),
            mention_count=data.get("mention_count", 0),
            first_mentioned=data.get("first_mentioned", datetime.utcnow().isoformat()),
            last_mentioned=data.get("last_mentioned", datetime.utcnow().isoformat()),
            source_ids=data.get("source_ids", []),
        )
    
    def update_mention(self, source_id: Optional[int] = None) -> None:
        """
        更新提及信息
        
        Args:
            source_id: 来源 ID
        """
        self.mention_count += 1
        self.last_mentioned = datetime.utcnow().isoformat()
        if source_id and source_id not in self.source_ids:
            self.source_ids.append(source_id)
        # 更新重要性
        self.importance = min(1.0, 0.3 + self.mention_count * 0.1)


@dataclass
class KnowledgeRelation:
    """
    知识关系数据类
    
    存储知识图谱中的关系信息
    """
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)  # 支持该关系的证据
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含关系信息的字典
        """
        return {
            "id": self.id,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "properties": self.properties,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeRelation":
        """
        从字典创建关系
        
        Args:
            data: 包含关系数据的字典
            
        Returns:
            关系实例
        """
        return cls(
            id=data.get("id", ""),
            source_entity_id=data.get("source_entity_id", ""),
            target_entity_id=data.get("target_entity_id", ""),
            relation_type=RelationType(data.get("relation_type", "related_to")),
            weight=data.get("weight", 1.0),
            properties=data.get("properties", {}),
            evidence=data.get("evidence", []),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class WorkingMemoryItem:
    """
    工作记忆项数据类
    
    存储单个工作记忆条目
    """
    id: int
    content: str
    importance: float
    entity_ids: List[str] = field(default_factory=list)
    relation_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source_type: str = "conversation"
    source_id: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            包含工作记忆项的字典
        """
        return {
            "id": self.id,
            "content": self.content,
            "importance": self.importance,
            "entity_ids": self.entity_ids,
            "relation_ids": self.relation_ids,
            "tags": self.tags,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }


class InformationExtractor:
    """
    信息提取器类
    
    从文本中提取实体、关系和关键信息
    """
    
    # 实体识别模式
    ENTITY_PATTERNS = {
        EntityType.PERSON: [
            r'([一-龥]{2,4})(?:说|表示|认为|指出|提到)',
            r'([一-龥]{2,4})先生',
            r'([一-龥]{2,4})女士',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ],
        EntityType.ORGANIZATION: [
            r'([一-龥]{2,8})(?:公司|集团|机构|组织|部门|团队)',
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:Inc|Corp|Company|Ltd)',
        ],
        EntityType.LOCATION: [
            r'([一-龥]{2,6})(?:市|省|县|区|镇|村)',
            r'在([一-龥]{2,6})',
            r'位于([一-龥]{2,6})',
        ],
        EntityType.DATE: [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{1,2}月\d{1,2}日)',
            r'(昨天|今天|明天|上周|下周|本月)',
        ],
        EntityType.TOPIC: [
            r'关于([一-龥]{2,8})',
            r'讨论([一-龥]{2,8})',
            r'([一-龥]{2,8})话题',
        ],
    }
    
    # 关键信息模式
    KEY_INFO_PATTERNS = [
        r'重要[：:]\s*(.+)',
        r'关键[：:]\s*(.+)',
        r'注意[：:]\s*(.+)',
        r'结论[：:]\s*(.+)',
        r'总结[：:]\s*(.+)',
        r'目标[：:]\s*(.+)',
        r'计划[：:]\s*(.+)',
        r'问题[：:]\s*(.+)',
        r'解决[：:]\s*(.+)',
    ]
    
    @classmethod
    def extract_entities(cls, text: str) -> List[Tuple[str, EntityType]]:
        """
        从文本中提取实体
        
        Args:
            text: 源文本
            
        Returns:
            实体列表，每项为 (实体名, 实体类型)
        """
        entities = []
        seen = set()
        
        for entity_type, patterns in cls.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match and len(match) >= 2 and match not in seen:
                        entities.append((match, entity_type))
                        seen.add(match)
        
        return entities
    
    @classmethod
    def extract_key_information(cls, text: str) -> List[str]:
        """
        提取关键信息
        
        Args:
            text: 源文本
            
        Returns:
            关键信息列表
        """
        key_info = []
        for pattern in cls.KEY_INFO_PATTERNS:
            matches = re.findall(pattern, text)
            key_info.extend(matches)
        
        return key_info
    
    @classmethod
    def extract_topics(cls, text: str) -> List[str]:
        """
        提取主题
        
        Args:
            text: 源文本
            
        Returns:
            主题列表
        """
        topics = []
        
        # 提取引号中的内容作为主题
        quoted = re.findall(r'[""「」『』【】]([^""「」『』【】]+)[""「」『』【】]', text)
        topics.extend(quoted)
        
        # 提取标题格式的内容
        titles = re.findall(r'^#+\s*(.+)$', text, re.MULTILINE)
        topics.extend(titles)
        
        return list(dict.fromkeys(topics))[:10]
    
    @classmethod
    def calculate_importance(
        cls,
        text: str,
        entities: List[Tuple[str, EntityType]],
        key_info: List[str],
    ) -> float:
        """
        计算文本重要性评分
        
        Args:
            text: 源文本
            entities: 提取的实体
            key_info: 关键信息
            
        Returns:
            重要性评分（0-1）
        """
        score = 0.3  # 基础分
        
        # 实体数量加分
        score += min(0.2, len(entities) * 0.03)
        
        # 关键信息加分
        score += min(0.3, len(key_info) * 0.1)
        
        # 特殊关键词加分
        important_keywords = ['重要', '关键', '必须', '紧急', '核心', '主要']
        for keyword in important_keywords:
            if keyword in text:
                score += 0.05
        
        # 问句可能是重要问题
        if '？' in text or '?' in text:
            score += 0.05
        
        return min(1.0, score)


class KnowledgeGraph:
    """
    知识图谱类
    
    管理实体和关系的存储、查询和更新
    """
    
    def __init__(self):
        """
        初始化知识图谱
        """
        self._entities: Dict[str, KnowledgeEntity] = {}
        self._relations: Dict[str, KnowledgeRelation] = {}
        self._entity_name_index: Dict[str, str] = {}  # 名称到实体ID的映射
        
        logger.info("初始化知识图谱")
    
    def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: str = "",
        properties: Optional[Dict[str, Any]] = None,
        source_id: Optional[int] = None,
    ) -> KnowledgeEntity:
        """
        添加实体
        
        Args:
            name: 实体名称
            entity_type: 实体类型
            description: 描述
            properties: 属性
            source_id: 来源 ID
            
        Returns:
            创建或更新的实体
        """
        # 检查是否已存在
        entity_id = self._entity_name_index.get(name.lower())
        
        if entity_id and entity_id in self._entities:
            # 更新现有实体
            entity = self._entities[entity_id]
            entity.update_mention(source_id)
            if description:
                entity.description = description
            if properties:
                entity.properties.update(properties)
        else:
            # 创建新实体
            import uuid
            entity_id = str(uuid.uuid4())
            
            entity = KnowledgeEntity(
                id=entity_id,
                name=name,
                entity_type=entity_type,
                description=description,
                properties=properties or {},
                source_ids=[source_id] if source_id else [],
            )
            
            self._entities[entity_id] = entity
            self._entity_name_index[name.lower()] = entity_id
        
        return entity
    
    def add_relation(
        self,
        source_entity_name: str,
        target_entity_name: str,
        relation_type: RelationType,
        evidence: Optional[str] = None,
    ) -> Optional[KnowledgeRelation]:
        """
        添加关系
        
        Args:
            source_entity_name: 源实体名称
            target_entity_name: 目标实体名称
            relation_type: 关系类型
            evidence: 证据文本
            
        Returns:
            创建的关系，如果实体不存在则返回 None
        """
        source_id = self._entity_name_index.get(source_entity_name.lower())
        target_id = self._entity_name_index.get(target_entity_name.lower())
        
        if not source_id or not target_id:
            return None
        
        # 检查是否已存在相同关系
        relation_key = f"{source_id}:{relation_type.value}:{target_id}"
        if relation_key in self._relations:
            relation = self._relations[relation_key]
            if evidence:
                relation.evidence.append(evidence)
            relation.weight += 0.1
            return relation
        
        # 创建新关系
        import uuid
        relation = KnowledgeRelation(
            id=str(uuid.uuid4()),
            source_entity_id=source_id,
            target_entity_id=target_id,
            relation_type=relation_type,
            evidence=[evidence] if evidence else [],
        )
        
        self._relations[relation_key] = relation
        return relation
    
    def get_entity(self, name: str) -> Optional[KnowledgeEntity]:
        """
        根据名称获取实体
        
        Args:
            name: 实体名称
            
        Returns:
            实体对象，不存在则返回 None
        """
        entity_id = self._entity_name_index.get(name.lower())
        if entity_id:
            return self._entities.get(entity_id)
        return None
    
    def get_entity_by_id(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """
        根据 ID 获取实体
        
        Args:
            entity_id: 实体 ID
            
        Returns:
            实体对象，不存在则返回 None
        """
        return self._entities.get(entity_id)
    
    def get_related_entities(
        self,
        entity_name: str,
        relation_types: Optional[List[RelationType]] = None,
    ) -> List[Tuple[KnowledgeEntity, RelationType, float]]:
        """
        获取相关实体
        
        Args:
            entity_name: 实体名称
            relation_types: 关系类型过滤
            
        Returns:
            相关实体列表，每项为 (实体, 关系类型, 权重)
        """
        entity_id = self._entity_name_index.get(entity_name.lower())
        if not entity_id:
            return []
        
        related = []
        
        for relation in self._relations.values():
            if relation_types and relation.relation_type not in relation_types:
                continue
            
            if relation.source_entity_id == entity_id:
                target = self._entities.get(relation.target_entity_id)
                if target:
                    related.append((target, relation.relation_type, relation.weight))
            
            elif relation.target_entity_id == entity_id:
                source = self._entities.get(relation.source_entity_id)
                if source:
                    related.append((source, relation.relation_type, relation.weight))
        
        return sorted(related, key=lambda x: x[2], reverse=True)
    
    def get_all_entities(self) -> List[KnowledgeEntity]:
        """
        获取所有实体
        
        Returns:
            实体列表
        """
        return list(self._entities.values())
    
    def get_all_relations(self) -> List[KnowledgeRelation]:
        """
        获取所有关系
        
        Returns:
            关系列表
        """
        return list(self._relations.values())
    
    def search_entities(
        self,
        query: str,
        entity_types: Optional[List[EntityType]] = None,
        top_k: int = 10,
    ) -> List[KnowledgeEntity]:
        """
        搜索实体
        
        Args:
            query: 搜索关键词
            entity_types: 实体类型过滤
            top_k: 返回数量
            
        Returns:
            匹配的实体列表
        """
        results = []
        query_lower = query.lower()
        
        for entity in self._entities.values():
            if entity_types and entity.entity_type not in entity_types:
                continue
            
            # 名称匹配
            if query_lower in entity.name.lower():
                results.append(entity)
                continue
            
            # 别名匹配
            for alias in entity.aliases:
                if query_lower in alias.lower():
                    results.append(entity)
                    break
        
        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:top_k]
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出状态
        
        Returns:
            状态字典
        """
        return {
            "entities": [e.to_dict() for e in self._entities.values()],
            "relations": [r.to_dict() for r in self._relations.values()],
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        导入状态
        
        Args:
            state: 状态字典
        """
        self._entities.clear()
        self._relations.clear()
        self._entity_name_index.clear()
        
        for entity_data in state.get("entities", []):
            entity = KnowledgeEntity.from_dict(entity_data)
            self._entities[entity.id] = entity
            self._entity_name_index[entity.name.lower()] = entity.id
        
        for relation_data in state.get("relations", []):
            relation = KnowledgeRelation.from_dict(relation_data)
            relation_key = f"{relation.source_entity_id}:{relation.relation_type.value}:{relation.target_entity_id}"
            self._relations[relation_key] = relation


class WorkingMemory:
    """
    工作记忆类
    
    管理短期重要信息的存储和检索
    支持分钟级记忆更新机制
    """
    
    # 默认最大记忆数量
    DEFAULT_MAX_ITEMS = 1000
    
    # 更新间隔（秒）
    UPDATE_INTERVAL = 60
    
    # 记忆衰减因子
    DECAY_FACTOR = 0.95
    
    def __init__(
        self,
        max_items: int = DEFAULT_MAX_ITEMS,
        use_vector_store: bool = True,
    ):
        """
        初始化工作记忆
        
        Args:
            max_items: 最大记忆数量
            use_vector_store: 是否使用向量存储
        """
        self.max_items = max_items
        self.use_vector_store = use_vector_store
        
        # 知识图谱
        self._knowledge_graph = KnowledgeGraph()
        
        # 工作记忆项
        self._items: Dict[int, WorkingMemoryItem] = {}
        self._next_id = 1
        
        # 最后更新时间
        self._last_update = datetime.utcnow()
        
        logger.info(
            f"初始化工作记忆: max_items={max_items}, "
            f"use_vector_store={use_vector_store}"
        )
    
    @property
    def knowledge_graph(self) -> KnowledgeGraph:
        """
        获取知识图谱
        
        Returns:
            知识图谱实例
        """
        return self._knowledge_graph
    
    @property
    def item_count(self) -> int:
        """
        获取记忆项数量
        
        Returns:
            记忆项数量
        """
        return len(self._items)
    
    async def add_memory(
        self,
        content: str,
        source_type: str = "conversation",
        source_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkingMemoryItem:
        """
        添加工作记忆
        
        Args:
            content: 记忆内容
            source_type: 来源类型
            source_id: 来源 ID
            tags: 标签
            metadata: 元数据
            
        Returns:
            创建的工作记忆项
        """
        # 提取实体和关键信息
        entities = InformationExtractor.extract_entities(content)
        key_info = InformationExtractor.extract_key_information(content)
        topics = InformationExtractor.extract_topics(content)
        
        # 计算重要性
        importance = InformationExtractor.calculate_importance(content, entities, key_info)
        
        # 添加实体到知识图谱
        entity_ids = []
        for entity_name, entity_type in entities:
            entity = self._knowledge_graph.add_entity(
                name=entity_name,
                entity_type=entity_type,
                source_id=source_id,
            )
            entity_ids.append(entity.id)
        
        # 创建共现关系
        for i, entity_id_1 in enumerate(entity_ids):
            for entity_id_2 in entity_ids[i+1:]:
                entity_1 = self._knowledge_graph.get_entity_by_id(entity_id_1)
                entity_2 = self._knowledge_graph.get_entity_by_id(entity_id_2)
                if entity_1 and entity_2:
                    self._knowledge_graph.add_relation(
                        source_entity_name=entity_1.name,
                        target_entity_name=entity_2.name,
                        relation_type=RelationType.MENTIONED_WITH,
                        evidence=content[:100],
                    )
        
        # 创建记忆项
        item = WorkingMemoryItem(
            id=self._next_id,
            content=content,
            importance=importance,
            entity_ids=entity_ids,
            tags=tags or topics,
            source_type=source_type,
            source_id=source_id,
            metadata=metadata or {},
        )
        
        self._items[item.id] = item
        self._next_id += 1
        
        logger.debug(
            f"添加工作记忆: id={item.id}, importance={importance:.2f}, "
            f"entities={len(entity_ids)}"
        )
        
        return item
    
    async def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[WorkingMemoryItem]:
        """
        更新工作记忆
        
        Args:
            memory_id: 记忆 ID
            content: 新内容
            importance: 新重要性
            tags: 新标签
            
        Returns:
            更新后的记忆项，不存在则返回 None
        """
        item = self._items.get(memory_id)
        if not item:
            return None
        
        if content is not None:
            item.content = content
            # 重新提取实体
            entities = InformationExtractor.extract_entities(content)
            entity_ids = []
            for entity_name, entity_type in entities:
                entity = self._knowledge_graph.add_entity(name=entity_name, entity_type=entity_type)
                entity_ids.append(entity.id)
            item.entity_ids = entity_ids
        
        if importance is not None:
            item.importance = importance
        
        if tags is not None:
            item.tags = tags
        
        item.last_accessed = datetime.utcnow().isoformat()
        
        return item
    
    async def get_memory(self, memory_id: int) -> Optional[WorkingMemoryItem]:
        """
        获取工作记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            记忆项，不存在则返回 None
        """
        item = self._items.get(memory_id)
        if item:
            item.access_count += 1
            item.last_accessed = datetime.utcnow().isoformat()
        return item
    
    async def search_memories(
        self,
        query: str,
        top_k: int = 10,
        min_importance: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> List[WorkingMemoryItem]:
        """
        搜索工作记忆
        
        Args:
            query: 搜索关键词
            top_k: 返回数量
            min_importance: 最小重要性
            tags: 标签过滤
            
        Returns:
            匹配的记忆列表
        """
        results = []
        query_lower = query.lower()
        
        for item in self._items.values():
            # 重要性过滤
            if item.importance < min_importance:
                continue
            
            # 标签过滤
            if tags and not any(tag in item.tags for tag in tags):
                continue
            
            # 内容匹配
            score = 0.0
            if query_lower in item.content.lower():
                score = 1.0
            else:
                # 实体匹配
                for entity_id in item.entity_ids:
                    entity = self._knowledge_graph.get_entity_by_id(entity_id)
                    if entity and query_lower in entity.name.lower():
                        score = 0.8
                        break
            
            if score > 0:
                results.append((item, score))
        
        # 按分数和重要性排序
        results.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
        return [item for item, _ in results[:top_k]]
    
    async def get_memories_by_entity(
        self,
        entity_name: str,
        top_k: int = 10,
    ) -> List[WorkingMemoryItem]:
        """
        根据实体获取相关记忆
        
        Args:
            entity_name: 实体名称
            top_k: 返回数量
            
        Returns:
            相关记忆列表
        """
        entity = self._knowledge_graph.get_entity(entity_name)
        if not entity:
            return []
        
        results = []
        for item in self._items.values():
            if entity.id in item.entity_ids:
                results.append(item)
        
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:top_k]
    
    async def decay_memories(self) -> int:
        """
        记忆衰减处理
        
        Returns:
            衰减处理的记忆数量
        """
        now = datetime.utcnow()
        
        # 检查是否需要更新
        if (now - self._last_update).total_seconds() < self.UPDATE_INTERVAL:
            return 0
        
        self._last_update = now
        decayed_count = 0
        
        for item in self._items.values():
            # 计算衰减
            old_importance = item.importance
            item.importance *= self.DECAY_FACTOR
            
            # 访问次数增加重要性
            if item.access_count > 0:
                item.importance += 0.05 * item.access_count
                item.access_count = 0
            
            if item.importance != old_importance:
                decayed_count += 1
        
        logger.debug(f"记忆衰减处理: 处理了 {decayed_count} 条记忆")
        return decayed_count
    
    async def cleanup_memories(self) -> int:
        """
        清理低重要性记忆
        
        Returns:
            清理的记忆数量
        """
        # 检查是否超过最大数量
        if len(self._items) <= self.max_items:
            return 0
        
        # 按重要性排序
        sorted_items = sorted(
            self._items.items(),
            key=lambda x: x[1].importance,
        )
        
        # 移除最低重要性的记忆
        remove_count = len(self._items) - self.max_items
        for i in range(remove_count):
            memory_id = sorted_items[i][0]
            del self._items[memory_id]
        
        logger.info(f"清理低重要性记忆: 移除了 {remove_count} 条记忆")
        return remove_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        # 按重要性分布
        importance_dist = {"high": 0, "medium": 0, "low": 0}
        for item in self._items.values():
            if item.importance >= 0.7:
                importance_dist["high"] += 1
            elif item.importance >= 0.4:
                importance_dist["medium"] += 1
            else:
                importance_dist["low"] += 1
        
        # 按来源分布
        source_dist: Dict[str, int] = {}
        for item in self._items.values():
            source_dist[item.source_type] = source_dist.get(item.source_type, 0) + 1
        
        return {
            "total_items": len(self._items),
            "max_items": self.max_items,
            "entity_count": len(self._knowledge_graph.get_all_entities()),
            "relation_count": len(self._knowledge_graph.get_all_relations()),
            "importance_distribution": importance_dist,
            "source_distribution": source_dist,
            "last_update": self._last_update.isoformat(),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出状态
        
        Returns:
            状态字典
        """
        return {
            "items": [item.to_dict() for item in self._items.values()],
            "knowledge_graph": self._knowledge_graph.export_state(),
            "next_id": self._next_id,
            "last_update": self._last_update.isoformat(),
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        导入状态
        
        Args:
            state: 状态字典
        """
        self._items.clear()
        
        for item_data in state.get("items", []):
            item = WorkingMemoryItem(
                id=item_data.get("id", 0),
                content=item_data.get("content", ""),
                importance=item_data.get("importance", 0.5),
                entity_ids=item_data.get("entity_ids", []),
                relation_ids=item_data.get("relation_ids", []),
                tags=item_data.get("tags", []),
                source_type=item_data.get("source_type", "conversation"),
                source_id=item_data.get("source_id"),
                created_at=item_data.get("created_at", datetime.utcnow().isoformat()),
                last_accessed=item_data.get("last_accessed", datetime.utcnow().isoformat()),
                access_count=item_data.get("access_count", 0),
                metadata=item_data.get("metadata", {}),
            )
            self._items[item.id] = item
        
        self._knowledge_graph.import_state(state.get("knowledge_graph", {}))
        self._next_id = state.get("next_id", 1)
        
        if "last_update" in state:
            self._last_update = datetime.fromisoformat(state["last_update"])
