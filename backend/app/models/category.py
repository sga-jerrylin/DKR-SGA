"""
分类相关数据模型
"""
from typing import List
from pydantic import BaseModel


class Category(BaseModel):
    """文档分类"""
    name: str
    description: str
    document_count: int


class CategoryInfo(BaseModel):
    """分类信息"""
    category: str
    confidence: float
    reasoning: str


class CategoryListResponse(BaseModel):
    """分类列表响应"""
    success: bool
    categories: List[Category]
    total: int

