"""
API 路由
"""
from fastapi import APIRouter

from .documents import router as documents_router
from .query import router as query_router
from .agent import router as agent_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(query_router, prefix="/query", tags=["query"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])

__all__ = ["api_router"]

