"""
外部 Agent API - 供其他 Agent 调用
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header
from loguru import logger

from app.agent.dkr_agent import DKRAgent
from app.core.library_manager import LibraryManager

router = APIRouter(prefix="/agent", tags=["agent"])

# 全局实例
agent = DKRAgent()
library_manager = LibraryManager()


@router.post("/ask")
async def agent_ask(
    query: str,
    options: Optional[Dict[str, Any]] = None,
    x_api_key: Optional[str] = Header(None)
):
    """
    Agent 查询接口（供外部 Agent 调用）
    
    Args:
        query: 自然语言查询
        options: 可选参数（如 thread_id）
        x_api_key: API Key（可选，用于鉴权）
    
    Returns:
        查询结果
    """
    try:
        logger.info(f"[External Agent] 收到查询: {query}")
        
        # TODO: API Key 验证（如果需要）
        # if x_api_key != expected_key:
        #     raise HTTPException(status_code=401, detail="Invalid API Key")
        
        thread_id = options.get("thread_id", "default") if options else "default"
        
        result = await agent.ask(query=query, thread_id=thread_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/overview")
async def get_library_overview():
    """
    获取文档库概览（供外部 Agent 调用）
    
    Returns:
        文档库的分类和文档概览
    """
    try:
        summary = library_manager.get_category_summary()
        return {
            "success": True,
            "library_overview": summary
        }
    except Exception as e:
        logger.error(f"获取文档库概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/categories")
async def get_categories():
    """
    获取所有分类（供外部 Agent 调用）
    
    Returns:
        分类列表
    """
    try:
        summary = library_manager.get_category_summary()
        categories = [
            {
                "name": category,
                "document_count": info["document_count"]
            }
            for category, info in summary.items()
        ]
        return {
            "success": True,
            "categories": categories
        }
    except Exception as e:
        logger.error(f"获取分类列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/documents/{category}")
async def get_documents_in_category(category: str):
    """
    获取指定分类下的文档（供外部 Agent 调用）
    
    Args:
        category: 分类名称
    
    Returns:
        文档列表
    """
    try:
        documents = library_manager.list_documents(category=category)
        return {
            "success": True,
            "category": category,
            "documents": documents
        }
    except Exception as e:
        logger.error(f"获取分类文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

