"""
Visual-Memvid: 视觉原生 RAG

基于 DeepSeek OCR + Memvid 的革命性文档检索系统
"""

from .pdf_encoder import VisualMemvidEncoder
from .lightweight_index import LightweightIndex  # 保留兼容性
from .bm25s_index import BM25SIndex  # 新的高性能索引
from .ocr_client import DeepSeekOCRClient
from .ocr_cache import OCRCache
from .visual_retriever import VisualMemvidRetriever
# from .doris_client import DorisClient  # Optional Doris integration
from .enhanced_encoder import EnhancedPDFEncoder
# from .doris_retriever import DorisProgressiveRetriever  # Optional Doris integration
from .config import CONFIG

__version__ = "0.1.0"
__all__ = [
    "VisualMemvidEncoder",
    "LightweightIndex",  # 保留兼容性
    "BM25SIndex",  # 新的高性能索引
    "DeepSeekOCRClient",
    "OCRCache",
    "VisualMemvidRetriever",
    # "DorisClient",
    "EnhancedPDFEncoder",
    # "DorisProgressiveRetriever",
    "CONFIG",
]

