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
def get_library_catalog(query: str = "") -> str:
    """
    获取文档库的完整目录（所有分类 + 所有文档）。

    这个工具会一次性返回：
    1. 所有分类列表
    2. 每个分类下的所有文档（文件名、页数、文档摘要）

    适用于：快速浏览整个文档库，判断要查看哪些文档。

    Args:
        query: 用户的查询问题（可选，用于日志记录）

    Returns:
        完整的文档库目录（所有分类和文档）
    """
    _init_globals()
    logger.info(f"[Tool] get_library_catalog: {query}")

    # 获取所有分类
    categories = _library_manager.list_categories()

    if not categories:
        return "文档库为空，没有任何分类和文档"

    result = "【文档库完整目录】\n\n"
    result += f"共 {len(categories)} 个分类\n\n"
    result += "=" * 80 + "\n\n"

    total_docs = 0

    for category in categories:
        category_name = category.get('name', '未命名分类')
        doc_count = category.get('doc_count', 0)
        total_docs += doc_count

        result += f"📁 分类：{category_name}（{doc_count} 份文档）\n"
        result += f"{'-' * 80}\n"

        # 获取该分类下的所有文档
        documents = _library_manager.list_documents(category=category_name)

        if documents:
            for i, doc in enumerate(documents, 1):
                metadata = doc.get('metadata', {})

                # 文件名
                filename = metadata.get('filename', doc.get('title', doc['doc_id']))

                # 页数
                page_count = metadata.get('page_count', '未知')

                # 文档摘要
                doc_summary = metadata.get('doc_summary', '无摘要')

                result += f"  {i}. {filename}\n"
                result += f"     - 文档 ID: {doc['doc_id']}\n"
                result += f"     - 页数: {page_count} 页\n"
                result += f"     - 摘要: {doc_summary}\n"
                result += f"\n"
        else:
            result += f"  （该分类下暂无文档）\n\n"

        result += "\n"

    result += "=" * 80 + "\n"
    result += f"【统计】共 {len(categories)} 个分类，{total_docs} 份文档\n\n"
    result += "【下一步】请选择您想查看的文档（可以是 1 个或多个），我会返回这些文档的目录（所有页面的摘要）。\n"

    return result


@tool
def get_documents_table_of_contents(doc_ids: list, query: str = "") -> str:
    """
    获取一个或多个文档的目录（所有页面的 page_summary）。

    这个工具会返回指定文档的所有页面摘要，像翻阅目录一样快速了解文档结构。

    工作流程：
    1. 读取指定文档的 summaries.json
    2. 提取所有页面的 page_summary
    3. 返回简洁的目录格式

    适用于：快速浏览文档内容，定位感兴趣的页面。

    Args:
        doc_ids: 文档 ID 列表（可以是 1 个或多个，例如 ["doc_xxx", "doc_yyy"]）
        query: 用户的查询问题（可选，用于日志记录）

    Returns:
        文档目录（所有页面的 page_summary）
    """
    _init_globals()
    logger.info(f"[Tool] get_documents_table_of_contents: doc_ids={doc_ids}, query={query}")

    try:
        import sys
        import json
        from pathlib import Path

        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from app.core.library_manager import LibraryManager

        library_manager = LibraryManager()

        result = "【文档目录】\n\n"

        for doc_id in doc_ids:
            # 获取文档信息
            doc_info = library_manager.get_document(doc_id)
            if not doc_info:
                result += f"⚠️ 错误：文档 {doc_id} 不存在\n\n"
                continue

            metadata = doc_info.get("metadata", {})
            filename = metadata.get("filename", doc_id)
            page_count = metadata.get("page_count", 0)
            summary_path = metadata.get("summary_path")

            if not summary_path:
                result += f"⚠️ 错误：文档 {doc_id} 缺少 Summary 文件\n\n"
                continue

            # 读取 Summary JSON
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)

            # 检查格式
            if not isinstance(summary_data, list):
                result += f"⚠️ 错误：文档 {doc_id} 的 Summary 文件格式不正确\n\n"
                continue

            result += f"📄 文档：{filename}\n"
            result += f"   文档 ID: {doc_id}\n"
            result += f"   总页数: {page_count} 页\n"
            result += f"{'-' * 80}\n"

            # 提取所有页面的 page_summary
            for page_data in summary_data:
                page_num = page_data.get("page_num", "?")
                page_summary = page_data.get("page_summary", "无摘要")

                result += f"  第 {page_num} 页：{page_summary}\n"

            result += f"\n"

        result += "=" * 80 + "\n"
        result += "【下一步】请选择您感兴趣的页面，我会返回这些页面的详细信息（包括实体、数据、表格等）。\n"

        return result

    except Exception as e:
        logger.error(f"get_documents_table_of_contents error: {e}", exc_info=True)
        return f"获取文档目录出错：{str(e)}"


@tool
def get_pages_full_summary(doc_id: str, page_nums: list) -> str:
    """
    获取指定页面的完整 Summary 信息。

    这个工具会返回指定页面的详细 Summary，包括：
    - page_summary（页面摘要）
    - entities（关键实体）
    - key_data（关键数据）
    - table_info（表格信息）
    - chart_info（图表信息）
    - image_info（图像信息）

    适用于：在目录中定位到感兴趣的页面后，查看详细信息。

    Args:
        doc_id: 文档 ID
        page_nums: 页码列表（例如 [1, 3, 5, 61]）

    Returns:
        指定页面的完整 Summary 信息
    """
    _init_globals()
    logger.info(f"[Tool] get_pages_full_summary: doc_id={doc_id}, page_nums={page_nums}")

    try:
        import sys
        import json
        from pathlib import Path

        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))

        from app.core.library_manager import LibraryManager

        library_manager = LibraryManager()

        # 获取文档信息
        doc_info = library_manager.get_document(doc_id)
        if not doc_info:
            return f"错误：文档 {doc_id} 不存在"

        metadata = doc_info.get("metadata", {})
        summary_path = metadata.get("summary_path")

        if not summary_path:
            return f"错误：文档 {doc_id} 缺少 Summary 文件"

        # 读取 Summary JSON
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        # 检查格式
        if not isinstance(summary_data, list):
            return f"错误：文档 {doc_id} 的 Summary 文件格式不正确"

        result = f"【页面详细信息】\n"
        result += f"文档: {doc_id}\n"
        result += f"查看 {len(page_nums)} 个页面\n\n"
        result += "=" * 80 + "\n\n"

        for page_num in page_nums:
            # 查找对应的页面数据（page_num 从 1 开始，索引从 0 开始）
            page_data = None
            for data in summary_data:
                if data.get("page_num") == page_num:
                    page_data = data
                    break

            if not page_data:
                result += f"⚠️ 第 {page_num} 页：未找到 Summary 数据\n\n"
                continue

            result += f"【第 {page_num} 页】\n"
            result += f"{'-' * 80}\n"

            # 页面类型
            page_type = page_data.get("page_type", "未知")
            result += f"页面类型：{page_type}\n\n"

            # 页面摘要
            page_summary = page_data.get("page_summary", "无摘要")
            result += f"页面摘要：\n{page_summary}\n\n"

            # 关键实体
            entities = page_data.get("entities", [])
            if entities:
                result += f"关键实体（{len(entities)} 个）：\n"
                # 只显示前 20 个实体
                display_entities = entities[:20]
                result += f"{', '.join(display_entities)}\n"
                if len(entities) > 20:
                    result += f"...（还有 {len(entities) - 20} 个实体）\n"
                result += f"\n"

            # 关键数据
            key_data = page_data.get("key_data", [])
            if key_data:
                result += f"关键数据：\n"
                for data in key_data:
                    key = data.get("key", "")
                    value = data.get("value", "")
                    result += f"  - {key}: {value}\n"
                result += f"\n"

            # 表格信息
            table_info = page_data.get("table_info")
            if table_info:
                result += f"表格信息：\n"
                title = table_info.get("title", "无标题")
                result += f"  标题：{title}\n"

                columns = table_info.get("columns", [])
                if columns:
                    result += f"  列名：{', '.join(columns)}\n"

                rows_data = table_info.get("rows_data", "")
                if rows_data:
                    # 限制长度
                    display_data = rows_data[:500]
                    result += f"  数据：{display_data}\n"
                    if len(rows_data) > 500:
                        result += f"  ...（数据过长，已截断）\n"
                result += f"\n"

            # 图表信息
            chart_info = page_data.get("chart_info")
            if chart_info:
                result += f"图表信息：\n"
                chart_type = chart_info.get("type", "未知")
                description = chart_info.get("description", "无描述")
                result += f"  类型：{chart_type}\n"
                result += f"  描述：{description}\n"
                result += f"\n"

            # 图像信息
            image_info = page_data.get("image_info")
            if image_info:
                result += f"图像信息：\n"
                description = image_info.get("description", "无描述")
                result += f"  描述：{description}\n"

                key_elements = image_info.get("key_elements", [])
                if key_elements:
                    result += f"  关键元素：{', '.join(key_elements)}\n"
                result += f"\n"

            result += f"{'-' * 80}\n\n"

        result += "=" * 80 + "\n"
        result += "【下一步】如果 Summary 信息足够，请直接生成答案。如果需要查看原文，请使用 search_in_document 进行全量 OCR。\n"

        return result

    except Exception as e:
        logger.error(f"get_pages_full_summary error: {e}", exc_info=True)
        return f"获取页面详细信息出错：{str(e)}"


@tool
def search_in_document(doc_id: str, page_nums: list, query: str = "") -> str:
    """
    【全量 OCR 工具】对指定页面进行全量 OCR（使用 DeepSeek OCR API）。

    ⚠️⚠️⚠️ 严重警告：这是成本极高、速度极慢的操作！

    ⚠️ 使用前提条件（必须满足）：
    1. 必须先调用 get_documents_table_of_contents 查看目录
    2. 必须先调用 get_pages_full_summary 查看详细 Summary
    3. 必须确认 Summary 完全不足以回答问题
    4. 必须说明为什么 Summary 不足（记录决策理由）

    ⚠️ 如果未满足上述条件，禁止调用此工具！

    适用场景（仅限以下情况）：
    - Summary 信息严重不足，无法回答问题
    - 需要查看图表、表格的详细内容
    - 需要精确的数字、公式、代码等

    工作流程：
    1. 对指定的页面进行全量 OCR（耗时 3-5 秒/页）
    2. 返回 OCR 结果

    Args:
        doc_id: 文档 ID
        page_nums: 要 OCR 的页码列表（例如 [1, 3, 5]，建议不超过 5 页）
        query: 用户的查询问题（可选，用于日志记录）

    Returns:
        全量 OCR 结果
    """
    _init_globals()

    # 安全检查
    if not page_nums or len(page_nums) == 0:
        return "错误：必须指定要 OCR 的页码列表（page_nums 参数）"

    if len(page_nums) > 5:
        logger.warning(f"[Tool] ⚠️ 请求 OCR {len(page_nums)} 页，超过建议的 5 页限制")
        return (
            f"⚠️ 警告：您请求 OCR {len(page_nums)} 页，超过建议的 5 页限制。\n"
            f"建议：请从中选择 3-5 页最相关的页面。\n"
            f"原因：全量 OCR 成本高、速度慢，应精准选择页面。"
        )

    logger.info(f"[Tool] search_in_document: doc_id={doc_id}, page_nums={page_nums}, query={query}")
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

        if results:
            logger.info(f"[Tool] DeepSeek OCR 成功处理 {len(results)} 个页面")

            response = f"【全量 OCR 结果】\n"
            response += f"文档: {doc_id}\n"
            response += f"处理了 {len(results)} 个页面（指定页码: {page_nums}）\n\n"
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
            return f"OCR 失败：未能成功处理任何页面"

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


# 旧工具已删除：search_in_document_summary（被 get_documents_table_of_contents + get_pages_full_summary 替代）
# 旧工具已删除：get_full_document_content（不再需要）


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

        # 定义工具列表（新版本：5个工具）
        self.tools = [
            get_library_catalog,                # 工具1: 获取文档库完整目录
            get_documents_table_of_contents,    # 工具2: 获取文档目录（所有 page_summary）
            get_pages_full_summary,             # 工具3: 获取页面详细信息
            search_in_document,                 # 工具4: 全量 OCR
            evaluate_answer_confidence          # 工具5: 评估答案置信度
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

