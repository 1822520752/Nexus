"""
Nexus API 路由初始化文件
注册所有 API 路由
"""
from fastapi import APIRouter

from app.api.endpoints import actions, chat, conversations, documents, memory, models, search

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["对话管理"],
)

api_router.include_router(
    models.router,
    prefix="/models",
    tags=["模型管理"],
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["对话交互"],
)

api_router.include_router(
    documents.router,
    tags=["文档管理"],
)

api_router.include_router(
    actions.router,
    prefix="/actions",
    tags=["动作执行"],
)

api_router.include_router(
    search.router,
    tags=["搜索服务"],
)

api_router.include_router(
    memory.router,
    prefix="/memory",
    tags=["记忆管理"],
)
