"""
DKR 1.0 - Deep Knowledge Retrieval (Agent-First)
FastAPI 主应用入口
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Import routers
from app.api import documents, query, agent
from app.api import config as config_api

# Configure logger
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "./logs/dkr.log")
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

logger.add(
    log_file,
    rotation="500 MB",
    retention="10 days",
    level=log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 DKR 1.0 启动中...")

    # Initialize data directories - 使用统一的目录结构
    from app.config import get_settings
    settings = get_settings()

    directories = [
        settings.data_dir,
        settings.documents_dir,
        settings.videos_dir,
        settings.summaries_dir,
        settings.indexes_dir,
        settings.temp_dir,
        settings.cache_dir,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    logger.info(f"✅ 数据目录初始化完成: {settings.data_dir}")

    # Initialize library index if not exists
    library_index_path = settings.data_dir / "library_index.json"
    if not library_index_path.exists():
        import json
        library_index = {
            "version": "1.0",
            "categories": {},
            "total_documents": 0,
            "created_at": None,
            "updated_at": None
        }
        with open(library_index_path, "w", encoding="utf-8") as f:
            json.dump(library_index, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 创建图书馆索引: {library_index_path}")
    
    logger.info("✅ DKR 1.0 启动完成！")
    
    yield
    
    logger.info("👋 DKR 1.0 关闭中...")


# Create FastAPI app
app = FastAPI(
    title="DKR 1.0 - Deep Knowledge Retrieval",
    description="基于 Claude Agent SDK + DeepSeek OCR 的智能文档检索系统",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
from app.config import get_settings
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "DKR 1.0",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "DKR 1.0 - Deep Knowledge Retrieval (Agent-First)",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(agent.router)
app.include_router(config_api.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    reload = os.getenv("BACKEND_RELOAD", "true").lower() == "true"
    
    logger.info(f"🚀 启动服务: http://{host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower()
    )

