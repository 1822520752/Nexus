"""
Nexus 后端服务主入口文件
初始化 FastAPI 应用和路由配置
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时执行
    logger.info("正在启动 Nexus 后端服务...")
    await init_db()
    logger.info("数据库初始化完成")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭 Nexus 后端服务...")


def create_application() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例
    
    Returns:
        配置好的 FastAPI 应用实例
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


# 创建应用实例
app = create_application()


@app.get("/health", tags=["健康检查"])
async def health_check() -> dict:
    """
    健康检查端点
    
    Returns:
        服务状态信息
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
