"""
Lightweight Index

轻量级元数据索引，不使用 Embedding 和 FAISS
支持 BM25 算法进行高质量检索
"""

import json
import re
import math
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from collections import Counter, defaultdict
import logging

from .config import CONFIG

logger = logging.getLogger(__name__)


class LightweightIndex:
    """
    轻量级元数据索引
    
    特点：
    - 不使用 Embedding（节省计算和存储）
    - 基于关键词匹配和元数据检索
    - 支持目录结构、页码、特殊内容标记
    """
    
    def __init__(self):
        self.metadata = {
            "pages": [],  # 页面元数据列表
            "toc": {},    # 目录结构 {章节名: [页码列表]}
            "total_pages": 0,
        }
        self.min_keyword_length = CONFIG["index"]["min_keyword_length"]
        self.max_keywords = CONFIG["index"]["max_keywords_per_page"]

        # BM25 参数
        self.k1 = 1.5  # 词频饱和参数
        self.b = 0.75  # 文档长度归一化参数

        # BM25 统计信息（在索引构建完成后计算）
        self.idf = {}  # {term: idf_score}
        self.avgdl = 0  # 平均文档长度
    
    def add_page(
        self,
        page_num: int,
        frame_num: int,
        text_preview: str = "",
        title: str = "",
        chapter: str = "",
        **kwargs
    ):
        """
        添加页面元数据

        Args:
            page_num: 页码（从 1 开始）
            frame_num: 帧号（从 0 开始）
            text_preview: 文本预览（用于关键词提取）
            title: 页面标题
            chapter: 所属章节

        Note:
            移除了 has_table/has_formula/has_image 字段
            这些信息应该从 OCR Summary 中获取，而不是在上传时检测
        """
        # 提取关键词
        keywords = self._extract_keywords(text_preview)

        page_meta = {
            "page_num": page_num,
            "frame_num": frame_num,
            "title": title,
            "chapter": chapter,
            "keywords": keywords,
            **kwargs
        }
        
        self.metadata["pages"].append(page_meta)
        self.metadata["total_pages"] = len(self.metadata["pages"])
        
        # 更新目录
        if chapter:
            if chapter not in self.metadata["toc"]:
                self.metadata["toc"][chapter] = []
            self.metadata["toc"][chapter].append(page_num)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        简单关键词提取（支持中英文）

        提取：
        - 日期 (2024-01-01, 2024/01/01)
        - 数字 ($1.2M, 15%, 1000)
        - 中文词（2个字以上）
        - 英文词（长度 > min_keyword_length）
        """
        keywords = []

        # 1. 提取日期
        dates = re.findall(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', text)
        keywords.extend(dates)

        # 2. 提取数字（金额、百分比）
        numbers = re.findall(r'\$?\d+\.?\d*[%MKB]?', text)
        keywords.extend(numbers[:5])  # 最多 5 个数字

        # 3. 提取季度标识
        quarters = re.findall(r'Q[1-4]|第[一二三四]季度', text)
        keywords.extend(quarters)

        # 4. 提取中文词（2个字以上）
        chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
        keywords.extend(chinese_words[:15])  # 最多 15 个中文词

        # 5. 提取英文词
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        common_english = [
            w for w in english_words
            if len(w) >= self.min_keyword_length
        ]
        keywords.extend(common_english[:10])  # 最多 10 个英文词

        # 去重并限制数量
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:self.max_keywords]

    def build_bm25_index(self):
        """
        构建 BM25 索引（计算 IDF 和平均文档长度）

        应该在所有页面添加完成后调用
        """
        if not self.metadata["pages"]:
            logger.warning("没有页面数据，无法构建 BM25 索引")
            return

        # 计算文档频率 (DF)
        df = defaultdict(int)  # {term: 出现该词的文档数}
        total_length = 0

        for page in self.metadata["pages"]:
            # 统计每个页面的关键词（去重）
            unique_terms = set(page["keywords"])
            for term in unique_terms:
                df[term] += 1

            # 累计文档长度
            total_length += len(page["keywords"])

        # 计算平均文档长度
        self.avgdl = total_length / len(self.metadata["pages"])

        # 计算 IDF
        N = len(self.metadata["pages"])
        for term, doc_freq in df.items():
            # IDF = log((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

        logger.info(f"✅ BM25 索引构建完成: {len(self.idf)} 个词, 平均文档长度 {self.avgdl:.2f}")
    
    def search(self, query: str, top_k: int = 3, use_bm25: bool = True) -> List[int]:
        """
        基于 BM25 算法的高质量检索

        Args:
            query: 用户查询
            top_k: 返回最相关的 K 个结果
            use_bm25: 是否使用 BM25 算法（默认 True）

        Returns:
            List of frame_num (帧号列表)
        """
        if use_bm25 and self.idf:
            return self._search_bm25(query, top_k)
        else:
            return self._search_simple(query, top_k)

    def _search_bm25(self, query: str, top_k: int) -> List[int]:
        """
        BM25 算法检索

        BM25 公式：
        score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))
        """
        # 提取查询词
        query_terms = self._extract_keywords(query)

        if not query_terms:
            logger.warning(f"查询中没有有效关键词: {query}")
            return []

        scores = []

        for page in self.metadata["pages"]:
            bm25_score = 0

            # 计算文档长度
            doc_length = len(page["keywords"])

            # 统计查询词在文档中的词频
            term_freq = Counter(page["keywords"])

            # 计算 BM25 得分
            for term in query_terms:
                if term in term_freq:
                    # 词频
                    tf = term_freq[term]

                    # IDF（如果词不在索引中，使用默认值）
                    idf = self.idf.get(term, 0)

                    # BM25 公式
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avgdl)
                    bm25_score += idf * (numerator / denominator)

            # 额外加权（保留原有的特殊匹配逻辑）
            bonus_score = 0

            # 标题匹配（权重 5）
            if page.get("title"):
                title_terms = self._extract_keywords(page["title"])
                for term in query_terms:
                    if term in title_terms:
                        bonus_score += 5

            # 章节匹配（权重 3）
            if page.get("chapter"):
                chapter_terms = self._extract_keywords(page["chapter"])
                for term in query_terms:
                    if term in chapter_terms:
                        bonus_score += 3

            # 页码直接匹配（权重 10）
            page_num_match = re.search(r'第?\s*(\d+)\s*页', query)
            if page_num_match:
                target_page = int(page_num_match.group(1))
                if page["page_num"] == target_page:
                    bonus_score += 10

            # 总分 = BM25 得分 + 额外加权
            total_score = bm25_score + bonus_score

            scores.append((page["frame_num"], total_score, page["page_num"]))

        # 排序并返回 top_k
        scores.sort(key=lambda x: x[1], reverse=True)

        # 过滤掉得分为 0 的结果
        valid_scores = [(frame_num, score, page_num) for frame_num, score, page_num in scores if score > 0]

        if not valid_scores:
            logger.warning(f"未找到匹配的页面: {query}")
            return []

        # 返回帧号列表
        result_frames = [frame_num for frame_num, _, _ in valid_scores[:top_k]]

        logger.info(f"BM25 检索到 {len(result_frames)} 个相关页面: {result_frames}")
        return result_frames

    def _search_simple(self, query: str, top_k: int) -> List[int]:
        """
        简单关键词匹配检索（降级方案）
        """
        query_lower = query.lower()
        scores = []

        for page in self.metadata["pages"]:
            score = 0

            # 1. 关键词匹配（权重 2）
            for keyword in page["keywords"]:
                if keyword.lower() in query_lower:
                    score += 2

            # 2. 标题匹配（权重 5）
            if page.get("title") and page["title"].lower() in query_lower:
                score += 5

            # 3. 章节匹配（权重 3）
            if page.get("chapter") and page["chapter"].lower() in query_lower:
                score += 3

            # 4. 页码直接匹配（权重 10）
            page_num_match = re.search(r'第?\s*(\d+)\s*页', query)
            if page_num_match:
                target_page = int(page_num_match.group(1))
                if page["page_num"] == target_page:
                    score += 10

            scores.append((page["frame_num"], score, page["page_num"]))

        # 排序并返回 top_k
        scores.sort(key=lambda x: x[1], reverse=True)

        # 过滤掉得分为 0 的结果
        valid_scores = [(frame_num, score, page_num) for frame_num, score, page_num in scores if score > 0]

        if not valid_scores:
            logger.warning(f"未找到匹配的页面: {query}")
            return []

        # 返回帧号列表
        result_frames = [frame_num for frame_num, _, _ in valid_scores[:top_k]]

        logger.info(f"简单检索到 {len(result_frames)} 个相关页面: {result_frames}")
        return result_frames
    
    def get_page_info(self, frame_num: int) -> Optional[Dict]:
        """获取页面元数据"""
        for page in self.metadata["pages"]:
            if page["frame_num"] == frame_num:
                return page
        return None
    
    def save(self, output_path: str):
        """保存索引到 JSON 文件（包含 BM25 索引）"""
        # 构建 BM25 索引（如果还没有）
        if not self.idf:
            self.build_bm25_index()

        # 保存完整索引数据
        index_data = {
            "metadata": self.metadata,
            "bm25": {
                "idf": self.idf,
                "avgdl": self.avgdl,
                "k1": self.k1,
                "b": self.b
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 索引已保存: {output_path} (BM25 索引: {len(self.idf)} 个词)")

    @classmethod
    def load(cls, index_path: str) -> 'LightweightIndex':
        """从 JSON 文件加载索引（包含 BM25 索引）"""
        index = cls()

        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 兼容旧格式（没有 BM25 索引）
        if "metadata" in data:
            index.metadata = data["metadata"]

            # 加载 BM25 索引
            if "bm25" in data:
                bm25_data = data["bm25"]
                index.idf = bm25_data.get("idf", {})
                index.avgdl = bm25_data.get("avgdl", 0)
                index.k1 = bm25_data.get("k1", 1.5)
                index.b = bm25_data.get("b", 0.75)
                logger.info(f"✅ 索引已加载: {index_path} ({index.metadata['total_pages']} 页, BM25: {len(index.idf)} 个词)")
            else:
                # 旧格式，重新构建 BM25 索引
                logger.warning(f"旧格式索引，重新构建 BM25 索引")
                index.build_bm25_index()
                logger.info(f"✅ 索引已加载: {index_path} ({index.metadata['total_pages']} 页)")
        else:
            # 非常旧的格式
            index.metadata = data
            index.build_bm25_index()
            logger.info(f"✅ 索引已加载（旧格式）: {index_path} ({index.metadata['total_pages']} 页)")

        return index
    
    def get_chapter_pages(self, chapter: str) -> List[int]:
        """获取章节的所有页码"""
        return self.metadata["toc"].get(chapter, [])
    
    def get_toc(self) -> Dict[str, List[int]]:
        """获取完整目录"""
        return self.metadata["toc"]

