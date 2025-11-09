"""
图书馆管理器 - 管理文档索引和分类
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from app.config import get_settings
from app.utils import load_json, save_json


class LibraryManager:
    """图书馆管理器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.index_path = self.settings.data_dir / "library_index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """确保索引文件存在"""
        if not self.index_path.exists():
            initial_index = {
                "version": "1.0",
                "categories": {},
                "total_documents": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            save_json(initial_index, self.index_path)
    
    def get_index(self) -> Dict[str, Any]:
        """获取完整索引"""
        return load_json(self.index_path)
    
    def add_document(
        self,
        doc_id: str,
        title: str,
        category: str,
        category_confidence: float,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        添加文档到索引
        
        Args:
            doc_id: 文档 ID
            title: 文档标题
            category: 分类
            category_confidence: 分类置信度
            metadata: 元数据
        
        Returns:
            是否成功
        """
        try:
            index = self.get_index()
            
            # Initialize category if not exists
            if category not in index["categories"]:
                index["categories"][category] = {
                    "name": category,
                    "documents": {},
                    "document_count": 0
                }
            
            # Add document to category
            index["categories"][category]["documents"][doc_id] = {
                "doc_id": doc_id,
                "title": title,
                "category_confidence": category_confidence,
                "metadata": metadata,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Update counts
            index["categories"][category]["document_count"] = len(
                index["categories"][category]["documents"]
            )
            index["total_documents"] = sum(
                cat["document_count"] for cat in index["categories"].values()
            )
            index["updated_at"] = datetime.now().isoformat()
            
            save_json(index, self.index_path)
            logger.info(f"文档已添加到索引: {doc_id} -> {category}")
            return True
        
        except Exception as e:
            logger.error(f"添加文档到索引失败: {e}")
            return False
    
    def remove_document(self, doc_id: str) -> bool:
        """
        从索引中移除文档
        
        Args:
            doc_id: 文档 ID
        
        Returns:
            是否成功
        """
        try:
            index = self.get_index()
            
            # Find and remove document
            for category_name, category_data in index["categories"].items():
                if doc_id in category_data["documents"]:
                    del category_data["documents"][doc_id]
                    category_data["document_count"] = len(category_data["documents"])
                    
                    # Remove empty category
                    if category_data["document_count"] == 0:
                        del index["categories"][category_name]
                    
                    break
            
            # Update total count
            index["total_documents"] = sum(
                cat["document_count"] for cat in index["categories"].values()
            )
            index["updated_at"] = datetime.now().isoformat()
            
            save_json(index, self.index_path)
            logger.info(f"文档已从索引移除: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"从索引移除文档失败: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档信息"""
        index = self.get_index()
        for category_data in index["categories"].values():
            if doc_id in category_data["documents"]:
                return category_data["documents"][doc_id]
        return None
    
    def list_documents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出文档

        Args:
            category: 分类过滤（可选）

        Returns:
            文档列表
        """
        index = self.get_index()
        documents = []

        if category:
            if category in index["categories"]:
                # 添加 category 字段到每个文档
                for doc in index["categories"][category]["documents"].values():
                    doc_with_category = doc.copy()
                    doc_with_category["category"] = category
                    documents.append(doc_with_category)
        else:
            for category_name, category_data in index["categories"].items():
                # 添加 category 字段到每个文档
                for doc in category_data["documents"].values():
                    doc_with_category = doc.copy()
                    doc_with_category["category"] = category_name
                    documents.append(doc_with_category)

        return documents
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有分类"""
        index = self.get_index()
        return [
            {
                "name": cat_name,
                "document_count": cat_data["document_count"]
            }
            for cat_name, cat_data in index["categories"].items()
        ]
    
    def get_category_summary(self) -> str:
        """
        获取分类摘要（用于 Layer 0 检索）
        
        Returns:
            分类摘要文本
        """
        index = self.get_index()
        summary_lines = [
            f"# 文档库概览",
            f"总文档数: {index['total_documents']}",
            f"",
            f"## 分类列表"
        ]
        
        for cat_name, cat_data in index["categories"].items():
            summary_lines.append(
                f"- **{cat_name}**: {cat_data['document_count']} 份文档"
            )
        
        return "\n".join(summary_lines)

