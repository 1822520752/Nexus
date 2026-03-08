"""
Nexus 数据库配置模块
配置 SQLAlchemy 异步数据库连接和 SQLite-vec 向量扩展
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logger import logger

# 确保数据目录存在
_db_path = settings.DATABASE_URL.split(":///")[1] if ":///" in settings.DATABASE_URL else "./data/nexus.db"
_data_dir = os.path.dirname(_db_path)
if _data_dir and not os.path.exists(_data_dir):
    os.makedirs(_data_dir, exist_ok=True)
    logger.info(f"创建数据目录: {_data_dir}")

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy 声明式基类
    
    所有数据库模型都应继承此类
    """
    pass


async def init_db() -> None:
    """
    初始化数据库
    
    创建所有表和索引，并加载 SQLite-vec 扩展
    """
    async with engine.begin() as conn:
        # 加载 SQLite-vec 扩展
        await _load_sqlite_vec_extension(conn)
        
        # 导入所有模型以确保它们被注册
        from app.models import (  # noqa: F401
            action,
            conversation,
            document,
            memory,
            message,
            model_config,
            user_config,
            vector,
        )
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")


async def _load_sqlite_vec_extension(conn) -> None:
    """
    加载 SQLite-vec 向量扩展
    
    Args:
        conn: 数据库连接
    """
    try:
        # 尝试加载 sqlite-vec 扩展
        # 注意：需要先安装 sqlite-vec
        # pip install sqlite-vss 或编译 sqlite-vec
        
        def load_extension(sync_conn):
            """同步加载扩展的回调函数"""
            try:
                # 尝试加载 sqlite-vec
                sync_conn.enable_load_extension(True)
                # 这里需要 sqlite-vec 的实际路径
                # 在 Windows 上可能是: sqlite_vec.dll
                # 在 Linux/macOS 上可能是: sqlite_vec.so / sqlite_vec.dylib
                import sqlite_vec
                
                sync_conn.load_extension(sqlite_vec.loadable_path())
                sync_conn.enable_load_extension(False)
                logger.info("SQLite-vec 扩展加载成功")
            except Exception as e:
                logger.warning(f"SQLite-vec 扩展加载失败（将使用备用方案）: {e}")
                sync_conn.enable_load_extension(False)
        
        await conn.run_sync(load_extension)
    except Exception as e:
        logger.warning(f"加载 SQLite-vec 扩展时出错: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    Yields:
        异步数据库会话实例
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的上下文管理器
    
    Yields:
        异步数据库会话实例
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
