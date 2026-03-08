"""
记忆服务整合层
整合瞬时记忆、工作记忆和长期记忆，提供统一的记忆管理接口
支持记忆的自动流转、重要信息提取和跨层检索
使用数据库作为唯一存储后端
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, MemoryType, MemoryCategory


class MemoryServiceConfig:
    """
    记忆服务配置类
    
    定义记忆服务的各项配置参数
    """
    
    # 瞬时记忆配置
    INSTANT_MAX_TOKENS = 100000  # 瞬时记忆最大 Token 数
    INSTANT_EXPIRE_HOURS = 1  # 即时记忆过期时间（小时）
    
    # 工作记忆配置
    WORKING_MAX_ITEMS = 1000  # 工作记忆最大条目数
    
    # 长期记忆配置
    LONG_TERM_MAX_MEMORIES = 10000  # 长期记忆最大条目数
    
    # 记忆流转阈值
    WORKING_TO_LONG_TERM_THRESHOLD = 0.7  # 工作记忆转长期记忆的重要性阈值
    CONSOLIDATION_ACCESS_COUNT = 3  # 巩固所需的最小访问次数
    
    # 记忆遗忘配置
    WORKING_DECAY_HOURS = 1  # 工作记忆衰减时间（小时）
    LONG_TERM_FORGET_DAYS = 30  # 长期记忆遗忘天数
    MIN_ACCESS_FOR_KEEP = 2  # 保持记忆的最小访问次数
    
    # 记忆提取配置
    IMPORTANCE_BOOST_FOR_KEY_INFO = 0.2  # 关键信息的重要性加成
    IMPORTANCE_BOOST_FOR_ENTITIES = 0.1  # 实体丰富的重要性加成


class MemoryService:
    """
    记忆服务整合层
    
    整合三层记忆架构，提供统一的记忆管理接口：
    - 瞬时记忆（INSTANT）：滑动窗口上下文管理
    - 工作记忆（WORKING）：短期重要信息存储
    - 长期记忆（LONG_TERM）：持久化的重要信息存储
    
    所有记忆都存储在数据库中，确保数据一致性和可靠性。
    """
    
    def __init__(
        self,
        db: AsyncSession,
        config: Optional[MemoryServiceConfig] = None,
    ):
        """
        初始化记忆服务
        
        Args:
            db: 数据库会话
            config: 配置对象，为 None 时使用默认配置
        """
        self.db = db
        self.config = config or MemoryServiceConfig()
        
        # 当前活跃会话
        self._current_session_id: Optional[str] = None
        self._current_conversation_id: Optional[str] = None
        
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
    
    async def add_instant_memory(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        添加即时记忆（对话上下文）
        
        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
            metadata: 元数据
            
        Returns:
            创建的记忆对象
        """
        if not self._current_conversation_id:
            raise ValueError("未设置当前会话，请先调用 set_session()")
        
        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(hours=self.config.INSTANT_EXPIRE_HOURS)
        
        memory = Memory(
            memory_type=MemoryType.INSTANT,
            content=f"[{role}] {content}",
            importance=0.3,  # 即时记忆默认重要性较低
            source_type="conversation",
            session_id=self._current_session_id,
            conversation_id=self._current_conversation_id,
            metadata=metadata or {},
            expires_at=expires_at,
        )
        
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        
        # 异步提取重要信息到工作记忆
        await self._extract_and_store_important_info(content, role)
        
        return memory
    
    async def get_instant_memories(
        self,
        conversation_id: Optional[str] = None,
    ) -> List[Memory]:
        """
        获取即时记忆列表
        
        Args:
            conversation_id: 对话 ID，为 None 时使用当前对话
            
        Returns:
            即时记忆列表
        """
        conv_id = conversation_id or self._current_conversation_id
        if not conv_id:
            return []
        
        # 清理过期的即时记忆
        await self._cleanup_expired_instant_memories(conv_id)
        
        # 查询即时记忆
        stmt = select(Memory).where(
            Memory.memory_type == MemoryType.INSTANT,
            Memory.conversation_id == conv_id,
            Memory.status == "active",
        ).order_by(Memory.created_at.asc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
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
        memories = await self.get_instant_memories(conversation_id)
        
        messages = []
        for memory in memories:
            # 解析角色和内容
            content = memory.content
            role = "user"
            if content.startswith("[user] "):
                role = "user"
                content = content[7:]
            elif content.startswith("[assistant] "):
                role = "assistant"
                content = content[11:]
            elif content.startswith("[system] "):
                role = "system"
                content = content[9:]
            
            messages.append({
                "role": role,
                "content": content,
            })
        
        return messages
    
    async def _cleanup_expired_instant_memories(self, conversation_id: str) -> int:
        """
        清理过期的即时记忆
        
        Args:
            conversation_id: 对话 ID
            
        Returns:
            删除的记忆数量
        """
        stmt = delete(Memory).where(
            Memory.memory_type == MemoryType.INSTANT,
            Memory.conversation_id == conversation_id,
            Memory.expires_at < datetime.utcnow(),
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount
    
    # ==================== 工作记忆操作 ====================
    
    async def add_to_working_memory(
        self,
        content: str,
        source_type: str = "conversation",
        source_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entities: Optional[List[str]] = None,
    ) -> Memory:
        """
        添加工作记忆
        
        Args:
            content: 记忆内容
            source_type: 来源类型
            source_id: 来源 ID
            tags: 标签
            metadata: 元数据
            entities: 关联实体
            
        Returns:
            创建的工作记忆
        """
        # 计算重要性
        importance = await self._calculate_importance(content, entities or [])
        
        memory = Memory(
            memory_type=MemoryType.WORKING,
            content=content,
            importance=importance,
            source_type=source_type,
            source_id=source_id,
            session_id=self._current_session_id,
            conversation_id=self._current_conversation_id,
            tags=tags or [],
            metadata=metadata or {},
            entities=entities or [],
        )
        
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        
        # 检查是否需要转存到长期记忆
        if memory.importance >= self.config.WORKING_TO_LONG_TERM_THRESHOLD:
            await self._promote_to_long_term(memory)
        
        return memory
    
    async def search_working_memory(
        self,
        query: str,
        top_k: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """
        搜索工作记忆
        
        Args:
            query: 搜索关键词
            top_k: 返回数量
            min_importance: 最小重要性
            
        Returns:
            匹配的工作记忆列表
        """
        # 使用简单的 LIKE 搜索（实际应使用向量搜索）
        search_term = f"%{query}%"
        
        stmt = select(Memory).where(
            Memory.memory_type == MemoryType.WORKING,
            Memory.status == "active",
            Memory.importance >= min_importance,
            Memory.content.ilike(search_term),
        ).order_by(
            Memory.importance.desc()
        ).limit(top_k)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_working_memory_stats(self) -> Dict[str, Any]:
        """
        获取工作记忆统计信息
        
        Returns:
            统计信息字典
        """
        # 总数
        count_stmt = select(func.count(Memory.id)).where(
            Memory.memory_type == MemoryType.WORKING,
            Memory.status == "active",
        )
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # 平均重要性
        avg_stmt = select(func.avg(Memory.importance)).where(
            Memory.memory_type == MemoryType.WORKING,
            Memory.status == "active",
        )
        avg_result = await self.db.execute(avg_stmt)
        avg_importance = avg_result.scalar() or 0.0
        
        return {
            "total_count": total_count,
            "avg_importance": float(avg_importance),
        }
    
    # ==================== 长期记忆操作 ====================
    
    async def add_to_long_term_memory(
        self,
        content: str,
        category: str = "fact",
        keywords: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        添加长期记忆
        
        Args:
            content: 记忆内容
            category: 记忆分类
            keywords: 关键词列表
            entities: 实体列表
            tags: 标签
            metadata: 元数据
            
        Returns:
            创建的长期记忆
        """
        if not self._current_session_id:
            raise ValueError("未设置当前会话，请先调用 set_session()")
        
        # 计算重要性
        importance = await self._calculate_importance(content, entities or [])
        
        memory = Memory(
            memory_type=MemoryType.LONG_TERM,
            content=content,
            importance=importance,
            category=category,
            keywords=keywords or [],
            entities=entities or [],
            tags=tags or [],
            metadata=metadata or {},
            session_id=self._current_session_id,
        )
        
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        
        return memory
    
    async def search_long_term_memory(
        self,
        query: str,
        top_k: int = 10,
        categories: Optional[List[str]] = None,
        min_importance: float = 0.0,
    ) -> List[Memory]:
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
        search_term = f"%{query}%"
        
        stmt = select(Memory).where(
            Memory.memory_type == MemoryType.LONG_TERM,
            Memory.status == "active",
            Memory.importance >= min_importance,
            Memory.content.ilike(search_term),
        )
        
        if categories:
            stmt = stmt.where(Memory.category.in_(categories))
        
        stmt = stmt.order_by(Memory.importance.desc()).limit(top_k)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_long_term_memory_stats(self) -> Dict[str, Any]:
        """
        获取长期记忆统计信息
        
        Returns:
            统计信息字典
        """
        # 总数
        count_stmt = select(func.count(Memory.id)).where(
            Memory.memory_type == MemoryType.LONG_TERM,
            Memory.status == "active",
        )
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # 按分类统计
        category_stmt = select(
            Memory.category,
            func.count(Memory.id)
        ).where(
            Memory.memory_type == MemoryType.LONG_TERM,
            Memory.status == "active",
        ).group_by(Memory.category)
        
        category_result = await self.db.execute(category_stmt)
        category_counts = {row[0]: row[1] for row in category_result.all()}
        
        # 平均重要性
        avg_stmt = select(func.avg(Memory.importance)).where(
            Memory.memory_type == MemoryType.LONG_TERM,
            Memory.status == "active",
        )
        avg_result = await self.db.execute(avg_stmt)
        avg_importance = avg_result.scalar() or 0.0
        
        return {
            "total_count": total_count,
            "category_counts": category_counts,
            "avg_importance": float(avg_importance),
        }
    
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
            working_memories = await self.search_working_memory(
                query=query,
                top_k=top_k,
            )
            for memory in working_memories:
                results.append({
                    "id": memory.id,
                    "content": memory.content,
                    "importance": memory.importance,
                    "source": "working_memory",
                    "entities": memory.entities or [],
                    "tags": memory.tags or [],
                    "created_at": memory.created_at.isoformat(),
                })
        
        # 检索长期记忆
        if include_long_term:
            long_term_memories = await self.search_long_term_memory(
                query=query,
                top_k=top_k,
            )
            for memory in long_term_memories:
                results.append({
                    "id": memory.id,
                    "content": memory.content,
                    "importance": memory.importance,
                    "source": "long_term_memory",
                    "category": memory.category,
                    "entities": memory.entities or [],
                    "tags": memory.tags or [],
                    "created_at": memory.created_at.isoformat(),
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
        # 获取瞬时记忆上下文
        instant_context = await self.get_context_for_llm(conversation_id)
        
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
        # 简单的关键信息提取（实际应使用 NLP）
        key_info = self._extract_key_information(content)
        
        if not key_info:
            return
        
        # 计算重要性
        importance = await self._calculate_importance(content, [])
        
        # 如果重要性足够高，存储到工作记忆
        if importance >= 0.5:
            await self.add_to_working_memory(
                content=content,
                source_type="conversation",
                tags=[role] + [info[:20] for info in key_info[:3]],
                metadata={
                    "key_info": key_info,
                },
            )
    
    def _extract_key_information(self, content: str) -> List[str]:
        """
        提取关键信息
        
        Args:
            content: 内容
            
        Returns:
            关键信息列表
        """
        # 简单实现：提取包含关键词的句子
        keywords = ["喜欢", "偏好", "希望", "想要", "重要", "记住", "项目", "任务"]
        
        key_info = []
        sentences = content.split("。")
        for sentence in sentences:
            if any(kw in sentence for kw in keywords):
                key_info.append(sentence.strip())
        
        return key_info
    
    async def _calculate_importance(
        self,
        content: str,
        entities: List[str],
    ) -> float:
        """
        计算记忆重要性
        
        Args:
            content: 内容
            entities: 实体列表
            
        Returns:
            重要性分数（0-1）
        """
        importance = 0.5
        
        # 基于关键词调整
        high_importance_keywords = ["重要", "记住", "偏好", "喜欢", "项目"]
        if any(kw in content for kw in high_importance_keywords):
            importance += self.config.IMPORTANCE_BOOST_FOR_KEY_INFO
        
        # 基于实体数量调整
        if len(entities) > 3:
            importance += self.config.IMPORTANCE_BOOST_FOR_ENTITIES
        
        # 限制在 0-1 范围内
        return min(max(importance, 0.0), 1.0)
    
    async def _promote_to_long_term(self, working_memory: Memory) -> None:
        """
        将工作记忆提升到长期记忆
        
        Args:
            working_memory: 工作记忆对象
        """
        # 确定记忆分类
        category = self._determine_category(working_memory.content)
        
        # 创建长期记忆
        await self.add_to_long_term_memory(
            content=working_memory.content,
            category=category,
            keywords=working_memory.tags,
            entities=working_memory.entities or [],
            tags=working_memory.tags,
            metadata=working_memory.metadata,
        )
        
        logger.debug(
            f"工作记忆提升到长期记忆: id={working_memory.id}, "
            f"category={category}"
        )
    
    def _determine_category(self, content: str) -> str:
        """
        根据内容特征确定记忆分类
        
        Args:
            content: 内容
            
        Returns:
            记忆分类
        """
        content_lower = content.lower()
        
        # 基于关键词判断分类
        if any(kw in content_lower for kw in ["喜欢", "偏好", "希望", "想要"]):
            return "preference"
        
        if any(kw in content_lower for kw in ["项目", "任务", "计划"]):
            return "project"
        
        if any(kw in content_lower for kw in ["日程", "会议", "时间", "日期"]):
            return "schedule"
        
        if any(kw in content_lower for kw in ["技能", "能力", "方法", "步骤"]):
            return "skill"
        
        if any(kw in content_lower for kw in ["经验", "教训", "总结"]):
            return "experience"
        
        # 默认为事实
        return "fact"
    
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
        decay_threshold = datetime.utcnow() - timedelta(hours=self.config.WORKING_DECAY_HOURS)
        stmt = update(Memory).where(
            Memory.memory_type == MemoryType.WORKING,
            Memory.created_at < decay_threshold,
            Memory.importance < 0.5,
            Memory.status == "active",
        ).values(status="forgotten")
        result = await self.db.execute(stmt)
        stats["working_decayed"] = result.rowcount
        
        # 长期记忆巩固
        consolidate_threshold = datetime.utcnow() - timedelta(days=7)
        stmt = update(Memory).where(
            Memory.memory_type == MemoryType.LONG_TERM,
            Memory.access_count >= self.config.CONSOLIDATION_ACCESS_COUNT,
            Memory.created_at < consolidate_threshold,
            Memory.is_consolidated == False,
            Memory.status == "active",
        ).values(is_consolidated=True)
        result = await self.db.execute(stmt)
        stats["long_term_consolidated"] = result.rowcount
        
        # 长期记忆遗忘
        forget_threshold = datetime.utcnow() - timedelta(days=self.config.LONG_TERM_FORGET_DAYS)
        stmt = update(Memory).where(
            Memory.memory_type == MemoryType.LONG_TERM,
            Memory.last_accessed_at < forget_threshold,
            Memory.access_count < self.config.MIN_ACCESS_FOR_KEEP,
            Memory.status == "active",
        ).values(status="forgotten")
        result = await self.db.execute(stmt)
        stats["long_term_forgotten"] = result.rowcount
        
        await self.db.commit()
        
        logger.info(f"记忆巩固完成: {stats}")
        
        return stats
    
    async def reinforce_memory(
        self,
        memory_id: int,
    ) -> bool:
        """
        强化记忆
        
        通过访问或引用来强化记忆，提高其保留率
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            是否成功强化
        """
        stmt = select(Memory).where(Memory.id == memory_id)
        result = await self.db.execute(stmt)
        memory = result.scalar_one_or_none()
        
        if not memory:
            return False
        
        # 增加访问次数
        memory.increment_access()
        await self.db.commit()
        
        return True
    
    # ==================== 统计与监控 ====================
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有记忆层的统计信息
        
        Returns:
            综合统计信息字典
        """
        instant_stats = await self._get_instant_memory_stats()
        working_stats = await self.get_working_memory_stats()
        long_term_stats = await self.get_long_term_memory_stats()
        
        return {
            "instant_memory": instant_stats,
            "working_memory": working_stats,
            "long_term_memory": long_term_stats,
            "current_session": self._current_session_id,
            "current_conversation": self._current_conversation_id,
        }
    
    async def _get_instant_memory_stats(self) -> Dict[str, Any]:
        """
        获取即时记忆统计信息
        
        Returns:
            统计信息字典
        """
        # 总数
        count_stmt = select(func.count(Memory.id)).where(
            Memory.memory_type == MemoryType.INSTANT,
            Memory.status == "active",
        )
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # 当前对话的消息数
        current_count = 0
        if self._current_conversation_id:
            current_stmt = select(func.count(Memory.id)).where(
                Memory.memory_type == MemoryType.INSTANT,
                Memory.conversation_id == self._current_conversation_id,
                Memory.status == "active",
            )
            current_result = await self.db.execute(current_stmt)
            current_count = current_result.scalar() or 0
        
        return {
            "total_count": total_count,
            "current_conversation_count": current_count,
        }
    
    async def clear_all(self) -> None:
        """
        清空所有记忆
        """
        stmt = delete(Memory)
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.warning("所有记忆已清空")


def get_memory_service(db: AsyncSession) -> MemoryService:
    """
    获取记忆服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        记忆服务实例
    """
    return MemoryService(db)
