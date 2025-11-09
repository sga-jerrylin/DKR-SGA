"""
DKR Agent - 基于 LangGraph 的自主 Agent 实现
"""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

from app.core.library_manager import LibraryManager
from app.core.llm_client import DeepSeekLLMClient
from app.config import get_settings


# 全局实例（用于工具函数访问）
_library_manager: Optional[LibraryManager] = None
_llm_client: Optional[DeepSeekLLMClient] = None


def _init_globals():
    """初始化全局实例"""
    global _library_manager, _llm_client
    if _library_manager is None:
        _library_manager = LibraryManager()
    if _llm_client is None:
        _llm_client = DeepSeekLLMClient()


# LangGraph 工具定义
@tool
def search_library_overview(query: str = "") -> str:
    """
    获取文档库概览（图书管理员视角）。

    这个工具会返回文档库的分类列表，每个分类下有多少份文档。
    适用于：不确定要在哪个分类中搜索时使用。

    Args:
        query: 用户的查询问题（可选，用于日志记录）

    Returns:
        文档库的分类概览信息
    """
    _init_globals()
    logger.info(f"[Tool] search_library_overview: {query}")

    # 获取分类摘要
    summary = _library_manager.get_category_summary()

    return summary


@tool
def search_in_category(category: str, query: str = "") -> str:
    """
    查看特定分类中的所有文档列表（图书管理员视角）。

    这个工具会返回该分类下所有文档的元信息，包括：
    - 文件名
    - 页数
    - 文档摘要（大概内容）

    适用于：已知要在哪个分类中查找，需要了解该分类下有哪些文档时使用。

    Args:
        category: 分类名称（如：财务类、制度类、简历、合同）
        query: 用户的查询问题（可选，用于日志记录）

    Returns:
        该分类下所有文档的详细列表
    """
    _init_globals()
    logger.info(f"[Tool] search_in_category: category={category}, query={query}")

    documents = _library_manager.list_documents(category=category)

    if not documents:
        return f"分类 '{category}' 中没有找到文档"

    result = f"# 分类 '{category}' 中的文档列表\n\n"
    result += f"共 {len(documents)} 份文档：\n\n"

    for i, doc in enumerate(documents, 1):
        metadata = doc.get('metadata', {})

        # 文件名
        filename = metadata.get('filename', doc.get('title', doc['doc_id']))

        # 页数
        page_count = metadata.get('page_count', '未知')

        # 文档摘要
        doc_summary = metadata.get('doc_summary', '无摘要')

        result += f"{i}. **{filename}**\n"
        result += f"   - 文档 ID: {doc['doc_id']}\n"
        result += f"   - 页数: {page_count} 页\n"
        result += f"   - 内容摘要: {doc_summary}\n"
        result += f"\n"

    result += "\n提示：选择一个文档后，可以使用 search_in_document_summary 或 search_in_document 进行深入检索。"

    return result


@tool
def search_in_document(doc_id: str, query: str, page_nums: list = None, top_k: int = 5) -> str:
    """
    【Stage 2 工具】在特定文档中搜索答案（使用 DeepSeek OCR 实时理解文档内容）。

    ⚠️⚠️⚠️ 严重警告：这是成本极高、速度极慢的操作！

    ⚠️ 使用前提条件（必须满足）：
    1. 必须先调用 search_in_document_summary 获取 Summary
    2. 必须先尝试用 Summary 回答问题
    3. 必须确认 Summary 完全不足以回答问题
    4. 必须说明为什么 Summary 不足（记录决策理由）

    ⚠️ 如果未满足上述条件，禁止调用此工具！

    适用场景（仅限以下情况）：
    - Summary 信息严重不足，无法回答问题
    - 需要查看图表、表格的详细内容
    - 需要精确的数字、公式、代码等

    工作流程：
    1. 如果指定了 page_nums，只 OCR 这些页面（强烈推荐）
    2. 如果未指定 page_nums，使用轻量级索引定位 top_k 个页面
    3. 调用 DeepSeek OCR API 实时理解页面内容（耗时 3-5 秒/页）
    4. 返回 OCR 结果

    Args:
        doc_id: 文档 ID
        query: 用户的查询问题
        page_nums: 指定要 OCR 的页码列表（强烈推荐，例如 [1, 3, 5]）
        top_k: 如果未指定 page_nums，返回最相关的页面数量（默认 5，最大 5）

    Returns:
        从文档中检索到的答案和来源页面
    """
    _init_globals()

    # 安全检查
    if page_nums and len(page_nums) > 5:
        logger.warning(f"[Tool] ⚠️ 请求 OCR {len(page_nums)} 页，超过建议的 5 页限制")
        return (
            f"⚠️ 警告：您请求 OCR {len(page_nums)} 页，超过建议的 5 页限制。\n"
            f"建议：请从中选择 3-5 页最相关的页面。\n"
            f"原因：全量 OCR 成本高、速度慢，应精准选择页面。"
        )

    if top_k > 5:
        logger.warning(f"[Tool] ⚠️ top_k={top_k} 超过限制，自动调整为 5")
        top_k = 5

    logger.info(f"[Tool] search_in_document: doc_id={doc_id}, query={query}, page_nums={page_nums}, top_k={top_k}")
    logger.info(f"[Tool] 将调用 DeepSeek OCR API 进行实时文档理解")

    try:
        import sys
        from pathlib import Path

        # Add project root to path (to import visual_memvid)
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from visual_memvid.visual_retriever import VisualMemvidRetriever
        from visual_memvid.ocr_client import DeepSeekOCRClient
        from app.config import get_settings
        from app.core.library_manager import LibraryManager

        settings = get_settings()
        library_manager = LibraryManager()

        # 获取文档信息
        doc_info = library_manager.get_document(doc_id)
        if not doc_info:
            return f"错误：文档 {doc_id} 不存在"

        metadata = doc_info.get("metadata", {})
        video_path = metadata.get("video_path")
        index_path = metadata.get("index_path")

        if not video_path or not index_path:
            return f"错误：文档 {doc_id} 缺少视频或索引文件"

        # 初始化 OCR 客户端和 visual retriever
        ocr_client = DeepSeekOCRClient(endpoint=settings.ocr_api_url)
        logger.info(f"[Tool] 正在调用 DeepSeek OCR API: {settings.ocr_api_url}")

        visual_retriever = VisualMemvidRetriever(
            video_path=video_path,
            index_path=index_path,
            ocr_client=ocr_client,
            enable_cache=True
        )

        # 执行检索
        if page_nums:
            # 精准 OCR：只处理指定的页面
            logger.info(f"[Tool] 精准 OCR 模式：处理指定的 {len(page_nums)} 页: {page_nums}")
            results = []
            for page_num in page_nums:
                try:
                    # 提取帧并 OCR（页码从 1 开始，frame_num 从 0 开始）
                    frame_num = page_num - 1
                    frame = visual_retriever._extract_frame(frame_num)
                    if frame is not None:
                        ocr_result = ocr_client.ocr_image(frame)

                        # 检查 OCR 结果是否为 None
                        if ocr_result is None:
                            logger.warning(f"[Tool] ⚠️ 第 {page_num} 页 OCR 返回 None")
                            continue

                        if ocr_result.get("success"):
                            content = ocr_result.get("text", "")
                            results.append({
                                "page_num": page_num,
                                "frame_num": frame_num,
                                "content": content,
                                "page_type": "OCR"
                            })
                            logger.info(f"[Tool] ✅ 第 {page_num} 页 OCR 成功，内容长度: {len(content)}")
                        else:
                            error_msg = ocr_result.get("error", "未知错误")
                            logger.warning(f"[Tool] ⚠️ 第 {page_num} 页 OCR 失败: {error_msg}")
                    else:
                        logger.warning(f"[Tool] ⚠️ 第 {page_num} 页帧提取失败")
                except Exception as e:
                    logger.error(f"[Tool] ❌ 第 {page_num} 页处理出错: {e}", exc_info=True)
        else:
            # 自动检索模式：使用轻量级索引定位页面
            logger.info(f"[Tool] 自动检索模式：使用索引定位 top-{top_k} 页面")
            results = visual_retriever.search(
                query=query,
                top_k=top_k,
                context_window=1
            )

        if results:
            logger.info(f"[Tool] DeepSeek OCR 成功处理 {len(results)} 个页面")

            response = f"【全量 OCR 结果】\n"
            response += f"文档: {doc_id}\n"
            response += f"处理了 {len(results)} 个页面\n"
            if page_nums:
                response += f"模式: 精准 OCR（指定页码: {page_nums}）\n\n"
            else:
                response += f"模式: 自动检索（Top-{top_k}）\n\n"
            response += "=" * 80 + "\n\n"

            for i, page_result in enumerate(results, 1):
                page_num = page_result.get('page_num', '?')
                content = page_result.get('content', '')

                response += f"【页面 {i}/{len(results)}】第 {page_num} 页\n"
                response += f"{'-' * 80}\n"
                response += f"{content}\n"
                response += f"{'-' * 80}\n\n"

            return response
        else:
            return f"在文档 {doc_id} 中未找到与查询相关的内容"

    except Exception as e:
        logger.error(f"search_in_document error: {e}", exc_info=True)
        return f"搜索出错：{str(e)}"


@tool
def evaluate_answer_confidence(query: str, answer: str) -> str:
    """
    评估答案的置信度。
    适用于：获得答案后，判断答案质量是否满足要求。

    Args:
        query: 原始查询问题
        answer: 获得的答案

    Returns:
        置信度评分和建议（0-1之间，>0.9 表示高质量答案）
    """
    _init_globals()
    logger.info(f"[Tool] evaluate_answer_confidence")

    try:
        confidence = _llm_client.evaluate_confidence(query, answer, [])

        if confidence >= 0.9:
            return f"置信度: {confidence:.2f} - 答案质量很高，可以返回给用户"
        elif confidence >= 0.7:
            return f"置信度: {confidence:.2f} - 答案质量中等，建议继续搜索更多信息"
        else:
            return f"置信度: {confidence:.2f} - 答案质量较低，需要重新搜索"

    except Exception as e:
        logger.error(f"evaluate_answer_confidence error: {e}")
        return f"评估出错：{str(e)}"


@tool
def search_in_document_summary(doc_id: str, query: str, top_k: int = 5) -> str:
    """
    在文档的 Summary 中快速检索（不进行全量 OCR）。
    适用于：快速了解文档内容，判断是否需要深入 OCR。

    工作流程：
    1. 使用轻量级索引定位最相关的页面
    2. 读取这些页面的 Summary（从 JSON 文件）
    3. 返回 Summary 内容，不进行 OCR
    4. 如果 Summary 不足以回答问题，建议使用 search_in_document

    Args:
        doc_id: 文档 ID
        query: 用户查询问题
        top_k: 返回最相关的页面数量（默认 5）

    Returns:
        相关页面的 Summary 内容
    """
    _init_globals()
    logger.info(f"[Tool] search_in_document_summary: doc_id={doc_id}, query={query}, top_k={top_k}")

    try:
        import sys
        import json
        from pathlib import Path

        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from visual_memvid.bm25s_index import BM25SIndex
        from app.config import get_settings
        from app.core.library_manager import LibraryManager

        settings = get_settings()
        library_manager = LibraryManager()

        # 获取文档信息
        doc_info = library_manager.get_document(doc_id)
        if not doc_info:
            return f"错误：文档 {doc_id} 不存在"

        metadata = doc_info.get("metadata", {})
        index_path = metadata.get("index_path")
        summary_path = metadata.get("summary_path")

        if not index_path or not summary_path:
            return f"错误：文档 {doc_id} 缺少索引或 Summary 文件"

        # 加载 BM25S 索引（使用 mmap 节省内存）
        index = BM25SIndex.load(index_path, mmap=True)

        # 使用索引定位相关页面（返回包含分数和相关性等级的列表）
        search_results = index.search(query, top_k)

        if not search_results:
            return f"在文档 {doc_id} 的 Summary 中未找到与查询相关的内容"

        logger.info(f"[Tool] 定位到 {len(search_results)} 个相关页面")

        # 读取 Summary JSON
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        # 处理两种可能的格式
        if isinstance(summary_data, list):
            # 新格式：[{"doc_id": "...", "page_num": 1, "summary": "...", ...}, ...]
            pass
        elif isinstance(summary_data, dict):
            # 旧格式：{"page_summaries": ["summary1", "summary2", ...]}
            return f"错误：Summary 文件格式已过时，请重新生成文档"
        else:
            return f"错误：Summary 文件格式不正确"

        # 统计相关性等级
        high_relevance = [r for r in search_results if r["relevance_level"] == "高"]
        mid_relevance = [r for r in search_results if r["relevance_level"] == "中"]
        low_relevance = [r for r in search_results if r["relevance_level"] == "低"]

        # 提取相关页面的完整 Summary（包括所有字段）
        result = f"【Summary 检索结果】\n"
        result += f"文档: {doc_id}\n"
        result += f"找到 {len(search_results)} 个相关页面\n"
        result += f"相关性分布: 高 {len(high_relevance)} 页 | 中 {len(mid_relevance)} 页 | 低 {len(low_relevance)} 页\n\n"
        result += "=" * 80 + "\n\n"

        for search_item in search_results:
            frame_num = search_item["frame_num"]
            page_num = search_item["page_num"]
            score = search_item["score"]
            score_ratio = search_item["score_ratio"]
            relevance_level = search_item["relevance_level"]
            rank = search_item["rank"]

            if frame_num < len(summary_data):
                page_data = summary_data[frame_num]
                summary_content = page_data.get("summary", "")

                result += f"【排名 {rank}】第 {page_num} 页 | BM25S 得分: {score:.2f} ({score_ratio:.0%}) | 相关性: {relevance_level}\n"
                result += f"{'-' * 80}\n"
                result += f"{summary_content}\n"
                result += f"{'-' * 80}\n\n"

        result += "=" * 80 + "\n"
        result += "【下一步行动指引 - 渐进式精准检索】\n\n"
        result += "⚠️ Stage 1.5: Summary 批量分析\n"
        result += "   1. 仔细阅读上述所有 Summary 内容\n"
        result += "   2. 评估每页的相关性（已标注：高/中/低）\n"
        result += "   3. 判断 Summary 是否足够回答问题\n\n"

        result += "⚠️ 决策分支：\n"
        result += "   【分支 A】Summary 足够 → 直接基于 Summary 生成答案，标注'基于 Summary'\n"
        result += "   【分支 B】Summary 不足 → 进入 Stage 2（精准 OCR）\n\n"

        result += "⚠️ Stage 2: 精准 OCR（仅在 Summary 不足时执行）\n"
        result += "   1. 从上述页面中选择 3-5 页最相关的（优先选择'高'相关性的页面）\n"
        result += "   2. 调用 search_in_document，指定 page_nums 参数\n"
        result += f"   3. 示例: search_in_document(doc_id='{doc_id}', query='{query}', page_nums=[{', '.join(str(r['page_num']) for r in high_relevance[:3])}])\n\n"

        result += "⚠️ 禁止事项：\n"
        result += "   ❌ 禁止未尝试用 Summary 回答就直接调用 search_in_document\n"
        result += "   ❌ 禁止对所有 10 页都做全量 OCR（成本高、速度慢）\n"
        result += "   ❌ 禁止选择超过 5 页进行 OCR\n"

        return result

    except Exception as e:
        logger.error(f"search_in_document_summary error: {e}", exc_info=True)
        return f"搜索 Summary 出错：{str(e)}"


@tool
def get_full_document_content(doc_id: str, query: str) -> str:
    """
    获取小文档的完整内容（适用于 <= 15 页的文档）。

    适用场景：
    - 合同、简历、报告等连续性强的文档
    - 需要整体理解，片段检索意义不大
    - 文档页数较少（<= 15 页）

    工作流程：
    1. 检查文档页数
    2. 如果 <= 15 页，一次性 OCR 所有页面
    3. 使用 LLM 基于完整内容生成答案
    4. 如果 > 15 页，建议使用 search_in_document

    Args:
        doc_id: 文档 ID
        query: 用户查询问题

    Returns:
        基于完整文档内容的答案
    """
    _init_globals()
    logger.info(f"[Tool] get_full_document_content: doc_id={doc_id}, query={query}")

    try:
        import sys
        from pathlib import Path

        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from visual_memvid.visual_retriever import VisualMemvidRetriever
        from visual_memvid.ocr_client import DeepSeekOCRClient
        from app.config import get_settings
        from app.core.library_manager import LibraryManager

        settings = get_settings()
        library_manager = LibraryManager()

        # 获取文档信息
        doc_info = library_manager.get_document(doc_id)
        if not doc_info:
            return f"错误：文档 {doc_id} 不存在"

        metadata = doc_info.get("metadata", {})
        total_pages = metadata.get("page_count", 0)

        # 检查页数限制
        if total_pages > 15:
            return (
                f"文档 {doc_id} 共 {total_pages} 页，超过 15 页限制。\n"
                f"建议使用 search_in_document 工具进行片段检索。"
            )

        logger.info(f"[Tool] 文档共 {total_pages} 页，开始全量 OCR...")

        video_path = metadata.get("video_path")
        index_path = metadata.get("index_path")

        if not video_path or not index_path:
            return f"错误：文档 {doc_id} 缺少视频或索引文件"

        # 初始化 OCR 客户端
        ocr_client = DeepSeekOCRClient(endpoint=settings.ocr_api_url)

        visual_retriever = VisualMemvidRetriever(
            video_path=video_path,
            index_path=index_path,
            ocr_client=ocr_client,
            enable_cache=True
        )

        # 一次性 OCR 所有页面（使用批量 OCR）
        all_pages_content = []
        for page_num in range(total_pages):
            # 提取帧并 OCR
            frame = visual_retriever._extract_frame(page_num)
            if frame is not None:
                ocr_result = ocr_client.ocr_image(frame)
                if ocr_result.get("success"):
                    content = ocr_result.get("content", "")
                    all_pages_content.append(f"=== 第 {page_num + 1} 页 ===\n{content}")

        if not all_pages_content:
            return f"错误：无法提取文档 {doc_id} 的内容"

        # 合并所有页面内容
        full_content = "\n\n".join(all_pages_content)

        logger.info(f"[Tool] 全量 OCR 完成，共 {len(all_pages_content)} 页")

        # 使用 LLM 基于完整内容生成答案
        answer_prompt = f"""基于以下文档的完整内容，回答用户的问题。

用户问题：{query}

文档完整内容：
{full_content[:8000]}  # 限制长度避免超出 token 限制

请提供准确、详细的答案。"""

        answer_result = _llm_client.chat(
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=0.3
        )

        if answer_result.get("success"):
            answer = answer_result.get("content", "")
            return f"基于文档 {doc_id} 的完整内容（共 {total_pages} 页）：\n\n{answer}"
        else:
            return f"错误：生成答案失败 - {answer_result.get('error')}"

    except Exception as e:
        logger.error(f"get_full_document_content error: {e}", exc_info=True)
        return f"获取文档内容出错：{str(e)}"


class DKRAgent:
    """
    DKR Agent - 基于 LangGraph 的自主文档检索 Agent

    特性：
    - 自主决策工具调用顺序
    - 循环调用直到找到满意答案
    - 支持状态持久化
    - 类似 Claude Agentic Search 的工作方式
    """

    def __init__(self):
        self.settings = get_settings()
        self.confidence_threshold = self.settings.agent_confidence_threshold

        # 初始化全局实例
        _init_globals()

        # 创建 LangChain LLM（根据配置选择 DeepSeek 或 Gemini）
        if self.settings.agent_llm_provider == "gemini":
            logger.info(f"使用 Gemini 模型: {self.settings.agent_llm_model}")
            self.llm = ChatOpenAI(
                base_url=self.settings.openrouter_base_url,
                api_key=self.settings.openrouter_api_key,
                model=self.settings.agent_llm_model,
                temperature=0.3
            )
        else:
            logger.info(f"使用 DeepSeek 模型: {self.settings.deepseek_model}")
            self.llm = ChatOpenAI(
                base_url=self.settings.deepseek_base_url,
                api_key=self.settings.deepseek_api_key,
                model=self.settings.deepseek_model,
                temperature=0.3
            )

        # 定义工具列表
        self.tools = [
            search_library_overview,
            search_in_category,
            search_in_document_summary,
            search_in_document,
            get_full_document_content,
            evaluate_answer_confidence
        ]

        # 创建 Agent（带状态持久化）
        self.memory = MemorySaver()
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            state_modifier=self._get_system_prompt(),
            checkpointer=self.memory
        )

        logger.info("DKRAgent initialized with LangGraph")

    def _get_system_prompt(self) -> str:
        """获取 Agent 系统提示词（从文件读取）"""
        from pathlib import Path

        # 读取 Prompt 文件（backend/prompts/agent_system_prompt.txt）
        # dkr_agent.py 在 backend/app/agent/，所以需要 parent.parent.parent
        prompt_file = Path(__file__).parent.parent.parent / "prompts" / "agent_system_prompt.txt"

        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()

            # 替换占位符
            prompt = prompt_template.format(
                confidence_threshold=self.confidence_threshold
            )

            return prompt
        except Exception as e:
            logger.error(f"读取 Agent Prompt 文件失败: {e}")
            # 降级到默认 Prompt
            return f"""你是一个智能文档检索助手。置信度阈值：{self.confidence_threshold}"""
    
    async def ask(
        self,
        query: str,
        thread_id: str = "default"
    ) -> Dict[str, Any]:
        """
        处理用户查询（LangGraph Agent 自主循环）

        Args:
            query: 用户查询
            thread_id: 会话线程 ID（用于状态持久化）

        Returns:
            查询结果
        """
        start_time = datetime.now()
        logger.info(f"Agent 开始处理查询: {query}")

        try:
            # 配置会话状态和递归限制
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50  # 增加递归限制到 50（默认 25）
            }

            # 调用 LangGraph Agent（自主循环调用工具）
            logger.info("=" * 80)
            logger.info(f"【Agent 开始执行】")
            logger.info(f"查询: {query}")
            logger.info(f"Thread ID: {thread_id}")
            logger.info("=" * 80)

            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config=config
            )

            # 提取最终答案
            messages = result.get("messages", [])
            if not messages:
                return self._create_response(
                    success=False,
                    error="Agent 未返回任何消息",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )

            # 日志：记录 Agent 的完整执行过程
            logger.info("\n" + "=" * 80)
            logger.info(f"【Agent 执行过程】共 {len(messages)} 条消息")
            logger.info("=" * 80)

            for i, msg in enumerate(messages, 1):
                msg_type = getattr(msg, 'type', 'unknown')

                if msg_type == 'human':
                    logger.info(f"\n[{i}] 👤 用户消息:")
                    logger.info(f"    {msg.content[:200]}")

                elif msg_type == 'ai':
                    logger.info(f"\n[{i}] 🤖 Agent 思考:")
                    # 检查是否有工具调用
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get('name', 'unknown')
                            tool_args = tool_call.get('args', {})
                            logger.info(f"    📞 调用工具: {tool_name}")
                            logger.info(f"    📝 参数: {tool_args}")
                    else:
                        # Agent 的最终回答
                        content = msg.content[:500] if hasattr(msg, 'content') else str(msg)[:500]
                        logger.info(f"    💬 回答: {content}")

                elif msg_type == 'tool':
                    logger.info(f"\n[{i}] 🔧 工具返回:")
                    tool_name = getattr(msg, 'name', 'unknown')
                    content = msg.content[:300] if hasattr(msg, 'content') else str(msg)[:300]
                    logger.info(f"    工具: {tool_name}")
                    logger.info(f"    结果: {content}...")

                else:
                    logger.info(f"\n[{i}] ❓ 未知消息类型: {msg_type}")

            # 最后一条消息是 Agent 的最终回复
            final_message = messages[-1]
            answer = final_message.content if hasattr(final_message, 'content') else str(final_message)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info("\n" + "=" * 80)
            logger.info(f"【Agent 完成】")
            logger.info(f"执行步骤: {len(messages)} 条消息")
            logger.info(f"耗时: {processing_time:.2f}s")
            logger.info(f"最终答案长度: {len(answer)} 字符")
            logger.info("=" * 80)
            logger.info("\n📝 【最终答案】")
            logger.info("=" * 80)
            logger.info(answer)
            logger.info("=" * 80)

            return self._create_response(
                success=True,
                answer=answer,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Agent 处理失败: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds()
            return self._create_response(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _create_response(
        self,
        success: bool,
        answer: Optional[str] = None,
        processing_time: float = 0.0,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建响应（只返回最终答案，不返回执行步骤）"""
        return {
            "success": success,
            "answer": answer,
            "processing_time": processing_time,
            "error": error
        }

