"""
文档处理器 - 封装 visual_memvid 的 PDF 编码和 Summary 生成功能
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

# Add project root to path (to import visual_memvid)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from visual_memvid.enhanced_encoder import EnhancedPDFEncoder
from visual_memvid.config import CONFIG

from app.config import get_settings


class DocumentProcessor:
    """文档处理器"""

    def __init__(self):
        self.settings = get_settings()

        # Initialize encoder with OCR client
        from visual_memvid.ocr_client import DeepSeekOCRClient

        # Initialize OCR client and check availability
        logger.info(f"🔧 初始化 OCR 客户端: {self.settings.ocr_api_url}")
        ocr_client = DeepSeekOCRClient(endpoint=self.settings.ocr_api_url)

        if ocr_client.is_available:
            logger.info("✅ OCR 客户端初始化成功，Summary 生成已启用")
            enable_summary = True
        else:
            logger.warning("⚠️ OCR 服务不可用，将禁用 Summary 生成")
            enable_summary = False

        self.encoder = EnhancedPDFEncoder(
            ocr_client=ocr_client,
            enable_summary=enable_summary,
            enable_doris=False
        )
    
    async def process_document(
        self,
        pdf_path: str,
        doc_id: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理文档：PDF → Video + Summary
        
        Args:
            pdf_path: PDF 文件路径
            doc_id: 文档 ID
            title: 文档标题（可选）
        
        Returns:
            处理结果字典
        """
        try:
            logger.info("=" * 80)
            logger.info(f"📄 开始处理文档")
            logger.info("=" * 80)
            logger.info(f"   PDF 路径: {pdf_path}")
            logger.info(f"   文档 ID: {doc_id}")
            logger.info(f"   输出目录: {self.settings.data_dir}")
            logger.info(f"   标题: {title or '(未提供)'}")

            start_time = datetime.now()

            # Process PDF to video + summary using encode_with_summary
            logger.info(f"🚀 调用编码器...")
            result = self.encoder.encode_with_summary(
                pdf_path=str(pdf_path),
                output_dir=str(self.settings.data_dir),
                doc_id=doc_id
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info("=" * 80)
            logger.info(f"✅ 文档处理完成")
            logger.info("=" * 80)
            logger.info(f"   文档 ID: {doc_id}")
            logger.info(f"   总耗时: {processing_time:.2f}s")
            logger.info(f"   总页数: {result['total_pages']}")
            logger.info(f"   Summary 数量: {len(result.get('summaries', []))}")

            # Calculate video file size if exists
            video_path_obj = Path(result["video_path"])
            video_size = video_path_obj.stat().st_size if video_path_obj.exists() else 0

            return {
                "success": True,
                "doc_id": result["doc_id"],
                "doc_name": result["doc_name"],
                "video_path": result["video_path"],
                "index_path": result["index_path"],
                "summary_path": result.get("summary_path"),
                "page_count": result["total_pages"],
                "video_size": video_size,
                "summaries": result.get("summaries", []),
                "summaries_count": len(result.get("summaries", [])),
                "processing_time": processing_time,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"处理文档失败: {pdf_path}, 错误: {e}", exc_info=True)
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    async def get_document_summary(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档 Summary
        
        Args:
            doc_id: 文档 ID
        
        Returns:
            Summary 字典或 None
        """
        try:
            summary_path = self.settings.summary_dir / f"{doc_id}.json"
            if not summary_path.exists():
                return None
            
            import json
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"读取 Summary 失败: {doc_id}, 错误: {e}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档及其相关文件
        
        Args:
            doc_id: 文档 ID
        
        Returns:
            是否成功
        """
        try:
            # Delete PDF file
            pdf_path = self.settings.documents_dir / f"{doc_id}.pdf"
            if pdf_path.exists():
                pdf_path.unlink()

            # Delete video file
            video_path = self.settings.videos_dir / f"{doc_id}.mp4"
            if video_path.exists():
                video_path.unlink()

            # Delete summary folder
            summary_dir = self.settings.summaries_dir / doc_id
            if summary_dir.exists():
                import shutil
                shutil.rmtree(summary_dir)

            # Delete index directory (BM25S 索引是目录，不是单个文件)
            index_path = self.settings.indexes_dir / f"{doc_id}_index"
            if index_path.exists():
                import shutil
                shutil.rmtree(index_path)

            # Delete cache
            cache_dir = self.settings.cache_dir / doc_id
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)

            logger.info(f"文档删除成功: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"删除文档失败: {doc_id}, 错误: {e}")
            return False

