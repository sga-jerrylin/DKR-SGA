"""
PDF Encoder

将 PDF 转换为图片帧并构建视频
"""

import sys
from pathlib import Path
import subprocess
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple
import logging

# 添加 memvid 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "memvid"))

import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

from .bm25s_index import BM25SIndex  # 使用新的高性能索引
from .config import CONFIG

logger = logging.getLogger(__name__)


class VisualMemvidEncoder:
    """
    视觉 Memvid 编码器

    功能：
    - PDF → 图片帧（每页一张，保留完整布局）
    - 提取轻量级元数据（关键词、目录、特殊内容标记）
    - 图片帧 → MP4 视频（复用 Memvid FFmpeg 逻辑）
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化编码器

        Args:
            config: 自定义配置（可选）
        """
        self.config = config or CONFIG
        self.frames_dir = None
        self.index = BM25SIndex()  # 使用新的高性能索引
        self.total_pages = 0
    
    def add_pdf(
        self,
        pdf_path: str,
        dpi: Optional[int] = None,
        extract_toc: bool = True
    ) -> Tuple[Path, BM25SIndex]:
        """
        添加 PDF 并转换为图片帧
        
        Args:
            pdf_path: PDF 文件路径
            dpi: 渲染分辨率（默认 150）
            extract_toc: 是否提取目录
        
        Returns:
            (frames_dir, index)
        """
        dpi = dpi or self.config["pdf"]["dpi"]
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        logger.info(f"📄 开始处理 PDF: {pdf_path}")
        
        # 创建临时帧目录
        self.frames_dir = Path(tempfile.mkdtemp(prefix="visual_memvid_frames_"))
        logger.info(f"📁 帧目录: {self.frames_dir}")
        
        # 打开 PDF
        doc = fitz.open(pdf_path)
        self.total_pages = len(doc)
        logger.info(f"📊 总页数: {self.total_pages}")
        
        # 提取目录（如果有）
        toc = {}
        if extract_toc:
            toc = self._extract_toc(doc)
            logger.info(f"📑 目录章节: {len(toc)}")
        
        # 逐页处理
        for page_num in tqdm(range(len(doc)), desc="渲染 PDF 页面"):
            page = doc[page_num]

            # 1. 渲染为高分辨率图片
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 2. 确保宽高是偶数（H.265 要求）
            width, height = img.size
            if width % 2 != 0:
                width += 1
            if height % 2 != 0:
                height += 1

            if (width, height) != img.size:
                # 需要调整大小
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            # 3. 保存图片帧
            frame_path = self.frames_dir / f"page_{page_num:06d}.png"
            img.save(frame_path)

            # 3. 提取元数据（轻量级）
            text_preview = page.get_text()[:500]  # 仅前 500 字符用于关键词提取

            # 查找所属章节
            chapter = self._find_chapter(page_num + 1, toc)

            # 添加到索引（移除了 has_table/has_formula/has_image，依赖 OCR Summary）
            self.index.add_page(
                page_num=page_num + 1,
                frame_num=page_num,
                text_preview=text_preview,
                title="",  # 可以从页面提取标题
                chapter=chapter,
            )

        # 强制刷新日志
        import sys
        print("\n🔒 循环已结束，准备关闭 PDF 文档...", flush=True)
        sys.stdout.flush()
        logger.info(f"🔒 关闭 PDF 文档...")
        doc.close()
        print("✅ PDF 文档已关闭", flush=True)
        sys.stdout.flush()

        print(f"📊 准备记录日志: total_pages={self.total_pages}", flush=True)
        sys.stdout.flush()
        logger.info(f"✅ PDF 处理完成: {self.total_pages} 页")
        print("📊 日志已记录", flush=True)
        sys.stdout.flush()

        print(f"🔙 准备返回: frames_dir={self.frames_dir}, index={type(self.index)}", flush=True)
        sys.stdout.flush()
        return self.frames_dir, self.index
    
    def _extract_toc(self, doc: fitz.Document) -> Dict[str, List[int]]:
        """
        提取 PDF 目录
        
        Returns:
            {章节名: [页码列表]}
        """
        toc_dict = {}
        toc = doc.get_toc()  # [[level, title, page], ...]
        
        current_chapter = None
        for level, title, page in toc:
            if level == 1:  # 一级标题
                current_chapter = title
                toc_dict[current_chapter] = [page]
            elif level == 2 and current_chapter:  # 二级标题
                toc_dict[current_chapter].append(page)
        
        # 更新索引的目录
        self.index.metadata["toc"] = toc_dict
        
        return toc_dict
    
    def _find_chapter(self, page_num: int, toc: Dict[str, List[int]]) -> str:
        """查找页面所属章节"""
        for chapter, pages in toc.items():
            if page_num in pages or (pages and min(pages) <= page_num <= max(pages)):
                return chapter
        return ""
    
    # 移除了 _detect_table, _detect_formula, _detect_image 方法
    # 这些检测会严重拖慢上传速度，且与 OCR Summary 重复
    # 如需判断页面内容，应该在检索时使用 OCR Summary
    def build_video(
        self,
        output_path: str,
        index_path: Optional[str] = None,
        codec: Optional[str] = None
    ) -> Dict:
        """
        构建视频文件

        Args:
            output_path: 输出视频路径
            index_path: 索引保存路径（已废弃，不再生成 BM25S 索引）
            codec: 编解码器（h265, h264, av1）

        Returns:
            构建统计信息
        """
        if not self.frames_dir or not self.frames_dir.exists():
            raise ValueError("请先调用 add_pdf() 生成帧")

        codec = codec or self.config["video"]["codec"]
        output_path = Path(output_path)

        logger.info(f"🎬 开始构建视频: {output_path}")

        # 使用 FFmpeg 编码（复用 Memvid 逻辑）
        self._build_video_with_ffmpeg(self.frames_dir, output_path, codec)

        # 不再生成 BM25S 索引（已废弃）
        logger.info(f"⏭️  跳过 BM25S 索引生成（已废弃）")

        # 清理临时帧目录
        # shutil.rmtree(self.frames_dir)
        # logger.info(f"🗑️ 已清理临时帧目录")

        stats = {
            "video_path": str(output_path),
            "index_path": None,  # 不再生成索引
            "total_pages": self.total_pages,
            "codec": codec,
        }

        logger.info(f"✅ 视频构建完成: {output_path}")
        return stats
    
    def _build_video_with_ffmpeg(
        self,
        frames_dir: Path,
        output_path: Path,
        codec: str
    ):
        """
        使用 FFmpeg 命令行构建视频（参考 memvid 的实现）
        """
        # 获取 FFmpeg 可执行文件路径
        try:
            import imageio_ffmpeg
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            logger.info(f"✅ 使用 imageio-ffmpeg: {ffmpeg_exe}")
        except:
            # 降级到系统 FFmpeg
            ffmpeg_exe = 'ffmpeg'
            logger.info(f"⚠️ 使用系统 FFmpeg")

        # 导入 Memvid 配置
        try:
            from memvid.config import get_codec_parameters
            codec_config = get_codec_parameters(codec.lower())
            logger.info(f"✅ 使用 memvid 配置: {codec_config}")
        except Exception as e:
            # 降级到默认配置
            logger.warning(f"⚠️ 无法加载 memvid 配置: {e}")
            codec_config = self.config["video"]

        # FFmpeg 编解码器映射（参考 memvid）
        ffmpeg_codec_map = {
            "h265": "libx265", "hevc": "libx265",
            "h264": "libx264", "avc": "libx264",
            "av1": "libaom-av1", "vp9": "libvpx-vp9"
        }

        ffmpeg_codec = ffmpeg_codec_map.get(codec.lower(), "libx265")

        # 构建 FFmpeg 命令（参考 memvid 的 _build_ffmpeg_command）
        fps = codec_config.get("video_fps", 30)
        preset = codec_config.get("video_preset", "medium")
        crf = codec_config.get("video_crf", 28)
        pix_fmt = codec_config.get("pix_fmt", "yuv420p")

        # 基础命令
        cmd = [
            ffmpeg_exe, '-y',
            '-framerate', str(fps),
            '-i', str(frames_dir / 'page_%06d.png'),
            '-c:v', ffmpeg_codec,
            '-preset', preset,
            '-crf', str(crf),
        ]

        # 添加像素格式（不缩放，保持原始分辨率）
        if ffmpeg_codec in ['libx265', 'libx264']:
            # 不缩放！保持 PDF 渲染的原始高分辨率
            # 600 DPI 的 A4 页面是 4960×7016 像素，保持原样以确保 OCR 质量
            cmd.extend(['-pix_fmt', pix_fmt])

            # 添加 profile（如果有）
            if codec_config.get("video_profile"):
                cmd.extend(['-profile:v', codec_config["video_profile"]])
        else:
            cmd.extend(['-pix_fmt', pix_fmt])

        # 线程优化（参考 memvid）
        import os
        thread_count = min(os.cpu_count() or 4, 16)
        cmd.extend(['-threads', str(thread_count)])

        # 添加 H.265 静态图像优化参数（参考 Memvid）
        if ffmpeg_codec == 'libx265':
            # 从配置获取优化参数
            tune = codec_config.get("tune", "stillimage")
            extra_params = codec_config.get("extra_params", "keyint=1:no-scenecut:strong-intra-smoothing")

            # ✅ 正确：将 tune 合并到 x265-params 中（stillimage 不是 FFmpeg -tune 的有效值）
            x265_params = f"tune={tune}:{extra_params}:threads={thread_count}"
            cmd.extend(['-x265-params', x265_params])
        elif ffmpeg_codec == 'libx264':
            # H.264 也可以使用类似优化
            tune = codec_config.get("tune", "stillimage")
            cmd.extend(['-tune', tune])
        elif codec_config.get("extra_ffmpeg_args"):
            # 其他编解码器使用原有逻辑
            extra_args = codec_config["extra_ffmpeg_args"]
            if isinstance(extra_args, list):
                cmd.extend(extra_args)

        # 通用优化
        cmd.extend(['-movflags', '+faststart', '-avoid_negative_ts', 'make_zero'])
        cmd.append(str(output_path))

        # 获取第一帧的分辨率
        first_frame = frames_dir / 'page_000000.png'
        if first_frame.exists():
            from PIL import Image
            with Image.open(first_frame) as img:
                frame_width, frame_height = img.size
        else:
            frame_width, frame_height = "未知", "未知"

        logger.info(f"🎬 FFmpeg 编码摘要:")
        logger.info(f"   🎥 编解码器: {ffmpeg_codec}")
        logger.info(f"   📊 FPS: {fps}")
        logger.info(f"   🎚️ CRF: {crf}")
        logger.info(f"   ⚙️ 预设: {preset}")
        logger.info(f"   🧵 线程: {thread_count}")
        logger.info(f"   📐 像素格式: {pix_fmt}")
        logger.info(f"   📏 分辨率: {frame_width}×{frame_height} (保持原始分辨率)")
        logger.info(f"   📄 帧数: {self.total_pages}")

        # 执行 FFmpeg
        import time
        start_time = time.time()

        try:
            # 检查第一帧
            first_frame = frames_dir / 'page_000000.png'
            if not first_frame.exists():
                logger.error(f"❌ 第一帧文件不存在: {first_frame}")
                raise FileNotFoundError(f"帧文件不存在: {first_frame}")

            logger.info(f"✅ 帧文件检查通过")
            logger.info(f"🚀 执行 FFmpeg 命令...")
            logger.debug(f"   命令: {' '.join(cmd)}")

            # 执行命令（捕获输出用于调试）
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            elapsed_time = time.time() - start_time

            if result.returncode != 0:
                logger.error(f"❌ FFmpeg 编码失败 (返回码: {result.returncode})")
                logger.error(f"   stderr: {result.stderr[:1000]}")
                logger.error(f"   stdout: {result.stdout[:1000]}")
                raise RuntimeError(f"FFmpeg 编码失败: {result.stderr}")

            logger.info(f"✅ FFmpeg 编码成功，耗时: {elapsed_time:.1f} 秒")

            # 检查输出文件
            if not output_path.exists():
                logger.error(f"❌ 输出视频文件不存在: {output_path}")
                raise FileNotFoundError(f"输出视频文件不存在: {output_path}")

            video_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"   📦 视频大小: {video_size:.2f} MB")
            logger.info(f"   ⏱️ 压缩率: {video_size / self.total_pages:.2f} MB/页")

        except subprocess.TimeoutExpired:
            logger.error(f"❌ FFmpeg 编码超时（超过 600 秒）")
            raise RuntimeError("FFmpeg 编码超时")

