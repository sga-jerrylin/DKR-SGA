"""
BM25S Index

使用 bm25s 库实现的高性能 BM25 索引
- 100-500x 速度提升（相比 rank-bm25）
- 支持中文分词（jieba）
- 内存高效（支持 mmap）
"""

import json
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

import bm25s
import jieba
from bm25s.tokenization import Tokenizer

from .config import CONFIG

logger = logging.getLogger(__name__)


class BM25SIndex:
    """
    基于 bm25s 的高性能索引
    
    特点：
    - 使用 bm25s 库（100-500x 速度提升）
    - 支持中文分词（jieba）
    - 内存高效（支持 mmap）
    """
    
    def __init__(self):
        self.metadata = {
            "pages": [],  # 页面元数据列表
            "toc": {},    # 目录结构 {章节名: [页码列表]}
            "total_pages": 0,
        }
        
        # BM25S 检索器
        self.retriever = None
        
        # 中文停用词
        self.stopwords = [
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
            "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
            "自己", "这", "那", "里", "就是", "可以", "这个", "什么", "他", "她", "它"
        ]
        
        # Tokenizer（使用 jieba 分词）
        self.tokenizer = Tokenizer(
            stemmer=None,
            stopwords=self.stopwords,
            splitter=self._jieba_tokenize
        )
    
    def _jieba_tokenize(self, text: str) -> List[str]:
        """使用 jieba 分词"""
        # jieba 分词
        tokens = list(jieba.cut(text))
        
        # 过滤空白和单字符（除了数字）
        tokens = [
            t.strip() for t in tokens 
            if t.strip() and (len(t.strip()) > 1 or t.strip().isdigit())
        ]
        
        return tokens
    
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
            text_preview: 文本预览（用于索引）
            title: 页面标题
            chapter: 所属章节
        """
        page_meta = {
            "page_num": page_num,
            "frame_num": frame_num,
            "title": title,
            "chapter": chapter,
            "text": text_preview,  # 保存原始文本用于索引
            **kwargs
        }
        
        self.metadata["pages"].append(page_meta)
        self.metadata["total_pages"] = len(self.metadata["pages"])
        
        # 更新目录
        if chapter:
            if chapter not in self.metadata["toc"]:
                self.metadata["toc"][chapter] = []
            self.metadata["toc"][chapter].append(page_num)
    
    def build_index(self):
        """
        构建 BM25S 索引

        应该在所有页面添加完成后调用
        """
        if not self.metadata["pages"]:
            logger.warning("没有页面数据，无法构建索引")
            return

        # 准备文档语料库
        corpus = [page["text"] for page in self.metadata["pages"]]

        # 分词（返回 token 字符串列表，而不是 Tokenized 对象）
        logger.info(f"开始分词 {len(corpus)} 个文档...")
        corpus_tokens = self.tokenizer.tokenize(
            corpus,
            update_vocab=True,
            return_as="string"  # ← 返回字符串列表，而不是 Tokenized 对象
        )

        # 创建 BM25 检索器（使用 Lucene 变体）
        self.retriever = bm25s.BM25(method="lucene")

        # 构建索引
        logger.info(f"开始构建 BM25S 索引...")
        self.retriever.index(corpus_tokens)

        vocab_size = len(self.tokenizer.get_vocab_dict())
        logger.info(f"✅ BM25S 索引构建完成: {len(corpus)} 个文档, 词汇表大小 {vocab_size}")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        基于 BM25S 的高性能检索

        Args:
            query: 用户查询
            top_k: 返回最相关的 K 个结果

        Returns:
            List of dict with frame_num, page_num, score, relevance_level
            Example: [
                {"frame_num": 5, "page_num": 6, "score": 12.34, "relevance_level": "高"},
                {"frame_num": 2, "page_num": 3, "score": 8.56, "relevance_level": "中"},
                ...
            ]
        """
        if self.retriever is None:
            logger.error("索引未构建，请先调用 build_index()")
            return []

        # 日志：开始检索
        logger.info("=" * 80)
        logger.info(f"【BM25S 检索开始】")
        logger.info(f"查询: {query}")
        logger.info(f"Top-K: {top_k}")

        # 分词查询
        query_tokens = self.tokenizer.tokenize([query], update_vocab=False)

        # 日志：分词结果
        if isinstance(query_tokens, list) and len(query_tokens) > 0:
            tokens_str = query_tokens[0] if isinstance(query_tokens[0], list) else query_tokens
            logger.info(f"分词结果: {tokens_str}")
            logger.info(f"分词数量: {len(tokens_str) if isinstance(tokens_str, list) else 'N/A'}")

        # 检索
        results, scores = self.retriever.retrieve(query_tokens, k=top_k)

        # results 是 (n_queries, k) 的数组，包含文档索引
        # scores 是 (n_queries, k) 的数组，包含得分

        if results.shape[1] == 0:
            logger.warning(f"未找到匹配的页面: {query}")
            logger.info("=" * 80)
            return []

        # 获取第一个查询的结果（我们只有一个查询）
        doc_indices = results[0]
        doc_scores = scores[0]

        # 过滤掉得分为 0 的结果
        valid_results = [
            (int(doc_idx), float(score))
            for doc_idx, score in zip(doc_indices, doc_scores)
            if score > 0
        ]

        if not valid_results:
            logger.warning(f"未找到匹配的页面: {query}")
            logger.info("=" * 80)
            return []

        # 计算相关性等级（基于分数分布）
        scores_only = [score for _, score in valid_results]
        max_score = max(scores_only) if scores_only else 1.0

        # 日志：检索结果详情
        logger.info(f"\n【检索结果】找到 {len(valid_results)} 个相关页面:")

        result_list = []
        for rank, (doc_idx, score) in enumerate(valid_results, 1):
            page_info = self.metadata["pages"][doc_idx]
            frame_num = page_info["frame_num"]
            page_num = page_info["page_num"]
            title = page_info.get("title", "")

            # 计算相关性等级
            score_ratio = score / max_score if max_score > 0 else 0
            if score_ratio >= 0.7:
                relevance_level = "高"
            elif score_ratio >= 0.4:
                relevance_level = "中"
            else:
                relevance_level = "低"

            logger.info(f"  {rank}. 页面 {page_num} (frame {frame_num}) | 得分: {score:.4f} ({score_ratio:.1%}) | 相关性: {relevance_level} | 标题: {title}")

            result_list.append({
                "frame_num": frame_num,
                "page_num": page_num,
                "score": float(score),
                "score_ratio": float(score_ratio),
                "relevance_level": relevance_level,
                "rank": rank
            })

        logger.info(f"\n返回 {len(result_list)} 个结果（包含分数和相关性等级）")
        logger.info("=" * 80)
        return result_list

    def get_page_info(self, frame_num: int) -> Optional[Dict]:
        """获取页面元数据"""
        for page in self.metadata["pages"]:
            if page["frame_num"] == frame_num:
                return page
        return None

    def save(self, output_dir: str):
        """
        保存索引到目录

        Args:
            output_dir: 输出目录路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # 保存元数据
            logger.info(f"保存元数据到: {output_path / 'metadata.json'}")
            metadata_file = output_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 元数据已保存")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
            raise

        try:
            # 保存 BM25S 索引
            if self.retriever is not None:
                logger.info(f"保存 BM25S 索引到: {output_path / 'bm25s_index'}")
                self.retriever.save(str(output_path / "bm25s_index"))
                logger.info(f"✅ BM25S 索引已保存")
        except Exception as e:
            logger.error(f"保存 BM25S 索引失败: {e}")
            raise

        try:
            # 保存 Tokenizer 词汇表和停用词
            logger.info(f"保存 Tokenizer 词汇表...")
            # save_vocab 和 save_stopwords 需要传入目录路径
            self.tokenizer.save_vocab(str(output_path))
            logger.info(f"✅ Tokenizer 词汇表已保存")
        except Exception as e:
            logger.error(f"保存 Tokenizer 词汇表失败: {e}", exc_info=True)
            raise

        try:
            logger.info(f"保存停用词...")
            self.tokenizer.save_stopwords(str(output_path))
            logger.info(f"✅ 停用词已保存")
        except Exception as e:
            logger.error(f"保存停用词失败: {e}", exc_info=True)
            raise

        logger.info(f"✅ 索引保存完成: {output_path}")

    @classmethod
    def load(cls, index_dir: str, mmap: bool = False) -> 'BM25SIndex':
        """
        从目录加载索引

        Args:
            index_dir: 索引目录路径
            mmap: 是否使用内存映射（节省内存）

        Returns:
            BM25SIndex 实例
        """
        index = cls()
        index_path = Path(index_dir)

        # 加载元数据
        metadata_file = index_path / "metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            index.metadata = json.load(f)

        # 加载 BM25S 索引
        bm25s_index_path = index_path / "bm25s_index"
        if bm25s_index_path.exists():
            index.retriever = bm25s.BM25.load(str(bm25s_index_path), mmap=mmap)
            logger.info(f"✅ BM25S 索引已加载: {index_dir} ({index.metadata['total_pages']} 页, mmap={mmap})")
        else:
            logger.warning(f"未找到 BM25S 索引: {bm25s_index_path}")

        # 加载 Tokenizer
        index.tokenizer.load_vocab(str(index_path))
        index.tokenizer.load_stopwords(str(index_path))

        return index

    def get_chapter_pages(self, chapter: str) -> List[int]:
        """获取章节的所有页码"""
        return self.metadata["toc"].get(chapter, [])

    def get_toc(self) -> Dict[str, List[int]]:
        """获取完整目录"""
        return self.metadata["toc"]

