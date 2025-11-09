"""
Visual Retriever

视觉检索器：支持自动查看前后页的类人检索
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

from .bm25s_index import BM25SIndex  # 使用新的高性能索引
from .ocr_client import DeepSeekOCRClient
from .ocr_cache import OCRCache
from .config import CONFIG

logger = logging.getLogger(__name__)


class VisualMemvidRetriever:
    """
    视觉检索器
    
    核心功能：
    1. 基于元数据的轻量级检索
    2. 自动查看前后页（类人阅读行为）
    3. DeepSeek OCR 实时理解
    4. 批量 OCR 优化
    """
    
    def __init__(
        self,
        video_path: str,
        index_path: str,
        ocr_client: Optional[DeepSeekOCRClient] = None,
        enable_cache: bool = True
    ):
        """
        初始化检索器

        Args:
            video_path: 视频文件路径
            index_path: 索引文件路径
            ocr_client: OCR 客户端（可选，默认自动创建）
            enable_cache: 是否启用 OCR 缓存（默认启用）
        """
        self.video_path = Path(video_path)
        self.index_path = Path(index_path)

        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        if not self.index_path.exists():
            raise FileNotFoundError(f"索引文件不存在: {index_path}")

        # 加载索引（使用 mmap 节省内存）
        self.index = BM25SIndex.load(str(index_path), mmap=True)
        self.total_pages = self.index.metadata["total_pages"]

        # 初始化 OCR 客户端
        self.ocr_client = ocr_client or DeepSeekOCRClient()

        # 初始化 OCR 缓存
        self.enable_cache = enable_cache
        if enable_cache:
            self.ocr_cache = OCRCache()
            logger.info(f"✅ OCR 缓存已启用")
        else:
            self.ocr_cache = None

        logger.info(f"✅ 检索器初始化完成: {self.total_pages} 页")
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        context_window: int = 1,
        use_batch_ocr: bool = True
    ) -> List[Dict]:
        """
        检索 + 自动查看前后页
        
        Args:
            query: 用户查询
            top_k: 返回最相关的 K 个核心结果
            context_window: 前后页窗口大小（1 = 前后各 1 页）
            use_batch_ocr: 是否使用批量 OCR（性能优化）
        
        Returns:
            List of results with page_type ('prev', 'core', 'next')
        """
        logger.info(f"🔍 检索查询: {query}")
        
        # Step 1: 定位核心页面
        core_frames = self.index.search(query, top_k)
        
        if not core_frames:
            logger.warning(f"未找到匹配的页面")
            return []
        
        logger.info(f"📌 核心页面: {[f+1 for f in core_frames]}")
        
        # Step 2: 扩展到前后页
        extended_frames = self._extend_with_context(core_frames, context_window)
        logger.info(f"📖 扩展后页面: {[(f+1, t) for f, t in extended_frames]}")
        
        # Step 3: OCR 理解
        if use_batch_ocr and len(extended_frames) > 1:
            results = self._batch_ocr(extended_frames, core_frames)
        else:
            results = self._sequential_ocr(extended_frames, core_frames)
        
        return results
    
    def _extend_with_context(
        self,
        core_frames: List[int],
        window: int
    ) -> List[Tuple[int, str]]:
        """
        扩展到前后页（类人行为）
        
        Args:
            core_frames: 核心帧号列表
            window: 窗口大小（前后各 window 页）
        
        Returns:
            List of (frame_num, page_type) tuples
            page_type: 'prev' | 'core' | 'next'
        """
        extended = []
        
        for frame_num in core_frames:
            # 前 window 页
            for i in range(window, 0, -1):
                prev_frame = frame_num - i
                if prev_frame >= 0:
                    extended.append((prev_frame, 'prev'))
            
            # 当前页（核心）
            extended.append((frame_num, 'core'))
            
            # 后 window 页
            for i in range(1, window + 1):
                next_frame = frame_num + i
                if next_frame < self.total_pages:
                    extended.append((next_frame, 'next'))
        
        # 去重并保持顺序
        seen = set()
        unique_extended = []
        for frame, page_type in extended:
            if frame not in seen:
                seen.add(frame)
                # 如果同一页既是 prev 又是 core，优先标记为 core
                existing = [i for i, (f, t) in enumerate(unique_extended) if f == frame]
                if existing:
                    if page_type == 'core':
                        unique_extended[existing[0]] = (frame, 'core')
                else:
                    unique_extended.append((frame, page_type))
        
        # 按帧号排序（模拟顺序翻页）
        unique_extended.sort(key=lambda x: x[0])
        
        return unique_extended
    
    def _extract_frame(self, frame_num: int) -> Optional[np.ndarray]:
        """
        从视频中提取单帧
        
        Args:
            frame_num: 帧号
        
        Returns:
            OpenCV 图片数组
        """
        cap = cv2.VideoCapture(str(self.video_path))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                return frame
            else:
                logger.error(f"❌ 提取帧失败: frame_num={frame_num}")
                return None
        finally:
            cap.release()
    
    def _batch_ocr(
        self,
        extended_frames: List[Tuple[int, str]],
        core_frames: List[int]
    ) -> List[Dict]:
        """
        批量 OCR（性能优化）

        利用 DeepSeek OCR 的批量接口 + 缓存
        """
        logger.info(f"🚀 批量 OCR: {len(extended_frames)} 页")

        # 1. 检查缓存，分离已缓存和未缓存的帧
        cached_results = []
        uncached_frames = []

        for frame_num, page_type in extended_frames:
            # 尝试从缓存获取
            if self.enable_cache:
                cached_content = self.ocr_cache.get(str(self.video_path), frame_num)
                if cached_content:
                    page_info = self.index.get_page_info(frame_num)
                    cached_results.append({
                        "page_num": frame_num + 1,
                        "frame_num": frame_num,
                        "page_type": page_type,
                        "is_core": frame_num in core_frames,
                        "content": cached_content,
                        "processing_time": 0,  # 缓存命中，无需处理时间
                        "success": True,
                        "metadata": page_info,
                        "from_cache": True
                    })
                    continue

            # 未缓存，需要 OCR
            uncached_frames.append((frame_num, page_type))

        logger.info(f"📦 缓存命中: {len(cached_results)} 页，需要 OCR: {len(uncached_frames)} 页")

        # 2. 对未缓存的帧进行批量 OCR
        uncached_results = []
        if uncached_frames:
            # 提取帧
            frames_data = []
            for frame_num, page_type in uncached_frames:
                frame_img = self._extract_frame(frame_num)
                if frame_img is not None:
                    frames_data.append((frame_num, page_type, frame_img))

            # 批量 OCR
            images = [img for _, _, img in frames_data]
            ocr_results = self.ocr_client.ocr_batch(images)

            # 组装结果并缓存
            for i, (frame_num, page_type, _) in enumerate(frames_data):
                page_info = self.index.get_page_info(frame_num)
                content = ocr_results[i].get("text", "")

                # 保存到缓存
                if self.enable_cache:
                    self.ocr_cache.set(str(self.video_path), frame_num, content)

                uncached_results.append({
                    "page_num": frame_num + 1,
                    "frame_num": frame_num,
                    "page_type": page_type,
                    "is_core": frame_num in core_frames,
                    "content": content,
                    "processing_time": ocr_results[i].get("processing_time", 0),
                    "success": ocr_results[i].get("success", False),
                    "metadata": page_info,
                    "from_cache": False
                })

        # 3. 合并结果（保持原始顺序）
        results = cached_results + uncached_results
        results.sort(key=lambda x: x["frame_num"])

        logger.info(f"✅ 批量 OCR 完成")
        return results
    
    def _sequential_ocr(
        self,
        extended_frames: List[Tuple[int, str]],
        core_frames: List[int]
    ) -> List[Dict]:
        """
        串行 OCR（降级方案）
        """
        logger.info(f"🔄 串行 OCR: {len(extended_frames)} 页")
        
        results = []
        for frame_num, page_type in extended_frames:
            # 提取帧
            frame_img = self._extract_frame(frame_num)
            if frame_img is None:
                continue
            
            # OCR
            ocr_result = self.ocr_client.ocr_image(frame_img)
            
            # 获取页面元数据
            page_info = self.index.get_page_info(frame_num)
            
            results.append({
                "page_num": frame_num + 1,
                "frame_num": frame_num,
                "page_type": page_type,
                "is_core": frame_num in core_frames,
                "content": ocr_result.get("text", ""),
                "processing_time": ocr_result.get("processing_time", 0),
                "success": ocr_result.get("success", False),
                "metadata": page_info,
            })
        
        logger.info(f"✅ 串行 OCR 完成")
        return results
    
    def get_page_content(self, page_num: int) -> Dict:
        """
        获取指定页面的内容
        
        Args:
            page_num: 页码（从 1 开始）
        
        Returns:
            页面内容和元数据
        """
        frame_num = page_num - 1
        
        if frame_num < 0 or frame_num >= self.total_pages:
            raise ValueError(f"页码超出范围: {page_num} (总页数: {self.total_pages})")
        
        # 提取帧
        frame_img = self._extract_frame(frame_num)
        
        # OCR
        ocr_result = self.ocr_client.ocr_image(frame_img)
        
        # 获取元数据
        page_info = self.index.get_page_info(frame_num)
        
        return {
            "page_num": page_num,
            "frame_num": frame_num,
            "content": ocr_result.get("text", ""),
            "processing_time": ocr_result.get("processing_time", 0),
            "success": ocr_result.get("success", False),
            "metadata": page_info,
        }

