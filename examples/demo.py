#!/usr/bin/env python3
"""
Visual-Memvid Demo

端到端示例：PDF → 视频 → 检索 → OCR
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from visual_memvid import (
    VisualMemvidEncoder,
    VisualMemvidRetriever,
    DeepSeekOCRClient,
    CONFIG
)
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_encode(pdf_path: str, output_dir: str = "output"):
    """
    演示：PDF → 视频编码
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
    """
    print("\n" + "="*60)
    print("📄 Phase 1: PDF → 视频编码")
    print("="*60 + "\n")
    
    # 创建输出目录
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 初始化编码器
    encoder = VisualMemvidEncoder()
    
    # 添加 PDF
    print(f"📖 处理 PDF: {pdf_path}")
    frames_dir, index = encoder.add_pdf(pdf_path)
    
    print(f"\n📊 索引统计:")
    print(f"  - 总页数: {index.metadata['total_pages']}")
    print(f"  - 章节数: {len(index.metadata['toc'])}")
    print(f"  - 目录: {list(index.metadata['toc'].keys())}")
    
    # 构建视频
    video_path = output_dir / "knowledge.mp4"
    index_path = output_dir / "index.json"
    
    print(f"\n🎬 构建视频: {video_path}")
    stats = encoder.build_video(str(video_path), str(index_path))
    
    print(f"\n✅ 编码完成:")
    print(f"  - 视频: {stats['video_path']}")
    print(f"  - 索引: {stats['index_path']}")
    print(f"  - 编解码器: {stats['codec']}")
    
    return stats


def demo_retrieve(video_path: str, index_path: str, queries: list):
    """
    演示：视觉检索 + OCR
    
    Args:
        video_path: 视频文件路径
        index_path: 索引文件路径
        queries: 查询列表
    """
    print("\n" + "="*60)
    print("🔍 Phase 2: 视觉检索 + OCR")
    print("="*60 + "\n")
    
    # 初始化检索器
    retriever = VisualMemvidRetriever(video_path, index_path)
    
    print(f"📚 知识库: {retriever.total_pages} 页\n")
    
    # 执行查询
    for i, query in enumerate(queries, 1):
        print(f"\n{'─'*60}")
        print(f"🔍 查询 {i}: {query}")
        print(f"{'─'*60}\n")
        
        # 检索（自动查看前后页）
        results = retriever.search(
            query,
            top_k=2,
            context_window=1,  # 前后各 1 页
            use_batch_ocr=True
        )
        
        if not results:
            print("❌ 未找到匹配的页面\n")
            continue
        
        # 显示结果
        print(f"📖 找到 {len(results)} 个相关页面:\n")
        
        # 分组显示：核心页 vs 上下文页
        core_results = [r for r in results if r['is_core']]
        context_results = [r for r in results if not r['is_core']]
        
        # 显示核心页
        if core_results:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📌 核心结果 (最相关)")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            
            for result in core_results:
                print(f"📄 第 {result['page_num']} 页 ⭐")
                print(f"   处理时间: {result['processing_time']:.2f}s")
                if result['metadata']:
                    meta = result['metadata']
                    if meta.get('chapter'):
                        print(f"   章节: {meta['chapter']}")
                    if meta.get('has_table'):
                        print(f"   包含表格: ✅")
                print(f"\n{result['content'][:500]}...")
                print(f"\n{'-'*60}\n")
        
        # 显示上下文页
        if context_results:
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📖 上下文 (前后页)")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            
            for result in context_results:
                page_type_label = "前一页" if result['page_type'] == 'prev' else "后一页"
                print(f"📄 第 {result['page_num']} 页 ({page_type_label})")
                print(f"   处理时间: {result['processing_time']:.2f}s")
                print(f"\n{result['content'][:300]}...")
                print(f"\n{'-'*60}\n")


def demo_full_workflow(pdf_path: str):
    """
    完整演示：编码 + 检索
    
    Args:
        pdf_path: PDF 文件路径
    """
    print("\n" + "="*60)
    print("🚀 Visual-Memvid 完整演示")
    print("="*60 + "\n")
    
    # Phase 1: 编码
    stats = demo_encode(pdf_path)
    
    # Phase 2: 检索
    queries = [
        "第二季度的销售额",
        "表格",
        "第 5 页",
    ]
    
    demo_retrieve(stats['video_path'], stats['index_path'], queries)
    
    print("\n" + "="*60)
    print("✅ 演示完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual-Memvid Demo")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("--encode-only", action="store_true", help="仅编码")
    parser.add_argument("--retrieve-only", action="store_true", help="仅检索")
    parser.add_argument("--video", help="视频文件路径（检索模式）")
    parser.add_argument("--index", help="索引文件路径（检索模式）")
    parser.add_argument("--query", action="append", help="查询（可多次指定）")
    
    args = parser.parse_args()
    
    if args.encode_only:
        # 仅编码
        demo_encode(args.pdf_path)
    elif args.retrieve_only:
        # 仅检索
        if not args.video or not args.index:
            print("❌ 检索模式需要指定 --video 和 --index")
            sys.exit(1)
        
        queries = args.query or ["示例查询"]
        demo_retrieve(args.video, args.index, queries)
    else:
        # 完整流程
        demo_full_workflow(args.pdf_path)

