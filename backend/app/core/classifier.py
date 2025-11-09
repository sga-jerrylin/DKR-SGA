"""
文档自动分类器
"""
from typing import Dict, Any, List
from pathlib import Path
from loguru import logger

from app.core.llm_client import DeepSeekLLMClient
from app.config import get_settings


class DocumentClassifier:
    """文档自动分类器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_client = DeepSeekLLMClient()
        self.default_categories = self.settings.get_categories_list()
    
    async def classify(
        self,
        title: str,
        summary_data: Dict[str, Any],
        categories: List[str] = None
    ) -> Dict[str, Any]:
        """
        自动分类文档
        
        Args:
            title: 文档标题
            summary_data: Summary 数据（包含 page_summaries）
            categories: 可选分类列表（默认使用配置中的分类）
        
        Returns:
            分类结果 {"category": str, "confidence": float, "reasoning": str}
        """
        if categories is None:
            categories = self.default_categories
        
        # Get first 5 pages summary (封面通常信息量少，需要看前几页)
        page_summaries = summary_data.get("page_summaries", [])
        if not page_summaries:
            logger.warning(f"文档 {title} 没有页面摘要，使用默认分类")
            return {
                "success": True,
                "category": "其他",
                "confidence": 0.5,
                "reasoning": "无页面摘要，使用默认分类"
            }

        # 取前 5 页的 Summary（如果不足 5 页则取全部）
        first_5_pages = page_summaries[:5]
        combined_summary = "\n\n---\n\n".join(first_5_pages)

        logger.info(f"使用前 {len(first_5_pages)} 页 Summary 进行分类")

        # Use LLM to classify
        result = self.llm_client.classify_document(
            title=title,
            first_pages_summary=combined_summary,
            categories=categories
        )
        
        logger.info(
            f"文档分类完成: {title} -> {result['category']} "
            f"(置信度: {result['confidence']:.2f})"
        )
        
        return result
    
    async def reclassify(
        self,
        doc_id: str,
        title: str,
        summary_data: Dict[str, Any],
        new_categories: List[str] = None
    ) -> Dict[str, Any]:
        """
        重新分类文档
        
        Args:
            doc_id: 文档 ID
            title: 文档标题
            summary_data: Summary 数据
            new_categories: 新的分类列表（可选）
        
        Returns:
            分类结果
        """
        logger.info(f"重新分类文档: {doc_id}")
        return await self.classify(title, summary_data, new_categories)
    
    def get_category_description(self, category: str) -> str:
        """
        获取分类描述
        
        Args:
            category: 分类名称
        
        Returns:
            分类描述
        """
        descriptions = {
            "财务类": "包含财务报表、审计报告、预算文件等财务相关文档",
            "制度类": "包含公司制度、规章制度、管理办法等规范性文档",
            "研究类": "包含研究报告、学术论文、技术文档等研究性文档",
            "其他": "不属于以上分类的其他文档"
        }
        return descriptions.get(category, "未知分类")

