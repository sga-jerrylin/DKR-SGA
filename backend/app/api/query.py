"""
查询 API - Agent-First 自然语言查询
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.query import QueryRequest, QueryResponse
from app.api.agent import get_agent

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    自然语言查询（Agent-First）
    
    用户只需提供自然语言问题，Agent 会：
    1. 理解查询意图
    2. 自动选择分类
    3. 自动选择文档
    4. 自动定位页面
    5. 调用 DeepSeek OCR 理解内容
    6. 生成答案
    
    Args:
        request: 查询请求（只需要 query 字段）
    
    Returns:
        查询结果（答案 + 来源 + 置信度）
    """
    try:
        logger.info(f"收到查询请求: {request.query}")

        # 调用 LangGraph Agent（自主循环，无状态）
        agent = get_agent()  # 获取 Agent 实例
        result = await agent.ask(query=request.query)

        if not result["success"]:
            error_msg = result.get("error", "查询失败")
            logger.error(f"Agent 返回失败: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        logger.info(f"查询成功，耗时 {result['processing_time']:.2f}s")

        return QueryResponse(
            success=True,
            answer=result["answer"],
            execution_steps=result.get("execution_steps", []),
            processing_time=result["processing_time"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

