"""
增强的 PDF 编码器

功能：
1. PDF → 图片帧 → 视频（复用原有逻辑）
2. 生成每页的 VLM Summary
3. 存储到 Doris 4.0（可选）
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict
import hashlib

from typing import Any
from .pdf_encoder import VisualMemvidEncoder
from .ocr_client import DeepSeekOCRClient
from .gemini_ocr_client import GeminiOCRClient
from .qwen_ocr_client import QwenOCRClient
from .grok_ocr_client import GrokOCRClient
# from .doris_client import DorisClient  # Optional Doris integration
from .config import CONFIG

logger = logging.getLogger(__name__)


class EnhancedPDFEncoder(VisualMemvidEncoder):
    """
    增强的 PDF 编码器

    在原有编码器基础上增加：
    1. VLM Summary 生成
    2. Doris 存储（可选）
    """

    def __init__(
        self,
        summary_client: Optional[Any] = None,  # Summary生成客户端（Gemini/DeepSeek等）
        ocr_client: Optional[DeepSeekOCRClient] = None,  # 全页OCR客户端
        doris_client: Optional[Any] = None,  # DorisClient type (optional integration)
        enable_summary: bool = True,
        enable_doris: bool = False
    ):
        """
        初始化增强编码器

        Args:
            summary_client: Summary生成客户端（根据配置自动选择）
            ocr_client: 全页OCR客户端（DeepSeek OCR）
            doris_client: Doris 客户端
            enable_summary: 是否生成 Summary
            enable_doris: 是否存储到 Doris
        """
        super().__init__()

        # 初始化 Summary 生成客户端
        if summary_client:
            self.summary_client = summary_client
        else:
            # 根据配置选择 Summary 客户端
            summary_provider = CONFIG["summary"]["provider"]
            if summary_provider == "gemini":
                self.summary_client = GeminiOCRClient(
                    api_key=CONFIG["api_keys"]["openrouter"],
                    model=CONFIG["summary"]["model"]
                )
                logger.info("✅ 使用 Gemini 生成 Summary")
            elif summary_provider == "qwen":
                self.summary_client = QwenOCRClient(
                    api_key=CONFIG["api_keys"]["openrouter"],
                    model=CONFIG["summary"]["model"]
                )
                logger.info("✅ 使用 Qwen 生成 Summary")
            elif summary_provider == "grok":
                self.summary_client = GrokOCRClient(
                    api_key=CONFIG["api_keys"]["openrouter"],
                    model=CONFIG["summary"]["model"]
                )
                logger.info("✅ 使用 Grok-4-Fast 生成 Summary")
            else:
                # 默认使用 DeepSeek OCR
                self.summary_client = DeepSeekOCRClient(
                    endpoint=CONFIG["ocr"]["endpoint"]
                )
                logger.info("✅ 使用 DeepSeek OCR 生成 Summary")

        # 初始化全页 OCR 客户端
        self.ocr_client = ocr_client or DeepSeekOCRClient(
            endpoint=CONFIG["ocr"]["endpoint"]
        )

        self.doris_client = doris_client
        self.enable_summary = enable_summary
        self.enable_doris = enable_doris

        if enable_doris and not doris_client:
            logger.warning("⚠️ enable_doris=True 但未提供 doris_client，将禁用 Doris 存储")
            self.enable_doris = False

        logger.info(f"增强编码器初始化: Summary={enable_summary}, Doris={enable_doris}")
    
    def encode_with_summary(
        self,
        pdf_path: str,
        output_dir: str = "output",
        doc_id: Optional[str] = None
    ) -> Dict:
        """
        编码 PDF 并生成 Summary
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            doc_id: 文档ID（可选，默认使用文件名的 MD5）
        
        Returns:
            编码结果，包含视频路径、索引路径、Summary 等
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        # 生成文档 ID
        if doc_id is None:
            doc_id = hashlib.md5(pdf_path.name.encode()).hexdigest()[:16]
        
        logger.info(f"📄 开始编码: {pdf_path.name} (doc_id={doc_id})")
        logger.info(f"   PDF 路径: {pdf_path}")
        logger.info(f"   输出目录: {output_dir}")

        # Phase 1: 原有编码流程（PDF → 视频）
        logger.info("=" * 60)
        logger.info("Phase 1: PDF → 视频编码")
        logger.info("=" * 60)
        start_time = time.time()

        logger.info(f"🔧 添加 PDF 到编码器...")
        self.add_pdf(str(pdf_path))
        print(f"\n✅ add_pdf() 返回成功！total_pages={self.total_pages}", flush=True)
        logger.info(f"✅ PDF 添加成功，总页数: {self.total_pages}")

        # 创建输出目录结构
        print(f"📁 创建输出目录...", flush=True)
        output_dir_path = Path(output_dir)
        videos_dir = output_dir_path / "videos"
        indexes_dir = output_dir_path / "indexes"
        videos_dir.mkdir(parents=True, exist_ok=True)
        indexes_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 输出目录已创建: {output_dir_path}")

        # 生成视频和索引文件路径（按doc_id命名）
        print(f"🎬 生成视频文件路径...", flush=True)
        video_path = videos_dir / f"{doc_id}.mp4"
        # BM25S 索引需要保存到目录，而不是单个 JSON 文件
        index_path = indexes_dir / f"{doc_id}_index"
        logger.info(f"🎬 视频输出路径: {video_path}")
        logger.info(f"📋 索引输出路径: {index_path}")

        print(f"🎥 准备调用 build_video()...", flush=True)
        logger.info(f"🎥 开始构建视频...")
        result = self.build_video(str(video_path), str(index_path))
        print(f"✅ build_video() 返回成功！", flush=True)

        # 保持我们设置的正确路径，不使用 build_video 返回的路径
        # video_path 和 index_path 已经在前面设置好了
        print(f"📊 使用预设路径: video={video_path}, index={index_path}", flush=True)

        print(f"⏱️ 计算编码时间...", flush=True)
        encode_time = time.time() - start_time
        print(f"⏱️ 编码时间: {encode_time:.1f} 秒", flush=True)

        print(f"📝 准备记录日志 1...", flush=True)
        logger.info(f"✅ 视频编码完成: {encode_time:.1f} 秒")
        print(f"📝 日志 1 完成", flush=True)

        logger.info(f"   视频文件: {video_path}")
        print(f"📝 日志 2 完成", flush=True)

        logger.info(f"   索引文件: {index_path}")
        print(f"📝 日志 3 完成", flush=True)

        # Phase 2: 生成 Summary（如果启用）
        print(f"🔄 进入 Phase 2...", flush=True)
        summaries = []
        if self.enable_summary:
            print(f"✅ Summary 已启用", flush=True)
            logger.info("=" * 60)
            logger.info("Phase 2: 生成 VLM Summary")
            logger.info("=" * 60)
            logger.info(f"📊 总页数: {self.total_pages}")
            logger.info(f"🔧 OCR 客户端可用: {self.ocr_client.is_available if self.ocr_client else False}")

            start_time = time.time()

            summaries = self._generate_summaries(
                doc_id=doc_id,
                doc_name=pdf_path.name
            )

            summary_time = time.time() - start_time
            logger.info(f"✅ Summary 生成完成: {summary_time:.1f} 秒")
            logger.info(f"   成功生成: {len(summaries)} 个 Summary")

            # 保存 Summary 到 JSON（按文档ID分文件夹）
            summary_dir = Path(output_dir) / "summaries" / doc_id
            summary_dir.mkdir(parents=True, exist_ok=True)
            summary_path = summary_dir / "summaries.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summaries, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Summary 已保存: {summary_path}")
        else:
            logger.info("⏭️  跳过 Phase 2: Summary 生成已禁用")
        
        # Phase 3: 存储到 Doris（如果启用）
        if self.enable_doris and summaries:
            logger.info("Phase 3: 存储到 Doris")
            start_time = time.time()
            
            self._store_to_doris(summaries)
            
            doris_time = time.time() - start_time
            logger.info(f"✅ Doris 存储完成: {doris_time:.1f} 秒")
        
        # 返回结果
        summary_path = str(Path(output_dir) / "summaries" / doc_id / "summaries.json") if self.enable_summary and summaries else None
        result = {
            "doc_id": doc_id,
            "doc_name": pdf_path.name,
            "video_path": str(video_path),
            "index_path": str(index_path),
            "summary_path": summary_path,
            "total_pages": self.total_pages,
            "summaries": summaries,
            "enable_summary": self.enable_summary,
            "enable_doris": self.enable_doris,
        }
        
        logger.info(f"🎉 编码完成: {pdf_path.name}")
        return result
    
    def _generate_summaries(
        self,
        doc_id: str,
        doc_name: str
    ) -> List[Dict]:
        """
        为每一页生成 Summary

        Args:
            doc_id: 文档ID
            doc_name: 文档名称

        Returns:
            Summary 列表
        """
        print(f"\n🔄 _generate_summaries() 开始执行...", flush=True)
        summaries = []
        total_pages = self.total_pages
        print(f"📊 总页数: {total_pages}", flush=True)

        logger.info(f"🔄 开始生成 {total_pages} 页的 Summary...")

        # 检查 Summary 客户端是否可用
        print(f"🔍 检查 Summary 客户端: {self.summary_client}", flush=True)
        if self.summary_client is None:
            print(f"⚠️ Summary 客户端为 None", flush=True)
            logger.warning("⚠️ Summary 客户端未初始化，跳过 Summary 生成")
            return summaries

        print(f"🔍 检查 Summary 客户端可用性: {self.summary_client.is_available}", flush=True)
        if not self.summary_client.is_available:
            print(f"⚠️ Summary 服务不可用", flush=True)
            logger.warning("⚠️ Summary 服务不可用，跳过 Summary 生成")
            return summaries

        print(f"✅ Summary 客户端检查通过，准备处理 {total_pages} 页", flush=True)

        # 连续失败计数器
        consecutive_failures = 0
        max_consecutive_failures = 5  # 连续失败 5 次后停止

        # 遍历所有页面
        print(f"🔁 开始遍历 {total_pages} 页...", flush=True)
        for page_num in range(1, total_pages + 1):
            frame_num = page_num - 1
            print(f"\n📄 处理第 {page_num}/{total_pages} 页...", flush=True)

            logger.info(f"📄 处理第 {page_num}/{total_pages} 页 (帧 {frame_num})...")

            try:
                # 从帧目录读取图片
                frame_path = self.frames_dir / f"page_{frame_num:06d}.png"
                print(f"   🖼️  帧路径: {frame_path}", flush=True)
                logger.debug(f"   🖼️  帧路径: {frame_path}")

                if not frame_path.exists():
                    print(f"   ⚠️ 帧文件不存在", flush=True)
                    logger.warning(f"   ⚠️ 帧文件不存在: {frame_path}")
                    continue

                from PIL import Image
                print(f"   📂 加载图片...", flush=True)
                frame_img = Image.open(frame_path)
                print(f"   ✅ 图片加载成功: {frame_img.size}", flush=True)
                logger.debug(f"   ✅ 图片加载成功: {frame_img.size}")

                # 调用 Summary 客户端生成 Summary
                print(f"   🔄 准备调用 Summary 服务...", flush=True)
                logger.info(f"   🔄 调用 Summary 服务...")
                print(f"   ⏳ Summary 生成中（可能需要几秒）...", flush=True)
                result = self.summary_client.ocr_image(
                    frame_img,
                    mode="summary"  # 使用 summary 模式
                )
                print(f"   ✅ Summary 调用返回", flush=True)
                print(f"   📦 Summary 完整响应: {result}", flush=True)

                logger.debug(f"   📦 Summary 响应: success={result.get('success')}, text_length={len(result.get('text', ''))}")

                if result.get("success"):
                    summary_text = result["text"]
                    print(f"   ✅ Summary 生成成功！文本长度: {len(summary_text)}", flush=True)
                    print(f"   📄 Summary 原始内容:\n{'-'*60}\n{summary_text}\n{'-'*60}", flush=True)
                    logger.info(f"   ✅ Summary 生成成功: 文本长度 {len(summary_text)}")

                    # 重置失败计数器
                    consecutive_failures = 0

                    # 解析 JSON（去除 Markdown 代码块标记）
                    import json

                    # 去除 ```json 和 ``` 标记
                    json_text = summary_text.strip()
                    if json_text.startswith("```json"):
                        json_text = json_text[7:]  # 去除 ```json
                    elif json_text.startswith("```"):
                        json_text = json_text[3:]  # 去除 ```
                    if json_text.endswith("```"):
                        json_text = json_text[:-3]  # 去除结尾的 ```
                    json_text = json_text.strip()

                    try:
                        # 解析 JSON
                        rich_summary = json.loads(json_text)
                        print(f"   ✅ JSON 解析成功！", flush=True)
                        logger.info(f"   ✅ JSON 解析成功")

                        # 提取字段（新结构：删除 summary 和 key_words）
                        page_type = rich_summary.get("page_type", "未知")
                        page_summary = rich_summary.get("page_summary", "")  # 使用 page_summary 而不是 summary
                        entities = rich_summary.get("entities", [])
                        key_data = rich_summary.get("key_data", [])
                        table_info = rich_summary.get("table_info")
                        chart_info = rich_summary.get("chart_info")
                        image_info = rich_summary.get("image_info")

                        print(f"   📄 解析后的 Summary:\n{'-'*60}\n{page_summary}\n{'-'*60}", flush=True)
                        logger.info(f"   📄 page_summary 长度: {len(page_summary)}")

                    except json.JSONDecodeError as e:
                        # JSON 解析失败，使用原始文本
                        logger.warning(f"   ⚠️ JSON 解析失败: {e}，使用原始文本")
                        print(f"   ⚠️ JSON 解析失败: {e}，使用原始文本", flush=True)
                        page_type = "未知"
                        page_summary = summary_text
                        entities = []
                        key_data = []
                        table_info = None
                        chart_info = None
                        image_info = None

                    # 检测特殊内容
                    has_table = table_info is not None
                    has_formula = "公式" in page_summary or "formula" in page_summary.lower()
                    has_chart = chart_info is not None
                    logger.debug(f"   📊 内容检测: 表格={has_table}, 公式={has_formula}, 图表={has_chart}")

                    # 保存简化的 Rich Summary（删除 summary, key_words, keywords, has_* 字段）
                    summary = {
                        "doc_id": doc_id,
                        "doc_name": doc_name,
                        "page_num": page_num,
                        "frame_num": frame_num,
                        "page_type": page_type,
                        "page_summary": page_summary,
                        "entities": entities,
                        "key_data": key_data,
                        "table_info": table_info,
                        "chart_info": chart_info,
                        "image_info": image_info,
                        "processing_time": result.get("processing_time", 0)
                    }

                    summaries.append(summary)
                    logger.info(f"   ✅ Summary 已保存: {page_summary[:80]}...")
                else:
                    consecutive_failures += 1
                    error_msg = result.get('error', '未知错误')
                    logger.warning(f"   ⚠️ Summary 生成失败 ({consecutive_failures}/{max_consecutive_failures}): {error_msg}")

                    # 检查是否连续失败过多
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"❌ OCR 服务连续失败 {consecutive_failures} 次，停止 Summary 生成")
                        break

            except Exception as e:
                consecutive_failures += 1
                logger.error(f"    ❌ 处理第 {page_num} 页时出错 ({consecutive_failures}/{max_consecutive_failures}): {e}")

                # 检查是否连续失败过多
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"❌ 连续异常 {consecutive_failures} 次，停止 Summary 生成")
                    break
        
        logger.info(f"✅ 成功生成 {len(summaries)}/{total_pages} 页的 Summary")
        return summaries
    

    def _store_to_doris(self, summaries: List[Dict]):
        """
        存储 Summary 到 Doris
        
        Args:
            summaries: Summary 列表
        """
        if not self.doris_client:
            logger.warning("⚠️ Doris 客户端未初始化，跳过存储")
            return
        
        try:
            # 批量插入
            self.doris_client.batch_insert_summaries(summaries)
            logger.info(f"✅ 已存储 {len(summaries)} 条 Summary 到 Doris")
        except Exception as e:
            logger.error(f"❌ 存储到 Doris 失败: {e}")
            raise

