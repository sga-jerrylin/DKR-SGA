"""
文档相关数据模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """文档元数据"""
    filename: str
    file_size: int
    page_count: int
    upload_time: datetime
    video_path: str
    video_size: int
    compression_ratio: float


class DocumentSummary(BaseModel):
    """文档摘要"""
    doc_id: str
    title: str
    category: str
    category_confidence: float
    total_pages: int
    page_summaries: List[str]
    keywords: List[str]
    created_at: datetime
    updated_at: datetime


class Document(BaseModel):
    """文档完整信息"""
    doc_id: str
    title: str
    category: str
    file_path: Optional[str] = None
    video_path: Optional[str] = None
    summary_path: Optional[str] = None
    page_count: int = 0
    keywords: List[str] = []
    upload_time: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    doc_id: Optional[str] = None
    category: Optional[str] = None
    message: str
    error: Optional[str] = None


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    success: bool
    total: int
    documents: List[Document]
    categories: Dict[str, int]  # category -> count

