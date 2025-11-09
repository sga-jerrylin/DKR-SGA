"""
配置 API
"""
from typing import List
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.core.library_manager import LibraryManager
from app.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])

library_manager = LibraryManager()
settings = get_settings()


@router.get("/categories")
async def get_categories():
    """获取所有分类"""
    try:
        summary = library_manager.get_category_summary()
        return {
            "success": True,
            "categories": list(summary.keys())
        }
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categories")
async def add_category(category: str):
    """添加新分类"""
    try:
        # 验证分类名称
        if not category or len(category.strip()) == 0:
            raise HTTPException(status_code=400, detail="分类名称不能为空")
        
        summary = library_manager.get_category_summary()
        if category in summary:
            raise HTTPException(status_code=400, detail=f"分类 '{category}' 已存在")
        
        # 添加分类（通过添加空文档列表）
        library_manager.library_index["categories"][category] = {
            "document_count": 0,
            "documents": {}
        }
        library_manager._save_index()
        
        logger.info(f"新增分类: {category}")
        return {
            "success": True,
            "message": f"分类 '{category}' 已添加"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        summary = library_manager.get_category_summary()
        
        total_documents = sum(info["document_count"] for info in summary.values())
        total_categories = len(summary)
        
        return {
            "success": True,
            "stats": {
                "total_documents": total_documents,
                "total_categories": total_categories,
                "categories": summary
            }
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

