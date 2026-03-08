"""
Nexus 数据库初始化脚本
创建数据库表结构并插入初始数据
"""
import asyncio
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import async_session_maker, engine, init_db
from app.core.logger import logger
from app.models import (
    ActionHistory,
    ActionType,
    Conversation,
    Document,
    DocumentChunk,
    Memory,
    MemoryType,
    Message,
    ModelConfig,
    UserConfig,
    Vector,
)


async def create_default_model_configs(session) -> None:
    """
    创建默认的模型配置
    
    Args:
        session: 数据库会话
    """
    # 检查是否已存在模型配置
    from sqlalchemy import select
    
    result = await session.execute(select(ModelConfig))
    existing_models = result.scalars().all()
    
    if existing_models:
        logger.info("模型配置已存在，跳过初始化")
        return
    
    # 创建默认模型配置
    default_models = [
        ModelConfig(
            name="GPT-3.5 Turbo",
            provider="openai",
            model_type="chat",
            is_default=True,
            is_active=True,
            max_tokens=4096,
            temperature=0.7,
            context_window=16384,
            config='{"model": "gpt-3.5-turbo"}',
        ),
        ModelConfig(
            name="GPT-4",
            provider="openai",
            model_type="chat",
            is_default=False,
            is_active=True,
            max_tokens=8192,
            temperature=0.7,
            context_window=8192,
            config='{"model": "gpt-4"}',
        ),
        ModelConfig(
            name="DeepSeek Chat",
            provider="deepseek",
            model_type="chat",
            is_default=False,
            is_active=True,
            max_tokens=4096,
            temperature=0.7,
            context_window=16384,
            base_url="https://api.deepseek.com/v1",
            config='{"model": "deepseek-chat"}',
        ),
        ModelConfig(
            name="Ollama Llama 2",
            provider="ollama",
            model_type="chat",
            is_default=False,
            is_active=True,
            max_tokens=4096,
            temperature=0.7,
            context_window=4096,
            base_url="http://localhost:11434",
            config='{"model": "llama2"}',
        ),
    ]
    
    session.add_all(default_models)
    await session.commit()
    logger.info(f"已创建 {len(default_models)} 个默认模型配置")


async def create_default_user_configs(session) -> None:
    """
    创建默认的用户配置
    
    Args:
        session: 数据库会话
    """
    from sqlalchemy import select
    
    result = await session.execute(select(UserConfig))
    existing_configs = result.scalars().all()
    
    if existing_configs:
        logger.info("用户配置已存在，跳过初始化")
        return
    
    # 创建默认用户配置
    default_configs = [
        UserConfig(
            key="appearance",
            value='{"theme": "system", "language": "zh-CN", "fontSize": 14}',
            description="外观设置",
        ),
        UserConfig(
            key="chat",
            value='{"streamResponse": true, "showTokenCount": true, "autoSave": true}',
            description="聊天设置",
        ),
        UserConfig(
            key="memory",
            value='{"enabled": true, "maxInstantMemory": 10, "maxWorkingMemory": 100, "maxLongTermMemory": 1000}',
            description="记忆设置",
        ),
        UserConfig(
            key="document",
            value='{"chunkSize": 500, "chunkOverlap": 50, "supportedFormats": ["pdf", "md", "txt", "docx"]}',
            description="文档设置",
        ),
    ]
    
    session.add_all(default_configs)
    await session.commit()
    logger.info(f"已创建 {len(default_configs)} 个默认用户配置")


async def init_database() -> None:
    """
    初始化数据库
    
    创建表结构并插入初始数据
    """
    logger.info("开始初始化数据库...")
    
    # 初始化数据库表
    await init_db()
    
    # 创建初始数据
    async with async_session_maker() as session:
        try:
            # 创建默认模型配置
            await create_default_model_configs(session)
            
            # 创建默认用户配置
            await create_default_user_configs(session)
            
            logger.info("数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            await session.rollback()
            raise


async def reset_database() -> None:
    """
    重置数据库
    
    删除所有表并重新创建
    """
    logger.warning("正在重置数据库...")
    
    # 删除所有表
    async with engine.begin() as conn:
        from app.core.database import Base
        
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("已删除所有数据库表")
    
    # 重新初始化
    await init_database()


def main() -> None:
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Nexus 数据库初始化脚本")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="重置数据库（删除所有数据并重新创建）",
    )
    args = parser.parse_args()
    
    if args.reset:
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database())


if __name__ == "__main__":
    main()
