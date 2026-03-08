"""
数据迁移脚本：将 JSON 文件中的记忆数据迁移到数据库
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.memory import Memory, MemoryType


class MemoryMigrator:
    """
    记忆数据迁移器
    
    将 JSON 文件中的记忆数据迁移到数据库
    """
    
    def __init__(self, data_dir: str = "./data/memory"):
        """
        初始化迁移器
        
        Args:
            data_dir: JSON 文件目录
        """
        self.data_dir = Path(data_dir)
        
    async def migrate_all(self) -> Dict[str, int]:
        """
        迁移所有记忆数据
        
        Returns:
            迁移统计信息
        """
        stats = {
            "working_memory_migrated": 0,
            "long_term_memory_migrated": 0,
            "instant_memory_migrated": 0,
            "errors": 0,
        }
        
        async with AsyncSessionLocal() as db:
            # 迁移工作记忆
            working_file = self.data_dir / "working_memory.json"
            if working_file.exists():
                count = await self._migrate_working_memory(db, working_file)
                stats["working_memory_migrated"] = count
                logger.info(f"工作记忆迁移完成: {count} 条")
            
            # 迁移长期记忆
            long_term_file = self.data_dir / "long_term_memory.json"
            if long_term_file.exists():
                count = await self._migrate_long_term_memory(db, long_term_file)
                stats["long_term_memory_migrated"] = count
                logger.info(f"长期记忆迁移完成: {count} 条")
            
            # 迁移即时记忆
            instant_file = self.data_dir / "instant_memory.json"
            if instant_file.exists():
                count = await self._migrate_instant_memory(db, instant_file)
                stats["instant_memory_migrated"] = count
                logger.info(f"即时记忆迁移完成: {count} 条")
            
            await db.commit()
        
        logger.info(f"数据迁移完成: {stats}")
        return stats
    
    async def _migrate_working_memory(
        self,
        db: AsyncSession,
        file_path: Path,
    ) -> int:
        """
        迁移工作记忆
        
        Args:
            db: 数据库会话
            file_path: JSON 文件路径
            
        Returns:
            迁移的记忆数量
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            items = data.get("items", [])
            count = 0
            
            for item in items:
                memory = Memory(
                    memory_type=MemoryType.WORKING,
                    content=item.get("content", ""),
                    importance=item.get("importance", 0.5),
                    access_count=item.get("access_count", 0),
                    tags=item.get("tags", []),
                    metadata=item.get("metadata", {}),
                    entities=item.get("entity_ids", []),
                    session_id=item.get("session_id"),
                    status="active",
                )
                
                # 解析时间
                if item.get("created_at"):
                    try:
                        memory.created_at = datetime.fromisoformat(item["created_at"])
                    except (ValueError, TypeError):
                        pass
                
                if item.get("last_accessed"):
                    try:
                        memory.last_accessed_at = datetime.fromisoformat(item["last_accessed"])
                    except (ValueError, TypeError):
                        pass
                
                db.add(memory)
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"迁移工作记忆失败: {e}")
            return 0
    
    async def _migrate_long_term_memory(
        self,
        db: AsyncSession,
        file_path: Path,
    ) -> int:
        """
        迁移长期记忆
        
        Args:
            db: 数据库会话
            file_path: JSON 文件路径
            
        Returns:
            迁移的记忆数量
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            memories = data.get("memories", [])
            count = 0
            
            for mem in memories:
                # 解析分类
                category = mem.get("category", "fact")
                if isinstance(category, dict):
                    category = category.get("value", "fact")
                
                memory = Memory(
                    memory_type=MemoryType.LONG_TERM,
                    content=mem.get("content", ""),
                    importance=mem.get("importance", 0.5),
                    access_count=mem.get("access_count", 0),
                    category=category,
                    keywords=mem.get("keywords", []),
                    tags=mem.get("tags", []),
                    metadata=mem.get("metadata", {}),
                    entities=mem.get("entities", []),
                    session_id=mem.get("session_id"),
                    is_consolidated=mem.get("status") == "consolidated",
                    status="active" if mem.get("status") in ["active", "consolidated"] else "forgotten",
                )
                
                # 解析时间
                if mem.get("created_at"):
                    try:
                        memory.created_at = datetime.fromisoformat(mem["created_at"])
                    except (ValueError, TypeError):
                        pass
                
                if mem.get("last_accessed"):
                    try:
                        memory.last_accessed_at = datetime.fromisoformat(mem["last_accessed"])
                    except (ValueError, TypeError):
                        pass
                
                db.add(memory)
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"迁移长期记忆失败: {e}")
            return 0
    
    async def _migrate_instant_memory(
        self,
        db: AsyncSession,
        file_path: Path,
    ) -> int:
        """
        迁移即时记忆
        
        Args:
            db: 数据库会话
            file_path: JSON 文件路径
            
        Returns:
            迁移的记忆数量
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            count = 0
            
            # 即时记忆按对话 ID 组织
            for conversation_id, conv_data in data.items():
                messages = conv_data.get("messages", [])
                
                for msg in messages:
                    memory = Memory(
                        memory_type=MemoryType.INSTANT,
                        content=f"[{msg.get('role', 'user')}] {msg.get('content', '')}",
                        importance=0.3,  # 即时记忆默认重要性较低
                        source_type="conversation",
                        conversation_id=conversation_id,
                        metadata=msg.get("metadata", {}),
                        status="active",
                    )
                    
                    # 解析时间
                    if msg.get("timestamp"):
                        try:
                            memory.created_at = datetime.fromisoformat(msg["timestamp"])
                        except (ValueError, TypeError):
                            pass
                    
                    # 设置过期时间（即时记忆默认 1 小时过期）
                    if memory.created_at:
                        from datetime import timedelta
                        memory.expires_at = memory.created_at + timedelta(hours=1)
                    
                    db.add(memory)
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"迁移即时记忆失败: {e}")
            return 0


async def main():
    """
    主函数
    """
    migrator = MemoryMigrator()
    stats = await migrator.migrate_all()
    print(f"迁移完成: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
