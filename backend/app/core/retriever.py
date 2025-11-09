"""
DKR 4层检索器
Layer 0: Library Overview (图书馆概览)
Layer 1: Category Documents (分类文档)
Layer 2: Document Pages (文档页面)
Layer 3: Full OCR (完整 OCR)
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

# Add project root to path (to import visual_memvid)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from visual_memvid.visual_retriever import VisualMemvidRetriever
from visual_memvid.config import CONFIG

from app.core.library_manager import LibraryManager
from app.core.llm_client import DeepSeekLLMClient
from app.config import get_settings


class DKRRetriever:
    """DKR 4层检索器"""

    def __init__(self):
        self.settings = get_settings()
        self.library_manager = LibraryManager()
        self.llm_client = DeepSeekLLMClient()

        # Initialize OCR client for visual retrieval
        from visual_memvid.ocr_client import DeepSeekOCRClient
        self.ocr_client = DeepSeekOCRClient(endpoint=self.settings.ocr_api_url)
    
    async def retrieve(
        self,
        query: str,
        max_iterations: int = None
    ) -> Dict[str, Any]:
        """
        执行 4 层检索
        
        Args:
            query: 用户查询
            max_iterations: 最大迭代次数
        
        Returns:
            检索结果
        """
        if max_iterations is None:
            max_iterations = self.settings.agent_max_iterations
        
        steps = []
        current_layer = 0
        
        try:
            # Layer 0: Library Overview
            logger.info("Layer 0: 图书馆概览")
            category_summary = self.library_manager.get_category_summary()
            
            selected_category = await self._select_category(query, category_summary)
            steps.append({
                "step": 1,
                "action": "select_category",
                "description": f"选择分类: {selected_category}",
                "layer": "Library",
                "result": {"category": selected_category}
            })
            
            if not selected_category:
                return self._create_response(
                    success=False,
                    answer="无法确定相关分类",
                    steps=steps
                )
            
            # Layer 1: Category Documents
            logger.info(f"Layer 1: 分类文档 - {selected_category}")
            documents = self.library_manager.list_documents(category=selected_category)
            
            if not documents:
                return self._create_response(
                    success=False,
                    answer=f"分类 {selected_category} 中没有文档",
                    steps=steps
                )
            
            selected_docs = await self._select_documents(query, documents)
            steps.append({
                "step": 2,
                "action": "select_documents",
                "description": f"选择文档: {[d['doc_id'] for d in selected_docs]}",
                "layer": "Category",
                "result": {"documents": [d["doc_id"] for d in selected_docs]}
            })
            
            # Layer 2 & 3: Document Pages + Full OCR
            all_sources = []
            for doc in selected_docs:
                doc_id = doc["doc_id"]
                logger.info(f"Layer 2/3: 检索文档 - {doc_id}")
                
                # Use visual retriever for page-level search
                video_path = self.settings.videos_dir / f"{doc_id}.mp4"
                if not video_path.exists():
                    logger.warning(f"视频文件不存在: {video_path}")
                    continue
                
                # Retrieve from document
                doc_result = self.visual_retriever.retrieve(
                    knowledge_name=doc_id,
                    query=query,
                    top_k=5
                )
                
                if doc_result.get("success"):
                    sources = doc_result.get("sources", [])
                    for source in sources:
                        source["doc_id"] = doc_id
                        source["doc_title"] = doc["title"]
                    all_sources.extend(sources)
            
            steps.append({
                "step": 3,
                "action": "retrieve_pages",
                "description": f"检索到 {len(all_sources)} 个相关页面",
                "layer": "Document/Page",
                "result": {"source_count": len(all_sources)}
            })
            
            if not all_sources:
                return self._create_response(
                    success=False,
                    answer="未找到相关内容",
                    steps=steps
                )
            
            # Generate answer from sources
            answer = await self._generate_answer(query, all_sources)
            confidence = await self.llm_client.evaluate_confidence(
                query=query,
                answer=answer,
                sources=all_sources
            )
            
            steps.append({
                "step": 4,
                "action": "generate_answer",
                "description": "生成答案",
                "layer": "Answer",
                "result": {"confidence": confidence}
            })
            
            return self._create_response(
                success=True,
                answer=answer,
                sources=all_sources,
                confidence=confidence,
                steps=steps
            )
        
        except Exception as e:
            logger.error(f"检索失败: {e}", exc_info=True)
            return self._create_response(
                success=False,
                answer=None,
                error=str(e),
                steps=steps
            )

    async def _select_category(self, query: str, category_summary: str) -> Optional[str]:
        """
        Layer 0: 选择分类

        Args:
            query: 用户查询
            category_summary: 分类摘要

        Returns:
            选中的分类名称
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个文档检索助手。根据用户查询和文档库概览，"
                    "选择最相关的文档分类。\n"
                    "请只返回分类名称，不要有其他内容。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户查询: {query}\n\n"
                    f"{category_summary}\n\n"
                    f"请选择最相关的分类："
                )
            }
        ]

        result = await self.llm_client.chat(messages=messages, temperature=0.1)

        if result["success"]:
            category = result["content"].strip()
            logger.info(f"选择分类: {category}")
            return category
        else:
            logger.error(f"选择分类失败: {result['error']}")
            return None

    async def _select_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Layer 1: 选择文档

        Args:
            query: 用户查询
            documents: 文档列表
            top_k: 返回前 K 个文档

        Returns:
            选中的文档列表
        """
        if len(documents) <= top_k:
            return documents

        # Create document summary
        doc_summaries = []
        for doc in documents:
            doc_summaries.append(
                f"- {doc['title']} (ID: {doc['doc_id']}, "
                f"页数: {doc['metadata']['page_count']})"
            )

        doc_summary_text = "\n".join(doc_summaries)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个文档检索助手。根据用户查询和文档列表，"
                    f"选择最相关的 {top_k} 个文档。\n"
                    "请以 JSON 数组格式返回文档 ID，例如: [\"doc_id_1\", \"doc_id_2\"]"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户查询: {query}\n\n"
                    f"文档列表:\n{doc_summary_text}\n\n"
                    f"请选择最相关的 {top_k} 个文档 ID："
                )
            }
        ]

        result = await self.llm_client.chat(
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        if result["success"]:
            try:
                import json
                selected_ids = json.loads(result["content"])
                if isinstance(selected_ids, dict):
                    selected_ids = selected_ids.get("documents", [])

                selected_docs = [
                    doc for doc in documents if doc["doc_id"] in selected_ids
                ]
                logger.info(f"选择文档: {[d['doc_id'] for d in selected_docs]}")
                return selected_docs[:top_k]
            except Exception as e:
                logger.error(f"解析选择的文档失败: {e}")
                return documents[:top_k]
        else:
            logger.error(f"选择文档失败: {result['error']}")
            return documents[:top_k]

    async def _generate_answer(
        self,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        生成答案

        Args:
            query: 用户查询
            sources: 来源列表

        Returns:
            生成的答案
        """
        # Format sources
        sources_text = []
        for i, source in enumerate(sources, 1):
            sources_text.append(
                f"[来源 {i}] 文档: {source['doc_title']}, "
                f"页码: {source['page_number']}\n"
                f"内容: {source['content']}\n"
            )

        sources_context = "\n".join(sources_text)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的文档问答助手。根据提供的文档内容，"
                    "准确、简洁地回答用户的问题。\n"
                    "要求：\n"
                    "1. 答案必须基于提供的文档内容\n"
                    "2. 如果文档中没有相关信息，明确说明\n"
                    "3. 引用具体的文档和页码\n"
                    "4. 保持客观和准确"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户问题: {query}\n\n"
                    f"相关文档内容:\n{sources_context}\n\n"
                    f"请回答用户的问题："
                )
            }
        ]

        result = await self.llm_client.chat(messages=messages, temperature=0.3)

        if result["success"]:
            return result["content"]
        else:
            return "抱歉，生成答案时出现错误。"

    def _create_response(
        self,
        success: bool,
        answer: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.0,
        steps: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建响应"""
        return {
            "success": success,
            "answer": answer,
            "sources": sources or [],
            "confidence": confidence,
            "agent_steps": steps or [],
            "error": error
        }

