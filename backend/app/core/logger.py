"""
Nexus 日志配置模块
配置 Loguru 日志记录器
"""
import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logger() -> None:
    """
    配置日志记录器
    
    设置日志格式、输出目标和日志级别
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # 添加文件输出
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )
    
    logger.info(f"日志系统初始化完成，日志级别: {settings.LOG_LEVEL}")


# 初始化日志
setup_logger()
