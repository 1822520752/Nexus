"""
Nexus 后端应用配置模块
定义应用的全局配置和设置
"""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    
    从环境变量和 .env 文件加载配置
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # 项目基本信息
    PROJECT_NAME: str = "Nexus"
    PROJECT_DESCRIPTION: str = "本地AI智能中枢后端服务"
    VERSION: str = "0.1.0"
    
    # API 配置
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/nexus.db"
    
    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "tauri://localhost",
    ]
    
    # AI 模型配置
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # 向量数据库配置
    VECTOR_DIMENSION: int = 1536  # OpenAI embeddings 维度
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/nexus.log"


# 创建全局配置实例
settings = Settings()
