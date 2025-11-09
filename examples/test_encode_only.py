#!/usr/bin/env python3
"""
测试编码功能（不需要 OCR 服务）

仅测试：PDF → 图片帧 → 视频 + 索引
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from visual_memvid import VisualMemvidEncoder
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_encode(pdf_path: str):
    """
    测试 PDF 编码
    """
    print("\n" + "="*70)
    print("🚀 Visual-Memvid 编码测试")
    print("="*70 + "\n")
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return
    
    print(f"📄 PDF 文件: {pdf_path}")
    print(f"📊 文件大小: {pdf_path.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 初始化编码器
    print("🔧 初始化编码器...")
    encoder = VisualMemvidEncoder()
    
    # 添加 PDF
    print(f"\n📖 开始处理 PDF...")
    try:
        frames_dir, index = encoder.add_pdf(str(pdf_path))
        
        print(f"\n✅ PDF 处理完成！")
        print(f"\n📊 索引统计:")
        print(f"  ├─ 总页数: {index.metadata['total_pages']}")
        print(f"  ├─ 章节数: {len(index.metadata['toc'])}")
        
        if index.metadata['toc']:
            print(f"  ├─ 目录:")
            for chapter, pages in list(index.metadata['toc'].items())[:5]:
                print(f"  │  ├─ {chapter}: 第 {min(pages)}-{max(pages)} 页")
            if len(index.metadata['toc']) > 5:
                print(f"  │  └─ ... 还有 {len(index.metadata['toc']) - 5} 个章节")
        
        # 显示前 3 页的元数据
        print(f"\n  └─ 前 3 页元数据:")
        for page in index.metadata['pages'][:3]:
            print(f"     ├─ 第 {page['page_num']} 页:")
            print(f"     │  ├─ 关键词: {page['keywords'][:5]}")
            print(f"     │  ├─ 有表格: {'✅' if page['has_table'] else '❌'}")
            print(f"     │  ├─ 有公式: {'✅' if page['has_formula'] else '❌'}")
            print(f"     │  └─ 有图片: {'✅' if page['has_image'] else '❌'}")
        
        # 构建视频
        video_path = output_dir / "knowledge.mp4"
        index_path = output_dir / "index.json"

        print(f"\n🎬 开始构建视频...")
        print(f"  ├─ 输出路径: {video_path}")
        print(f"  ├─ 索引路径: {index_path}")
        print(f"  └─ 编解码器: h265\n")

        stats = encoder.build_video(str(video_path), str(index_path))

        print(f"\n✅ 视频构建完成！")
        print(f"\n📦 输出文件:")
        print(f"  ├─ 视频: {stats['video_path']}")

        video_size = Path(stats['video_path']).stat().st_size / 1024 / 1024
        print(f"  │  └─ 大小: {video_size:.2f} MB")

        print(f"  ├─ 索引: {stats['index_path']}")
        index_size = Path(stats['index_path']).stat().st_size / 1024
        print(f"  │  └─ 大小: {index_size:.2f} KB")

        print(f"  └─ 编解码器: {stats['codec']}")

        # 压缩比
        pdf_size = pdf_path.stat().st_size / 1024 / 1024
        compression_ratio = pdf_size / video_size if video_size > 0 else 0
        print(f"\n📊 压缩统计:")
        print(f"  ├─ PDF 大小: {pdf_size:.2f} MB")
        print(f"  ├─ 视频大小: {video_size:.2f} MB")
        print(f"  └─ 压缩比: {compression_ratio:.2f}x")
        
        print("\n" + "="*70)
        print("✅ 测试完成！")
        print("="*70 + "\n")
        
        print("💡 下一步:")
        print("  1. 启动 DeepSeek OCR 服务 (http://localhost:8200)")
        print("  2. 运行检索测试:")
        print(f"     python examples/test_retrieve.py")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 Visual-Memvid 编码")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    
    args = parser.parse_args()
    
    test_encode(args.pdf_path)

