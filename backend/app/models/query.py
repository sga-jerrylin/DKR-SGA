"""
查询相关数据模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="自然语言查询")
    context: Optional[Dict[str, Any]] = Field(default=None, description="上下文信息")
    options: Optional[Dict[str, Any]] = Field(default=None, description="查询选项")


class AgentStep(BaseModel):
    """Agent 执行步骤"""
    step: int
    action: str
    description: str
    layer: Optional[str] = None  # Library, Category, Document, Page
    result: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


class SourceReference(BaseModel):
    """来源引用"""
    doc_id: str
    doc_title: str
    page_number: int
    content: str
    relevance_score: float


class QueryResponse(BaseModel):
    """查询响应"""
    success: bool
    answer: Optional[str] = None
    execution_steps: Optional[List[Dict[str, Any]]] = None
    processing_time: float
    error: Optional[str] = None


class AgentAskRequest(BaseModel):
    """外部 Agent 查询请求"""
    query: str
    context: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="查询选项: return_sources, return_agent_steps, max_results"
    )


class AgentAskResponse(BaseModel):
    """外部 Agent 查询响应"""
    success: bool
    answer: Optional[str] = None
    sources: Optional[List[SourceReference]] = None
    confidence: float
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None

