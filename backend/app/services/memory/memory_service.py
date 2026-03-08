"""
记忆服务整合层
整合瞬时记忆、工作记忆和长期记忆，提供统一的记忆管理接口
支持记忆的自动流转、重要信息提取和跨层检索
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.services.memory.instant_memory import (
    InstantMemory,
    InstantMemoryManager,
    MessageContext,
    TokenCounter,
)
from app.services.memory.working_memory import (
    EntityType,
    InformationExtractor,
    KnowledgeEntity,
    KnowledgeGraph,
    KnowledgeRelation,
    RelationType,
    WorkingMemory,
    WorkingMemoryItem,
)
from app.services.memory.long_term_memory import (
    CrossSessionIndex,
    ImportanceScorer,
    LongTermMemory,
    LongTermMemoryItem,
    MemoryCategory,
    MemoryForgetting,
    MemoryStatus,
)


class MemoryServiceConfig:
    """
    记忆服务配置类
    
    定义记忆服务的各项配置参数
    """
    
    # 瞬时记忆配置
    INSTANT_MAX_TOKENS = 100000  # 瞬时记忆最大 Token 数
    
    # 工作记忆配置
    WORKING_MAX_ITEMS = 1000  # 工作记忆最大条目数
    
    # 长期记忆配置
    LONG_TERM_MAX_MEMORIES = 10000  # 长期记忆最大条目数
    
    # 记忆流转阈值
    WORKING_TO_LONG_TERM_THRESHOLD = 0.7  # 工作记忆转长期记忆的重要性阈值
    CONSOLIDATION_ACCESS_COUNT = 3  # 巩固所需的最小访问次数
    
    # 自动保存配置
    AUTO_SAVE_INTERVAL = 300  # 自动保存间隔（秒）
    PERSISTENCE_DIR = "./data/memory"  # 持久化目录
    
    # 记忆提取配置
    IMPORTANCE_BOOST_FOR_KEY_INFO = 0.2  # 关键信息的重要性加成
    IMPORTANCE_BOOST_FOR_ENTITIES = 0.1  # 实体丰富的重要性加成


class MemoryService:
    """
    记忆服务整合层
    
    整合三层记忆架构，提供统一的记忆管理接口：
    - 瞬时记忆：滑动窗口上下文管理（100K tokens）
    - 工作记忆：短期重要信息存储（分钟级更新）
    - 长期记忆：持久化的重要信息存储（跨会话）
    
    支持功能：
    - 记忆自动流转：瞬时 -> 工作 -> 长期
    - 重要信息自动提取和存储
    - 跨层记忆检索
    - 记忆巩固和遗忘机制
    """
    
    def __init__(
        self,
        config: Optional[MemoryServiceConfig] = None,
        enable_persistence: bool = True,
    ):
        """
        初始化记忆服务
        
        Args:
            config: 配置对象，为 None 时使用默认配置
            enable_persistence: 是否启用持久化
        """
        self.config = config or MemoryServiceConfig()
        self.enable_persistence = enable_persistence
        
        # 初始化三层记忆
        self.instant_memory_manager = InstantMemoryManager(
            default_max_tokens=self.config.INSTANT_MAX_TOKENS
        )
        
        self.working_memory = WorkingMemory(
            max_items=self.config.WORKING_MAX_ITEMS,
            use_vector_store=True,
        )
        
        self.long_term_memory = LongTermMemory(
            max_memories=self.config.LONG_TERM_MAX_MEMORIES,
            enable_auto_consolidation=True,
        )
        
        # 当前活跃会话
        self._current_session_id: Optional[str] = None
        self._current_conversation_id: Optional[str] = None
        
        # 最后保存时间
        self._last_save_time = datetime.utcnow()
        
        # 持久化目录
        if self.enable_persistence:
            self._persistence_dir = Path(self.config.PERSISTENCE_DIR)
            self._persistence_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"初始化记忆服务: instant_max_tokens={self.config.INSTANT_MAX_TOKENS}, "
            f"working_max_items={self.config.WORKING_MAX_ITEMS}, "
            f"long_term_max_memories={self.config.LONG_TERM_MAX_MEMORIES}"
        )
    
    # ==================== 会话管理 ====================
    
    def set_session(self, session_id: str, conversation_id: Optional[str] = None) -> None:
        """
        设置当前会话
        
        Args:
            session_id: 会话 ID
            conversation_id: 对话 ID（可选）
        """
        self._current_session_id = session_id
        self._current_conversation_id = conversation_id or session_id
        
        logger.debug(f"设置当前会话: session_id={session_id}, conversation_id={conversation_id}")
    
    def get_current_session(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取当前会话信息
        
        Returns:
            元组 (session_id, conversation_id)
        """
        return self._current_session_id, self._current_conversation_id
    
    # ==================== 瞬时记忆操作 ====================
    
    async def add_message_to_context(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageContext:
        """
        添加消息到瞬时记忆上下文
        
        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
            metadata: 元数据
            
        Returns:
            创建的消息上下文对象
        """
        if not self._current_conversation_id:
            raise ValueError("未设置当前会话，请先调用 set_session()")
        
        # 获取或创建瞬时记忆
        instant_memory = self.instant_memory_manager.get_memory(self._current_conversation_id)
        
        # 添加消息
        message = instant_memory.add_message(
            role=role,
            content=content,
            metadata=metadata,
        )
        
        # 异步提取重要信息到工作记忆
        await self._extract_and_store_important_info(content, role)
        
        return message
    
    async def get_context_for_llm(
        self,
        conversation_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        获取适用于 LLM API 的上下文
        
        Args:
            conversation_id: 对话 ID，为 None 时使用当前对话
            
        Returns:
            LLM API 格式的消息列表
        """
        conv_id = conversation_id or self._current_conversation_id
        if not conv_id:
            return []
        
        instant_memory = self.instant_memory_manager.get_memory(conv_id)
        return instant_memory.get_messages_for_llm()
    
    async def get_context_stats(
        self,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取瞬时记忆统计信息
        
        Args:
            conversation_id: 对话 ID，为 None 时使用当前对话
            
        Returns:
            统计信息字典
        """
        conv_id = conversation_id or self._current_conversation_id
        if not conv_id:
            return {}
        
        instant_memory = self.instant_memory_manager.get_memory(conv_id)
        return instant_memory.get_stats()
    
    # ==================== 工作记忆操作 ====================
    
    async def add_to_working_memory(
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
        item = await self.working_memory.add_memory(
            content=content,
            source_type=source_type,
            source_id=source_id,
            tags=tags,
            metadata=metadata,
        )
        
        # 检查是否需要转存到长期记忆
        if item.importance >= self.config.WORKING_TO_LONG_TERM_THRESHOLD:
            await self._promote_to_long_term(item)
        
        return item
    
    async def search_working_memory(
        self,
        query: str,
        top_k: int = 10,
        min_importance: float = 0.0,
    ) -> List[WorkingMemoryItem]:
        """
        搜索工作记忆
        
        Args:
            query: 搜索关键词
            top_k: 返回数量
            min_importance: 最小重要性
            
        Returns:
            匹配的工作记忆列表
        """
        return await self.working_memory.search_memories(
            query=query,
            top_k=top_k,
            min_importance=min_importance,
        )
    
    async def get_working_memory_stats(self) -> Dict[str, Any]:
        """
        获取工作记忆统计信息
        
        Returns:
            统计信息字典
        """
        return await self.working_memory.get_stats()
    
    # ==================== 长期记忆操作 ====================
    
    async def add_to_long_term_memory(
        self,
        content: str,
        category: MemoryCategory = MemoryCategory.FACT,
        keywords: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LongTermMemoryItem:
        """
        添加长期记忆
        
        Args:
            content: 记忆内容
            category: 记忆分类
            keywords: 关键词列表
            entities: 实体列表
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            创建的长期记忆项
        """
        if not self._current_session_id:
            raise ValueError("未设置当前会话，请先调用 set_session()")
        
        return await self.long_term_memory.add_memory(
            content=content,
            session_id=self._current_session_id,
            category=category,
            keywords=keywords,
            entities=entities,
            tags=tags,
            metadata=metadata,
        )
    
    async def search_long_term_memory(
        self,
        query: str,
        top_k: int = 10,
        categories: Optional[List[MemoryCategory]] = None,
        min_importance: float = 0.0,
    ) -> List[LongTermMemoryItem]:
        """
        搜索长期记忆
        
        Args:
            query: 搜索关键词
            top_k: 返回数量
            categories: 分类过滤
            min_importance: 最小重要性
            
        Returns:
            匹配的长期记忆列表
        """
        return await self.long_term_memory.search_memories(
            query=query,
            top_k=top_k,
            categories=categories,
            min_importance=min_importance,
        )
    
    async def get_long_term_memory_stats(self) -> Dict[str, Any]:
        """
        获取长期记忆统计信息
        
        Returns:
            统计信息字典
        """
        return await self.long_term_memory.get_stats()
    
    # ==================== 跨层检索 ====================
    
    async def retrieve_relevant_memories(
        self,
        query: str,
        top_k: int = 10,
        include_working: bool = True,
        include_long_term: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        跨层检索相关记忆
        
        从工作记忆和长期记忆中检索相关信息
        
        Args:
            query: 搜索关键词
            top_k: 每层返回数量
            include_working: 是否包含工作记忆
            include_long_term: 是否包含长期记忆
            
        Returns:
            合并后的记忆列表
        """
        results = []
        
        # 检索工作记忆
        if include_working:
            working_results = await self.working_memory.search_memories(
                query=query,
                top_k=top_k,
            )
            for item in working_results:
                results.append({
                    "id": item.id,
                    "content": item.content,
                    "importance": item.importance,
                    "source": "working_memory",
                    "entities": item.entity_ids,
                    "tags": item.tags,
                    "created_at": item.created_at,
                })
        
        # 检索长期记忆
        if include_long_term:
            long_term_results = await self.long_term_memory.search_memories(
                query=query,
                top_k=top_k,
            )
            for item in long_term_results:
                results.append({
                    "id": item.id,
                    "content": item.content,
                    "importance": item.importance,
                    "source": "long_term_memory",
                    "category": item.category.value,
                    "entities": item.entities,
                    "tags": item.tags,
                    "created_at": item.created_at,
                })
        
        # 按重要性排序
        results.sort(key=lambda x: x["importance"], reverse=True)
        
        return results[:top_k * 2]  # 返回合并后的结果
    
    async def get_context_with_memories(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        max_memories: int = 5,
    ) -> Dict[str, Any]:
        """
        获取包含相关记忆的完整上下文
        
        整合瞬时记忆和相关记忆，用于 LLM 推理
        
        Args:
            query: 当前查询
            conversation_id: 对话 ID
            max_memories: 最大记忆数量
            
        Returns:
            包含上下文和记忆的字典
        """
        conv_id = conversation_id or self._current_conversation_id
        
        # 获取瞬时记忆上下文
        instant_context = []
        if conv_id:
            instant_memory = self.instant_memory_manager.get_memory(conv_id)
            instant_context = instant_memory.get_messages_for_llm()
        
        # 检索相关记忆
        relevant_memories = await self.retrieve_relevant_memories(
            query=query,
            top_k=max_memories,
        )
        
        # 构建记忆上下文
        memory_context = []
        if relevant_memories:
            memory_text = "相关记忆：\n"
            for mem in relevant_memories:
                memory_text += f"- {mem['content'][:200]}...\n"
            memory_context.append({
                "role": "system",
                "content": memory_text,
            })
        
        return {
            "instant_context": instant_context,
            "memory_context": memory_context,
            "relevant_memories": relevant_memories,
            "stats": {
                "instant_messages": len(instant_context),
                "memories_found": len(relevant_memories),
            },
        }
    
    # ==================== 记忆流转 ====================
    
    async def _extract_and_store_important_info(
        self,
        content: str,
        role: str,
    ) -> None:
        """
        从内容中提取重要信息并存储到工作记忆
        
        Args:
            content: 消息内容
            role: 消息角色
        """
        # 提取关键信息
        key_info = InformationExtractor.extract_key_information(content)
        
        if not key_info:
            return
        
        # 提取实体
        entities = InformationExtractor.extract_entities(content)
        
        # 计算重要性
        importance = InformationExtractor.calculate_importance(content, entities, key_info)
        
        # 如果重要性足够高，存储到工作记忆
        if importance >= 0.5:
            await self.add_to_working_memory(
                content=content,
                source_type="conversation",
                tags=[role] + [info[:20] for info in key_info[:3]],
                metadata={
                    "key_info": key_info,
                    "entities": [(e[0], e[1].value) for e in entities],
                },
            )
    
    async def _promote_to_long_term(self, working_item: WorkingMemoryItem) -> None:
        """
        将工作记忆提升到长期记忆
        
        Args:
            working_item: 工作记忆项
        """
        if not self._current_session_id:
            return
        
        # 确定记忆分类
        category = self._determine_category(working_item)
        
        # 获取实体名称
        entity_names = []
        for entity_id in working_item.entity_ids:
            entity = self.working_memory.knowledge_graph.get_entity_by_id(entity_id)
            if entity:
                entity_names.append(entity.name)
        
        # 添加到长期记忆
        await self.long_term_memory.add_memory(
            content=working_item.content,
            session_id=self._current_session_id,
            category=category,
            keywords=working_item.tags,
            entities=entity_names,
            tags=working_item.tags,
            metadata=working_item.metadata,
        )
        
        logger.debug(
            f"工作记忆提升到长期记忆: id={working_item.id}, "
            f"category={category.value}"
        )
    
    def _determine_category(self, item: WorkingMemoryItem) -> MemoryCategory:
        """
        根据内容特征确定记忆分类
        
        Args:
            item: 工作记忆项
            
        Returns:
            记忆分类
        """
        content = item.content.lower()
        tags = [t.lower() for t in item.tags]
        
        # 基于关键词判断分类
        if any(kw in content for kw in ["喜欢", "偏好", "希望", "想要"]):
            return MemoryCategory.PREFERENCE
        
        if any(kw in content for kw in ["项目", "任务", "计划"]):
            return MemoryCategory.PROJECT
        
        if any(kw in content for kw in ["日程", "会议", "时间", "日期"]):
            return MemoryCategory.SCHEDULE
        
        if any(kw in content for kw in ["技能", "能力", "方法", "步骤"]):
            return MemoryCategory.SKILL
        
        if any(kw in content for kw in ["经验", "教训", "总结"]):
            return MemoryCategory.EXPERIENCE
        
        # 基于标签判断
        if "user" in tags:
            return MemoryCategory.PREFERENCE
        
        # 默认为事实
        return MemoryCategory.FACT
    
    # ==================== 记忆巩固与遗忘 ====================
    
    async def consolidate_memories(self) -> Dict[str, int]:
        """
        执行记忆巩固
        
        将高重要性的记忆进行巩固，提高其保留率
        
        Returns:
            巩固结果统计
        """
        stats = {
            "working_decayed": 0,
            "long_term_consolidated": 0,
            "long_term_forgotten": 0,
        }
        
        # 工作记忆衰减
        stats["working_decayed"] = await self.working_memory.decay_memories()
        
        # 长期记忆自动巩固
        stats["long_term_consolidated"] = await self.long_term_memory.auto_consolidate()
        
        # 长期记忆遗忘机制
        forgetting_stats = await self.long_term_memory.apply_forgetting()
        stats["long_term_forgotten"] = forgetting_stats.get("removed", 0)
        
        logger.info(f"记忆巩固完成: {stats}")
        
        return stats
    
    async def reinforce_memory(
        self,
        memory_id: int,
        memory_type: str = "long_term",
    ) -> bool:
        """
        强化记忆
        
        通过访问或引用来强化记忆，提高其保留率
        
        Args:
            memory_id: 记忆 ID
            memory_type: 记忆类型（working/long_term）
            
        Returns:
            是否成功强化
        """
        if memory_type == "long_term":
            result = await self.long_term_memory.reinforce_memory(memory_id)
            return result is not None
        elif memory_type == "working":
            item = await self.working_memory.get_memory(memory_id)
            if item:
                # 增加访问次数来强化
                item.access_count += 5
                return True
        return False
    
    # ==================== 持久化 ====================
    
    async def save_state(self) -> None:
        """
        保存所有记忆状态到文件
        """
        if not self.enable_persistence:
            return
        
        try:
            # 保存工作记忆
            working_state = self.working_memory.export_state()
            working_file = self._persistence_dir / "working_memory.json"
            with open(working_file, "w", encoding="utf-8") as f:
                json.dump(working_state, f, ensure_ascii=False, indent=2)
            
            # 保存长期记忆
            long_term_state = self.long_term_memory.export_state()
            long_term_file = self._persistence_dir / "long_term_memory.json"
            with open(long_term_file, "w", encoding="utf-8") as f:
                json.dump(long_term_state, f, ensure_ascii=False, indent=2)
            
            # 保存瞬时记忆
            instant_state = self.instant_memory_manager.export_all_states()
            instant_file = self._persistence_dir / "instant_memory.json"
            with open(instant_file, "w", encoding="utf-8") as f:
                json.dump(instant_state, f, ensure_ascii=False, indent=2)
            
            self._last_save_time = datetime.utcnow()
            
            logger.info("记忆状态保存完成")
            
        except Exception as e:
            logger.error(f"保存记忆状态失败: {e}")
    
    async def load_state(self) -> None:
        """
        从文件加载所有记忆状态
        """
        if not self.enable_persistence:
            return
        
        try:
            # 加载工作记忆
            working_file = self._persistence_dir / "working_memory.json"
            if working_file.exists():
                with open(working_file, "r", encoding="utf-8") as f:
                    working_state = json.load(f)
                self.working_memory.import_state(working_state)
                logger.info("工作记忆状态加载完成")
            
            # 加载长期记忆
            long_term_file = self._persistence_dir / "long_term_memory.json"
            if long_term_file.exists():
                with open(long_term_file, "r", encoding="utf-8") as f:
                    long_term_state = json.load(f)
                self.long_term_memory.import_state(long_term_state)
                logger.info("长期记忆状态加载完成")
            
            # 加载瞬时记忆
            instant_file = self._persistence_dir / "instant_memory.json"
            if instant_file.exists():
                with open(instant_file, "r", encoding="utf-8") as f:
                    instant_state = json.load(f)
                for conv_id, state in instant_state.items():
                    memory = InstantMemory.import_state(state)
                    self.instant_memory_manager._memories[conv_id] = memory
                logger.info("瞬时记忆状态加载完成")
            
        except Exception as e:
            logger.error(f"加载记忆状态失败: {e}")
    
    # ==================== 统计与监控 ====================
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有记忆层的统计信息
        
        Returns:
            综合统计信息字典
        """
        working_stats = await self.working_memory.get_stats()
        long_term_stats = await self.long_term_memory.get_stats()
        instant_stats = self.instant_memory_manager.get_all_stats()
        
        return {
            "instant_memory": instant_stats,
            "working_memory": working_stats,
            "long_term_memory": long_term_stats,
            "current_session": self._current_session_id,
            "current_conversation": self._current_conversation_id,
            "last_save_time": self._last_save_time.isoformat(),
        }
    
    async def clear_all(self) -> None:
        """
        清空所有记忆
        """
        self.instant_memory_manager.clear_all()
        self.working_memory._items.clear()
        self.working_memory._knowledge_graph = KnowledgeGraph()
        self.long_term_memory._memories.clear()
        self.long_term_memory._index = CrossSessionIndex()
        
        logger.warning("所有记忆已清空")


# 全局记忆服务实例
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """
    获取全局记忆服务实例
    
    Returns:
        记忆服务实例
    """
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service


async def init_memory_service(
    config: Optional[MemoryServiceConfig] = None,
    enable_persistence: bool = True,
) -> MemoryService:
    """
    初始化全局记忆服务
    
    Args:
        config: 配置对象
        enable_persistence: 是否启用持久化
        
    Returns:
        初始化后的记忆服务实例
    """
    global _memory_service
    _memory_service = MemoryService(
        config=config,
        enable_persistence=enable_persistence,
    )
    
    # 加载持久化状态
    if enable_persistence:
        await _memory_service.load_state()
    
    return _memory_service
